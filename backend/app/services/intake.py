import hashlib
import json
import os
import re
import shutil
import sqlite3
import time
from _thread import RLock
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Literal
from uuid import uuid4

from app.schemas.health import OperationalStatus
from app.schemas.intake import (
    ActionKind,
    ActionRecord,
    ActionStatus,
    ApprovalAction,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalStatus,
    IntakeFile,
    IntakeScanResult,
    IntakeStatus,
    IntakeSummary,
    RecommendationRecord,
    RecoveryAssessment,
    RecoveryState,
    UnderstandingRecord,
    UnderstandingStatus,
)
from app.schemas.learning import (
    LearningPreferenceRecord,
    LearningResetRequest,
    LearningResetResult,
)
from app.services.database import migrate_database
from app.services.learning import (
    current_learning_revision,
    learned_destination,
    list_learning_preferences,
    record_confirmed_move,
    reset_learning_preference,
    revert_confirmed_move,
)
from app.services.ocr import OcrEngine
from app.services.recommendation import RULES_VERSION, recommend_file
from app.services.search import build_search_plan
from app.services.understanding import IMAGE_EXTENSIONS, understand_file


class ActionConflict(RuntimeError):
    """Raised when a requested file action cannot be completed safely."""


WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}

class IntakeService:
    def __init__(
        self,
        intake_path: Path,
        database_path: Path,
        library_path: Path | None = None,
        max_text_bytes: int = 1_000_000,
        max_extracted_text_bytes: int = 1_000_000,
        action_stale_seconds: float = 300.0,
        operation_lock: RLock | None = None,
        ocr_engine: OcrEngine | None = None,
    ) -> None:
        self.intake_path = intake_path
        self.library_path = library_path or intake_path.parent / "library"
        self.database_path = database_path
        self.max_text_bytes = max_text_bytes
        self.max_extracted_text_bytes = max_extracted_text_bytes
        self.action_stale_seconds = max(action_stale_seconds, 1.0)
        self._lock = operation_lock or RLock()
        self.ocr_engine = ocr_engine
        self._started_at = datetime.now(UTC)
        self._last_scan_status: Literal["ok", "failed", "never"] = "never"
        self._last_scan_completed_at: datetime | None = None
        self._last_scan_duration_ms: int | None = None

    def initialize(self) -> None:
        self.intake_path.mkdir(parents=True, exist_ok=True)
        self.library_path.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            migrate_database(connection)

    def scan(self) -> IntakeScanResult:
        started = time.perf_counter()
        with self._lock:
            try:
                result = self._scan_once()
            except Exception:
                self._record_scan("failed", started)
                raise
            self._record_scan("ok", started)
            return result

    def _scan_once(self) -> IntakeScanResult:
        scanned = added = updated = 0
        seen_paths: set[str] = set()
        intake_root = self.intake_path.resolve()
        with self._connection() as connection:
            for path in sorted(self.intake_path.rglob("*")):
                if not path.is_file():
                    continue
                try:
                    if not path.resolve(strict=True).is_relative_to(intake_root):
                        continue
                except OSError:
                    continue
                relative_path = path.relative_to(self.intake_path).as_posix()
                seen_paths.add(relative_path)
                try:
                    stat = path.stat()
                except OSError:
                    continue

                scanned += 1
                modified_at = datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
                existing = connection.execute(
                    """
                    SELECT id, size_bytes, modified_at, observed_at
                    FROM intake_files
                    WHERE relative_path = ?
                    """,
                    (relative_path,),
                ).fetchone()

                if (
                    existing is not None
                    and existing["size_bytes"] == stat.st_size
                    and existing["modified_at"] == modified_at
                ):
                    continue

                try:
                    digest = hash_file(path)
                except OSError:
                    continue

                file_id = existing["id"] if existing is not None else str(uuid4())
                observed_at = (
                    existing["observed_at"]
                    if existing is not None
                    else datetime.now(UTC).isoformat()
                )
                duplicate = connection.execute(
                    """
                    SELECT id
                    FROM intake_files
                    WHERE sha256 = ? AND id != ? AND duplicate_of IS NULL
                    ORDER BY observed_at, id
                    LIMIT 1
                    """,
                    (digest, file_id),
                ).fetchone()
                duplicate_of = duplicate["id"] if duplicate is not None else None
                status = (
                    IntakeStatus.duplicate if duplicate_of else IntakeStatus.observed
                )

                connection.execute(
                    """
                    INSERT INTO intake_files (
                        id, relative_path, original_name, extension, size_bytes,
                        modified_at, observed_at, sha256, status, duplicate_of
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(relative_path) DO UPDATE SET
                        original_name = excluded.original_name,
                        extension = excluded.extension,
                        size_bytes = excluded.size_bytes,
                        modified_at = excluded.modified_at,
                        sha256 = excluded.sha256,
                        status = excluded.status,
                        duplicate_of = excluded.duplicate_of
                    """,
                    (
                        file_id,
                        relative_path,
                        path.name,
                        path.suffix.lower(),
                        stat.st_size,
                        modified_at,
                        observed_at,
                        digest,
                        status.value,
                        duplicate_of,
                    ),
                )
                if existing is None:
                    added += 1
                else:
                    updated += 1
            removed = self._remove_missing_files(connection, seen_paths)
            duplicates = self._reconcile_duplicates(connection)
            self._refresh_understanding(connection)
            self._refresh_recommendations(connection)

        return IntakeScanResult(
            scanned=scanned,
            added=added,
            updated=updated,
            removed=removed,
            duplicates=duplicates,
        )

    def operational_status(self) -> OperationalStatus:
        with self._lock:
            now = datetime.now(UTC)
            warnings: list[str] = []
            try:
                database_size = (
                    self.database_path.stat().st_size
                    if self.database_path.is_file()
                    else 0
                )
            except OSError:
                database_size = None
                warnings.append("Nova could not read the local database size.")

            try:
                storage = shutil.disk_usage(self.intake_path)
                storage_total = storage.total
                storage_free = storage.free
                storage_free_percent = (
                    storage_free / storage_total * 100 if storage_total else 0.0
                )
                if storage_free < 5 * 1024**3 or storage_free_percent < 10:
                    warnings.append(
                        "Local storage headroom is low; plan additional space "
                        "before importing many files or models."
                    )
            except OSError:
                storage_total = None
                storage_free = None
                storage_free_percent = None
                warnings.append("Nova could not read local storage capacity.")

            if self._last_scan_status == "failed":
                warnings.append(
                    "The latest intake scan failed; Nova will retry automatically."
                )
            elif (
                self._last_scan_duration_ms is not None
                and self._last_scan_duration_ms > 30_000
            ):
                warnings.append(
                    "The latest intake scan took longer than 30 seconds."
                )

            return OperationalStatus(
                status="attention" if warnings else "healthy",
                uptime_seconds=max(
                    0,
                    int((now - self._started_at).total_seconds()),
                ),
                database_size_bytes=database_size,
                storage_free_bytes=storage_free,
                storage_total_bytes=storage_total,
                storage_free_percent=storage_free_percent,
                last_scan_status=self._last_scan_status,
                last_scan_completed_at=self._last_scan_completed_at,
                last_scan_duration_ms=self._last_scan_duration_ms,
                warnings=warnings,
            )

    def _record_scan(
        self,
        status: Literal["ok", "failed"],
        started: float,
    ) -> None:
        self._last_scan_status = status
        self._last_scan_completed_at = datetime.now(UTC)
        self._last_scan_duration_ms = max(
            0,
            round((time.perf_counter() - started) * 1000),
        )

    def summary(self) -> IntakeSummary:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(files.id) AS files_observed,
                    COALESCE(SUM(understanding.status = 'ready'), 0) AS understood,
                    COALESCE(SUM(
                        files.status = 'observed'
                        AND recommendation.outcome = 'suggested'
                        AND (
                            approval.file_id IS NULL
                            OR approval.status = 'pending'
                        )
                    ), 0) AS ready_for_review,
                    COALESCE(SUM(files.status = 'duplicate'), 0) AS exact_duplicates
                FROM intake_files AS files
                LEFT JOIN understanding_results AS understanding
                  ON understanding.file_id = files.id
                LEFT JOIN recommendation_results AS recommendation
                  ON recommendation.file_id = files.id
                LEFT JOIN approval_reviews AS approval
                  ON approval.file_id = files.id
                 AND approval.recommendation_generated_at = recommendation.generated_at
                """
            ).fetchone()
        return IntakeSummary(
            files_observed=row["files_observed"],
            understood=row["understood"],
            ready_for_review=row["ready_for_review"],
            exact_duplicates=row["exact_duplicates"],
        )

    def learning_preferences(self) -> list[LearningPreferenceRecord]:
        with self._lock, self._connection() as connection:
            preferences = list_learning_preferences(connection)
        return [
            LearningPreferenceRecord(
                document_type=preference.document_type,
                base_category=preference.base_category,
                candidate_destination=preference.candidate_destination,
                supporting_examples=preference.supporting_examples,
                active_examples=preference.active_examples,
                stored_examples=preference.stored_examples,
                preference_share=preference.share,
                eligible=preference.eligible,
                revision=preference.revision,
            )
            for preference in preferences
        ]

    def reset_learning(
        self,
        request: LearningResetRequest,
    ) -> LearningResetResult:
        document_type = request.document_type.strip()
        base_category = request.base_category.strip()
        if not document_type or not base_category:
            raise ValueError("Document type and category cannot be empty.")
        reset_at = datetime.now(UTC).isoformat()
        with self._lock, self._connection() as connection:
            reset = reset_learning_preference(
                connection,
                document_type=document_type,
                base_category=base_category,
                confirmation=request.confirmation,
                reset_at=reset_at,
            )
            self._refresh_recommendations(connection)
            connection.commit()
        return LearningResetResult(
            document_type=reset.document_type,
            base_category=reset.base_category,
            removed_examples=reset.removed_examples,
            reset_at=reset.reset_at,
            detail=reset.detail,
        )

    def list_files(
        self,
        query: str | None = None,
        status: IntakeStatus | None = None,
        understanding_status: UnderstandingStatus | None = None,
        extension: str | None = None,
        document_type: str | None = None,
        approval_status: ApprovalStatus | None = None,
    ) -> list[IntakeFile]:
        clauses: list[str] = []
        parameters: list[str] = []
        search = build_search_plan(query)
        if search.clause is not None:
            clauses.append(f"({search.clause})")
            parameters.extend(search.parameters)
        if status is not None:
            clauses.append("files.status = ?")
            parameters.append(status.value)
        if understanding_status is not None:
            clauses.append("understanding.status = ?")
            parameters.append(understanding_status.value)
        if extension and (normalized_extension := extension.strip().lower()):
            clauses.append("files.extension = ?")
            parameters.append(
                normalized_extension
                if normalized_extension.startswith(".")
                else f".{normalized_extension}"
            )
        if document_type and (normalized_type := document_type.strip().lower()):
            clauses.append("understanding.document_type = ?")
            parameters.append(normalized_type)
        if approval_status is ApprovalStatus.pending:
            clauses.append(
                """(
                    recommendation.outcome = 'suggested'
                    AND (approval.file_id IS NULL OR approval.status = 'pending')
                )"""
            )
        elif approval_status is not None:
            clauses.append("approval.status = ?")
            parameters.append(approval_status.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order = (
            f"ORDER BY {search.rank_expression} DESC, "
            "observed_at DESC, relative_path"
            if search.rank_expression is not None
            else "ORDER BY observed_at DESC, relative_path"
        )
        parameters.extend(search.rank_parameters)
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT files.id, files.relative_path, files.original_name,
                       files.extension, files.size_bytes, files.modified_at,
                       files.observed_at, files.sha256, files.status,
                       files.duplicate_of, understanding.status AS understanding_status,
                       understanding.document_type, understanding.title,
                       understanding.text_preview, understanding.word_count,
                       understanding.character_count, understanding.evidence,
                       understanding.error, understanding.error_code,
                       understanding.extraction_method, understanding.retryable,
                       understanding.understood_at,
                       recommendation.outcome AS recommendation_outcome,
                       recommendation.category AS recommendation_category,
                       recommendation.suggested_filename,
                       recommendation.destination,
                       recommendation.confidence,
                       recommendation.reasons,
                       recommendation.generated_at,
                       approval.status AS approval_status,
                       approval.category AS approval_category,
                       approval.suggested_filename AS approval_suggested_filename,
                       approval.destination AS approval_destination,
                       approval.recommendation_generated_at,
                       approval.reviewed_at
                FROM intake_files AS files
                LEFT JOIN understanding_results AS understanding
                  ON understanding.file_id = files.id
                LEFT JOIN recommendation_results AS recommendation
                  ON recommendation.file_id = files.id
                LEFT JOIN approval_reviews AS approval
                  ON approval.file_id = files.id
                 AND approval.recommendation_generated_at = recommendation.generated_at
                {where}
                {order}
                """,
                parameters,
            ).fetchall()
        return [self._intake_file_from_row(row) for row in rows]

    def review_recommendation(
        self,
        file_id: str,
        review: ApprovalRequest,
    ) -> ApprovalRecord:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                """
                SELECT recommendation.outcome, recommendation.category,
                       recommendation.suggested_filename,
                       recommendation.destination,
                       recommendation.generated_at,
                       approval.status AS approval_status,
                       approval.category AS approval_category,
                       approval.suggested_filename AS approval_suggested_filename,
                       approval.destination AS approval_destination
                FROM recommendation_results AS recommendation
                LEFT JOIN approval_reviews AS approval
                  ON approval.file_id = recommendation.file_id
                 AND approval.recommendation_generated_at =
                     recommendation.generated_at
                WHERE recommendation.file_id = ?
                """,
                (file_id,),
            ).fetchone()
            if row is None or row["outcome"] != "suggested":
                raise LookupError("No current recommendation is available for review.")

            category = row["approval_category"] or row["category"]
            suggested_filename = (
                row["approval_suggested_filename"] or row["suggested_filename"]
            )
            destination = row["approval_destination"] or row["destination"]
            if review.action is ApprovalAction.edit:
                if (
                    review.category is None
                    or review.suggested_filename is None
                    or review.destination is None
                ):
                    raise ValueError(
                        "Editing requires category, suggested filename, and destination."
                    )
                category = review.category
                suggested_filename = review.suggested_filename
                destination = review.destination
            elif review.action is ApprovalAction.approve:
                category = review.category or category
                suggested_filename = review.suggested_filename or suggested_filename
                destination = review.destination or destination

            category, suggested_filename, destination = self._validate_review_values(
                category,
                suggested_filename,
                destination,
            )
            status = {
                ApprovalAction.edit: ApprovalStatus.pending,
                ApprovalAction.approve: ApprovalStatus.approved,
                ApprovalAction.reject: ApprovalStatus.rejected,
                ApprovalAction.ignore: ApprovalStatus.ignored,
            }[review.action]
            reviewed_at = datetime.now(UTC).isoformat()
            connection.execute(
                """
                INSERT INTO approval_reviews (
                    file_id, recommendation_generated_at, status, category,
                    suggested_filename, destination, reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    recommendation_generated_at =
                        excluded.recommendation_generated_at,
                    status = excluded.status,
                    category = excluded.category,
                    suggested_filename = excluded.suggested_filename,
                    destination = excluded.destination,
                    reviewed_at = excluded.reviewed_at
                """,
                (
                    file_id,
                    row["generated_at"],
                    status.value,
                    category,
                    suggested_filename,
                    destination,
                    reviewed_at,
                ),
            )
        return ApprovalRecord(
            status=status,
            category=category,
            suggested_filename=suggested_filename,
            destination=destination,
            recommendation_generated_at=row["generated_at"],
            reviewed_at=reviewed_at,
        )

    def list_actions(self, limit: int = 50) -> list[ActionRecord]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                WITH latest AS (
                    SELECT operation_id, MAX(rowid) AS event_rowid
                    FROM action_events
                    GROUP BY operation_id
                )
                SELECT event.operation_id, event.file_id, event.kind,
                       event.status, event.source_path, event.destination_path,
                       event.sha256, event.related_operation_id, event.detail,
                       event.created_at,
                       CASE
                           WHEN event.kind = 'move'
                            AND event.status = 'succeeded'
                            AND NOT EXISTS (
                                SELECT 1
                                FROM action_events AS undo
                                WHERE undo.kind = 'undo'
                                  AND undo.status = 'succeeded'
                                  AND undo.related_operation_id =
                                      event.operation_id
                            )
                           THEN 1
                           ELSE 0
                       END AS can_undo
                FROM action_events AS event
                JOIN latest ON latest.event_rowid = event.rowid
                ORDER BY event.rowid DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._action_record_from_row(row) for row in rows]

    def list_recovery_assessments(self) -> list[RecoveryAssessment]:
        cutoff = datetime.now(UTC) - timedelta(seconds=self.action_stale_seconds)
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                WITH latest AS (
                    SELECT operation_id, MAX(rowid) AS event_rowid
                    FROM action_events
                    GROUP BY operation_id
                )
                SELECT event.operation_id, event.kind, event.source_path,
                       event.destination_path, event.sha256, event.created_at
                FROM action_events AS event
                JOIN latest ON latest.event_rowid = event.rowid
                WHERE event.status = 'started'
                  AND event.created_at <= ?
                ORDER BY event.rowid DESC
                """,
                (cutoff.isoformat(),),
            ).fetchall()
        return [self._assess_incomplete_operation(row) for row in rows]

    def execute_approved(self, file_id: str) -> ActionRecord:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                """
                SELECT files.id, files.relative_path, files.sha256, files.status,
                       recommendation.outcome,
                       recommendation.source_sha256,
                       recommendation.source_status,
                       recommendation.generated_at,
                       recommendation.category AS base_category,
                       recommendation.destination AS base_destination,
                       understanding.document_type,
                       approval.status AS approval_status,
                       approval.category AS approval_category,
                       approval.suggested_filename AS approval_suggested_filename,
                       approval.destination AS approval_destination
                FROM intake_files AS files
                JOIN recommendation_results AS recommendation
                  ON recommendation.file_id = files.id
                JOIN understanding_results AS understanding
                  ON understanding.file_id = files.id
                LEFT JOIN approval_reviews AS approval
                  ON approval.file_id = files.id
                 AND approval.recommendation_generated_at =
                     recommendation.generated_at
                WHERE files.id = ?
                """,
                (file_id,),
            ).fetchone()
            if row is None:
                raise LookupError("The intake file or its recommendation no longer exists.")
            if (
                row["status"] != IntakeStatus.observed.value
                or row["outcome"] != "suggested"
                or row["source_sha256"] != row["sha256"]
                or row["source_status"] != row["status"]
                or row["approval_status"] != ApprovalStatus.approved.value
            ):
                raise ActionConflict(
                    "Execution requires a current approved recommendation for "
                    "a non-duplicate file."
                )

            _, suggested_filename, destination = self._validate_review_values(
                row["approval_category"],
                row["approval_suggested_filename"],
                row["approval_destination"],
            )
            source_relative = PurePosixPath(row["relative_path"]).as_posix()
            destination_relative = (
                PurePosixPath(destination) / suggested_filename
            ).as_posix()
            source = self._resolve_existing_file(
                self.intake_path,
                source_relative,
                "The intake source is missing or outside the intake folder.",
            )
            target = self._resolve_new_file(
                self.library_path,
                destination_relative,
                "The approved destination is outside the library folder.",
            )
            if target.exists():
                raise ActionConflict(
                    "The destination already exists. Nova will not overwrite it."
                )
            try:
                current_hash = hash_file(source)
            except OSError as error:
                raise ActionConflict(
                    "Nova could not read the source file. No file was changed."
                ) from error
            if current_hash != row["sha256"]:
                raise ActionConflict(
                    "The source changed after review. Scan and approve it again."
                )

            operation_id = str(uuid4())
            started_at = datetime.now(UTC).isoformat()
            self._insert_action_event(
                connection,
                operation_id=operation_id,
                file_id=file_id,
                kind=ActionKind.move,
                status=ActionStatus.started,
                source_path=source_relative,
                destination_path=destination_relative,
                sha256=current_hash,
                related_operation_id=None,
                detail="Validated the current approval and began a no-overwrite move.",
                created_at=started_at,
            )
            connection.commit()

            try:
                self._perform_verified_move(source, target, current_hash)
            except (ActionConflict, OSError) as error:
                detail = self._action_failure_detail(error)
                failed_at = datetime.now(UTC).isoformat()
                self._insert_action_event(
                    connection,
                    operation_id=operation_id,
                    file_id=file_id,
                    kind=ActionKind.move,
                    status=ActionStatus.failed,
                    source_path=source_relative,
                    destination_path=destination_relative,
                    sha256=current_hash,
                    related_operation_id=None,
                    detail=detail,
                    created_at=failed_at,
                )
                connection.commit()
                raise ActionConflict(detail) from error

            completed_at = datetime.now(UTC).isoformat()
            self._insert_action_event(
                connection,
                operation_id=operation_id,
                file_id=file_id,
                kind=ActionKind.move,
                status=ActionStatus.succeeded,
                source_path=source_relative,
                destination_path=destination_relative,
                sha256=current_hash,
                related_operation_id=None,
                detail=(
                    "Moved the approved file after SHA-256 verification. "
                    "No existing file was overwritten."
                ),
                created_at=completed_at,
            )
            connection.commit()
            if (
                row["document_type"] is not None
                and row["base_category"] is not None
                and row["base_destination"] is not None
                and row["approval_category"] == row["base_category"]
            ):
                with suppress(sqlite3.Error):
                    record_confirmed_move(
                        connection,
                        operation_id=operation_id,
                        file_id=file_id,
                        source_sha256=current_hash,
                        document_type=row["document_type"],
                        base_category=row["base_category"],
                        base_destination=row["base_destination"],
                        approved_category=row["approval_category"],
                        approved_destination=row["approval_destination"],
                        approved_filename=row["approval_suggested_filename"],
                        created_at=completed_at,
                    )
                    connection.commit()

        with suppress(Exception):
            self.scan()
        return ActionRecord(
            operation_id=operation_id,
            file_id=file_id,
            kind=ActionKind.move,
            status=ActionStatus.succeeded,
            source_path=source_relative,
            destination_path=destination_relative,
            sha256=current_hash,
            related_operation_id=None,
            detail=(
                "Moved the approved file after SHA-256 verification. "
                "No existing file was overwritten."
            ),
            created_at=completed_at,
            can_undo=True,
        )

    def undo_action(self, operation_id: str) -> ActionRecord:
        with self._lock, self._connection() as connection:
            move = connection.execute(
                """
                SELECT operation_id, file_id, source_path, destination_path,
                       sha256
                FROM action_events
                WHERE operation_id = ?
                  AND kind = 'move'
                  AND status = 'succeeded'
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (operation_id,),
            ).fetchone()
            if move is None:
                raise LookupError("No completed move exists for that operation.")
            undone = connection.execute(
                """
                SELECT 1
                FROM action_events
                WHERE kind = 'undo'
                  AND status = 'succeeded'
                  AND related_operation_id = ?
                LIMIT 1
                """,
                (operation_id,),
            ).fetchone()
            if undone is not None:
                raise ActionConflict("That move has already been undone.")

            source = self._resolve_existing_file(
                self.library_path,
                move["destination_path"],
                "The filed copy is missing or outside the library folder.",
            )
            target = self._resolve_new_file(
                self.intake_path,
                move["source_path"],
                "The original intake destination is outside the intake folder.",
            )
            if target.exists():
                raise ActionConflict(
                    "The original intake path is occupied. Nova will not overwrite it."
                )
            try:
                current_hash = hash_file(source)
            except OSError as error:
                raise ActionConflict(
                    "Nova could not read the filed copy. No file was changed."
                ) from error
            if current_hash != move["sha256"]:
                raise ActionConflict(
                    "The filed copy changed after execution. Undo was stopped."
                )

            undo_operation_id = str(uuid4())
            started_at = datetime.now(UTC).isoformat()
            self._insert_action_event(
                connection,
                operation_id=undo_operation_id,
                file_id=move["file_id"],
                kind=ActionKind.undo,
                status=ActionStatus.started,
                source_path=move["destination_path"],
                destination_path=move["source_path"],
                sha256=current_hash,
                related_operation_id=operation_id,
                detail="Validated the filed copy and began a no-overwrite undo.",
                created_at=started_at,
            )
            connection.commit()

            try:
                self._perform_verified_move(source, target, current_hash)
            except (ActionConflict, OSError) as error:
                detail = self._action_failure_detail(error)
                failed_at = datetime.now(UTC).isoformat()
                self._insert_action_event(
                    connection,
                    operation_id=undo_operation_id,
                    file_id=move["file_id"],
                    kind=ActionKind.undo,
                    status=ActionStatus.failed,
                    source_path=move["destination_path"],
                    destination_path=move["source_path"],
                    sha256=current_hash,
                    related_operation_id=operation_id,
                    detail=detail,
                    created_at=failed_at,
                )
                connection.commit()
                raise ActionConflict(detail) from error

            completed_at = datetime.now(UTC).isoformat()
            detail = (
                "Restored the verified file to its original intake path. "
                "No existing file was overwritten."
            )
            self._insert_action_event(
                connection,
                operation_id=undo_operation_id,
                file_id=move["file_id"],
                kind=ActionKind.undo,
                status=ActionStatus.succeeded,
                source_path=move["destination_path"],
                destination_path=move["source_path"],
                sha256=current_hash,
                related_operation_id=operation_id,
                detail=detail,
                created_at=completed_at,
            )
            connection.commit()
            with suppress(sqlite3.Error):
                revert_confirmed_move(
                    connection,
                    operation_id=operation_id,
                    reverted_at=completed_at,
                )
                connection.commit()

        with suppress(Exception):
            self.scan()
        return ActionRecord(
            operation_id=undo_operation_id,
            file_id=move["file_id"],
            kind=ActionKind.undo,
            status=ActionStatus.succeeded,
            source_path=move["destination_path"],
            destination_path=move["source_path"],
            sha256=current_hash,
            related_operation_id=operation_id,
            detail=detail,
            created_at=completed_at,
            can_undo=False,
        )

    def _refresh_understanding(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            """
            SELECT files.id, files.relative_path, files.extension, files.sha256,
                   understanding.source_sha256,
                   understanding.status AS understanding_status,
                   understanding.extraction_method,
                   understanding.full_text
            FROM intake_files AS files
            LEFT JOIN understanding_results AS understanding
              ON understanding.file_id = files.id
            """
        ).fetchall()
        for row in rows:
            is_current = row["source_sha256"] == row["sha256"]
            has_complete_result = (
                row["understanding_status"] == UnderstandingStatus.unsupported.value
                or (
                    row["extraction_method"] != "none"
                    and (
                        row["understanding_status"] != UnderstandingStatus.ready.value
                        or row["full_text"] is not None
                    )
                )
            )
            needs_ocr_refresh = self.ocr_engine is not None and (
                (
                    row["extension"] in IMAGE_EXTENSIONS
                    and row["extraction_method"] == "none"
                )
                or (
                    row["extension"] == ".pdf"
                    and row["understanding_status"] == UnderstandingStatus.empty.value
                    and row["extraction_method"] == "pypdf"
                )
            )
            if is_current and has_complete_result and not needs_ocr_refresh:
                continue
            result = understand_file(
                self.intake_path / row["relative_path"],
                row["extension"],
                self.max_text_bytes,
                self.max_extracted_text_bytes,
                self.ocr_engine,
            )
            connection.execute(
                """
                INSERT INTO understanding_results (
                    file_id, source_sha256, status, document_type, title,
                    text_preview, word_count, character_count, evidence,
                    error, error_code, extraction_method, retryable, full_text,
                    understood_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    source_sha256 = excluded.source_sha256,
                    status = excluded.status,
                    document_type = excluded.document_type,
                    title = excluded.title,
                    text_preview = excluded.text_preview,
                    word_count = excluded.word_count,
                    character_count = excluded.character_count,
                    evidence = excluded.evidence,
                    error = excluded.error,
                    error_code = excluded.error_code,
                    extraction_method = excluded.extraction_method,
                    retryable = excluded.retryable,
                    full_text = excluded.full_text,
                    understood_at = excluded.understood_at
                """,
                (
                    row["id"],
                    row["sha256"],
                    result.status.value,
                    result.document_type,
                    result.title,
                    result.text_preview,
                    result.word_count,
                    result.character_count,
                    result.evidence,
                    result.error,
                    result.error_code,
                    result.extraction_method,
                    int(result.retryable),
                    result.full_text,
                    result.understood_at,
                ),
            )

    def _refresh_recommendations(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            """
            SELECT files.id, files.original_name, files.extension, files.modified_at,
                   files.sha256, files.status,
                   understanding.status AS understanding_status,
                   understanding.document_type, understanding.title,
                   understanding.full_text,
                   understanding.understood_at AS understanding_understood_at,
                   recommendation.source_sha256,
                   recommendation.source_status,
                   recommendation.source_understood_at,
                   recommendation.rules_version,
                   recommendation.category AS current_category,
                   recommendation.learning_revision
            FROM intake_files AS files
            LEFT JOIN understanding_results AS understanding
              ON understanding.file_id = files.id
            LEFT JOIN recommendation_results AS recommendation
              ON recommendation.file_id = files.id
            """
        ).fetchall()
        for row in rows:
            stored_learning_revision = current_learning_revision(
                connection,
                document_type=row["document_type"],
                base_category=row["current_category"],
            )
            if (
                row["source_sha256"] == row["sha256"]
                and row["source_status"] == row["status"]
                and row["source_understood_at"] == row["understanding_understood_at"]
                and row["rules_version"] == RULES_VERSION
                and row["learning_revision"] == stored_learning_revision
            ):
                continue
            result = recommend_file(
                original_name=row["original_name"],
                extension=row["extension"],
                modified_at=row["modified_at"],
                title=row["title"],
                full_text=row["full_text"],
                understanding_status=row["understanding_status"],
                is_duplicate=row["status"] == IntakeStatus.duplicate.value,
            )
            learning_revision = current_learning_revision(
                connection,
                document_type=row["document_type"],
                base_category=result.category,
            )
            if (
                result.outcome.value == "suggested"
                and result.category is not None
                and result.destination is not None
                and row["document_type"] is not None
            ):
                preference = learned_destination(
                    connection,
                    document_type=row["document_type"],
                    base_category=result.category,
                )
                if (
                    preference is not None
                    and preference.destination != result.destination
                ):
                    result = replace(
                        result,
                        destination=preference.destination,
                        reasons=[
                            *result.reasons,
                            (
                                "Learned the destination from "
                                f"{preference.supporting_examples} of "
                                f"{preference.total_examples} active, confirmed "
                                "moves with the same document type and category."
                            ),
                            "The learned destination still requires explicit approval.",
                        ],
                    )
            connection.execute(
                """
                INSERT INTO recommendation_results (
                    file_id, source_sha256, source_status, source_understood_at,
                    rules_version, learning_revision, outcome, category,
                    suggested_filename,
                    destination, confidence, reasons, generated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    source_sha256 = excluded.source_sha256,
                    source_status = excluded.source_status,
                    source_understood_at = excluded.source_understood_at,
                    rules_version = excluded.rules_version,
                    learning_revision = excluded.learning_revision,
                    outcome = excluded.outcome,
                    category = excluded.category,
                    suggested_filename = excluded.suggested_filename,
                    destination = excluded.destination,
                    confidence = excluded.confidence,
                    reasons = excluded.reasons,
                    generated_at = excluded.generated_at
                """,
                (
                    row["id"],
                    row["sha256"],
                    row["status"],
                    row["understanding_understood_at"],
                    RULES_VERSION,
                    learning_revision,
                    result.outcome.value,
                    result.category,
                    result.suggested_filename,
                    result.destination,
                    result.confidence,
                    json.dumps(result.reasons),
                    result.generated_at,
                ),
            )

    @staticmethod
    def _intake_file_from_row(row: sqlite3.Row) -> IntakeFile:
        understanding = None
        if row["understanding_status"] is not None:
            understanding = UnderstandingRecord(
                status=row["understanding_status"],
                document_type=row["document_type"],
                title=row["title"],
                text_preview=row["text_preview"],
                word_count=row["word_count"],
                character_count=row["character_count"],
                evidence=row["evidence"],
                error=row["error"],
                error_code=row["error_code"],
                extraction_method=row["extraction_method"],
                retryable=bool(row["retryable"]),
                understood_at=row["understood_at"],
            )
        recommendation = None
        if row["recommendation_outcome"] is not None:
            recommendation = RecommendationRecord(
                outcome=row["recommendation_outcome"],
                category=row["recommendation_category"],
                suggested_filename=row["suggested_filename"],
                destination=row["destination"],
                confidence=row["confidence"],
                reasons=json.loads(row["reasons"]),
                generated_at=row["generated_at"],
            )
        approval = None
        if row["approval_status"] is not None:
            approval = ApprovalRecord(
                status=row["approval_status"],
                category=row["approval_category"],
                suggested_filename=row["approval_suggested_filename"],
                destination=row["approval_destination"],
                recommendation_generated_at=row["recommendation_generated_at"],
                reviewed_at=row["reviewed_at"],
            )
        return IntakeFile(
            id=row["id"],
            relative_path=row["relative_path"],
            original_name=row["original_name"],
            extension=row["extension"],
            size_bytes=row["size_bytes"],
            modified_at=row["modified_at"],
            observed_at=row["observed_at"],
            sha256=row["sha256"],
            status=row["status"],
            duplicate_of=row["duplicate_of"],
            understanding=understanding,
            recommendation=recommendation,
            approval=approval,
        )

    def _reconcile_duplicates(self, connection: sqlite3.Connection) -> int:
        canonical_by_hash: dict[str, str] = {}
        duplicates = 0
        rows = connection.execute(
            """
            SELECT id, sha256
            FROM intake_files
            ORDER BY observed_at, relative_path, id
            """
        ).fetchall()
        for row in rows:
            canonical_id = canonical_by_hash.get(row["sha256"])
            if canonical_id is None:
                canonical_by_hash[row["sha256"]] = row["id"]
                status = IntakeStatus.observed
            else:
                duplicates += 1
                status = IntakeStatus.duplicate
            connection.execute(
                """
                UPDATE intake_files
                SET status = ?, duplicate_of = ?
                WHERE id = ?
                """,
                (status.value, canonical_id, row["id"]),
            )
        return duplicates

    @staticmethod
    def _remove_missing_files(
        connection: sqlite3.Connection,
        seen_paths: set[str],
    ) -> int:
        rows = connection.execute("SELECT id, relative_path FROM intake_files").fetchall()
        missing_ids = [row["id"] for row in rows if row["relative_path"] not in seen_paths]
        if missing_ids:
            connection.executemany(
                """
                UPDATE intake_files
                SET status = 'observed', duplicate_of = NULL
                WHERE duplicate_of = ?
                """,
                ((file_id,) for file_id in missing_ids),
            )
            connection.executemany(
                "DELETE FROM intake_files WHERE id = ?",
                ((file_id,) for file_id in missing_ids),
            )
        return len(missing_ids)

    @staticmethod
    def _insert_action_event(
        connection: sqlite3.Connection,
        *,
        operation_id: str,
        file_id: str,
        kind: ActionKind,
        status: ActionStatus,
        source_path: str,
        destination_path: str,
        sha256: str,
        related_operation_id: str | None,
        detail: str,
        created_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO action_events (
                event_id, operation_id, file_id, kind, status, source_path,
                destination_path, sha256, related_operation_id, detail,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                operation_id,
                file_id,
                kind.value,
                status.value,
                source_path,
                destination_path,
                sha256,
                related_operation_id,
                detail,
                created_at,
            ),
        )

    @staticmethod
    def _action_record_from_row(row: sqlite3.Row) -> ActionRecord:
        return ActionRecord(
            operation_id=row["operation_id"],
            file_id=row["file_id"],
            kind=row["kind"],
            status=row["status"],
            source_path=row["source_path"],
            destination_path=row["destination_path"],
            sha256=row["sha256"],
            related_operation_id=row["related_operation_id"],
            detail=row["detail"],
            created_at=row["created_at"],
            can_undo=bool(row["can_undo"]),
        )

    def _assess_incomplete_operation(
        self,
        row: sqlite3.Row,
    ) -> RecoveryAssessment:
        kind = ActionKind(row["kind"])
        source_root, destination_root = (
            (self.intake_path, self.library_path)
            if kind == ActionKind.move
            else (self.library_path, self.intake_path)
        )
        assessed_at = datetime.now(UTC)
        source = self._diagnostic_candidate(source_root, row["source_path"])
        destination = self._diagnostic_candidate(
            destination_root,
            row["destination_path"],
        )
        if source is None or destination is None:
            return self._recovery_assessment(
                row,
                state=RecoveryState.unsafe_path,
                source_sha256=None,
                destination_sha256=None,
                detail=(
                    "A recorded path is outside Nova's managed folders. "
                    "Nova made no recovery change."
                ),
                assessed_at=assessed_at,
            )

        try:
            source_exists = source.exists()
            destination_exists = destination.exists()
            if (source_exists and not source.is_file()) or (
                destination_exists and not destination.is_file()
            ):
                return self._recovery_assessment(
                    row,
                    state=RecoveryState.conflict,
                    source_sha256=None,
                    destination_sha256=None,
                    detail=(
                        "A recorded file path is occupied by a non-file item. "
                        "Manual review is required."
                    ),
                    assessed_at=assessed_at,
                )
            source_hash = hash_file(source) if source_exists else None
            destination_hash = hash_file(destination) if destination_exists else None
        except OSError:
            return self._recovery_assessment(
                row,
                state=RecoveryState.unreadable,
                source_sha256=None,
                destination_sha256=None,
                detail=(
                    "Nova could not inspect one or both recorded paths. "
                    "Permissions or storage availability need manual review."
                ),
                assessed_at=assessed_at,
            )

        expected_hash = row["sha256"]
        if source_hash == expected_hash and destination_hash is None:
            state = RecoveryState.ready_to_retry
            detail = (
                "The verified source remains and the destination is empty. "
                "No completed filesystem change was detected; review before retrying."
            )
        elif source_hash is None and destination_hash == expected_hash:
            state = RecoveryState.completed_without_audit
            detail = (
                "The verified file is at the destination, but the success event "
                "is missing. Treat the action as completed and review the audit."
            )
        elif source_hash == expected_hash and destination_hash == expected_hash:
            state = RecoveryState.copy_incomplete
            detail = (
                "Verified copies exist at both paths. The copy finished before "
                "source removal; manual review is required."
            )
        elif source_hash is None and destination_hash is None:
            state = RecoveryState.missing
            detail = (
                "Neither recorded file exists. Nova cannot infer the outcome; "
                "manual recovery from storage or backup may be required."
            )
        else:
            state = RecoveryState.conflict
            detail = (
                "The current file state does not match the recorded SHA-256. "
                "Nova will not retry or alter either path."
            )
        return self._recovery_assessment(
            row,
            state=state,
            source_sha256=source_hash,
            destination_sha256=destination_hash,
            detail=detail,
            assessed_at=assessed_at,
        )

    @staticmethod
    def _recovery_assessment(
        row: sqlite3.Row,
        *,
        state: RecoveryState,
        source_sha256: str | None,
        destination_sha256: str | None,
        detail: str,
        assessed_at: datetime,
    ) -> RecoveryAssessment:
        return RecoveryAssessment(
            operation_id=row["operation_id"],
            kind=row["kind"],
            state=state,
            source_path=row["source_path"],
            destination_path=row["destination_path"],
            expected_sha256=row["sha256"],
            source_sha256=source_sha256,
            destination_sha256=destination_sha256,
            detail=detail,
            started_at=row["created_at"],
            assessed_at=assessed_at,
        )

    @staticmethod
    def _diagnostic_candidate(root: Path, relative_path: str) -> Path | None:
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or any(
            part in {"", ".", ".."} for part in relative.parts
        ):
            return None
        try:
            resolved_root = root.resolve(strict=True)
            candidate = (root / Path(*relative.parts)).resolve(strict=False)
        except OSError:
            return None
        if not candidate.is_relative_to(resolved_root):
            return None
        return candidate

    @staticmethod
    def _resolve_existing_file(
        root: Path,
        relative_path: str,
        error_message: str,
    ) -> Path:
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ActionConflict(error_message)
        try:
            resolved_root = root.resolve(strict=True)
            candidate = (root / Path(*relative.parts)).resolve(strict=True)
        except OSError as error:
            raise ActionConflict(error_message) from error
        if not candidate.is_relative_to(resolved_root) or not candidate.is_file():
            raise ActionConflict(error_message)
        return candidate

    @staticmethod
    def _resolve_new_file(
        root: Path,
        relative_path: str,
        error_message: str,
    ) -> Path:
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ActionConflict(error_message)
        try:
            resolved_root = root.resolve(strict=True)
            candidate_parent = root / Path(*relative.parts[:-1])
            candidate_parent.mkdir(parents=True, exist_ok=True)
            resolved_parent = candidate_parent.resolve(strict=True)
        except OSError as error:
            raise ActionConflict(error_message) from error
        if not resolved_parent.is_relative_to(resolved_root):
            raise ActionConflict(error_message)
        return resolved_parent / relative.name

    @staticmethod
    def _perform_verified_move(
        source: Path,
        destination: Path,
        expected_hash: str,
    ) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination_created = False
        try:
            with source.open("rb") as source_file, destination.open("xb") as target_file:
                destination_created = True
                shutil.copyfileobj(source_file, target_file, length=1024 * 1024)
                target_file.flush()
                os.fsync(target_file.fileno())
            shutil.copystat(source, destination)
            if hash_file(destination) != expected_hash:
                raise ActionConflict(
                    "The copied file failed SHA-256 verification. The source was retained."
                )
            if hash_file(source) != expected_hash:
                raise ActionConflict(
                    "The source changed during the move. The source was retained."
                )
            source.unlink()
        except FileExistsError as error:
            raise ActionConflict(
                "The destination already exists. Nova will not overwrite it."
            ) from error
        except Exception:
            if destination_created and source.exists() and destination.exists():
                with suppress(OSError):
                    destination.unlink()
            raise

    @staticmethod
    def _action_failure_detail(error: Exception) -> str:
        if isinstance(error, ActionConflict):
            return str(error)
        return "The filesystem operation failed. Nova retained the safest recoverable state."

    @staticmethod
    def _validate_review_values(
        category: str | None,
        suggested_filename: str | None,
        destination: str | None,
    ) -> tuple[str, str, str]:
        normalized_category = (category or "").strip()
        normalized_filename = (suggested_filename or "").strip()
        normalized_destination = (destination or "").strip().replace("\\", "/")
        if not normalized_category:
            raise ValueError("Category cannot be empty.")
        if not normalized_filename:
            raise ValueError("Suggested filename cannot be empty.")
        if (
            normalized_filename in {".", ".."}
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', normalized_filename)
            or normalized_filename.endswith((".", " "))
            or normalized_filename.split(".", 1)[0].rstrip(" .").upper()
            in WINDOWS_RESERVED_NAMES
        ):
            raise ValueError("Suggested filename contains unsafe characters.")
        if (
            not normalized_destination
            or normalized_destination.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized_destination)
        ):
            raise ValueError("Destination must be a relative folder path.")
        destination_path = PurePosixPath(normalized_destination)
        if any(
            part in {"", ".", ".."}
            or re.search(r'[<>:"|?*\x00-\x1f]', part)
            or part.split(".", 1)[0].rstrip(" .").upper() in WINDOWS_RESERVED_NAMES
            or part.endswith((".", " "))
            for part in destination_path.parts
        ):
            raise ValueError("Destination contains an unsafe path component.")
        return (
            normalized_category,
            normalized_filename,
            destination_path.as_posix(),
        )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
            connection.commit()
        finally:
            connection.close()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
