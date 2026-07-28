import hashlib
import hmac
import json
import os
import re
import sqlite3
import zipfile
from _thread import RLock
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import uuid4

from app.services.chat import KnowledgeSourceRecord, MessageRecord

KNOWLEDGE_KINDS = (
    "fact",
    "preference",
    "goal",
    "project",
    "lesson",
    "rule",
    "reference",
)
_KIND_DIRECTORIES = {
    "fact": "Facts",
    "preference": "Preferences",
    "goal": "Goals",
    "project": "Projects",
    "lesson": "Lessons",
    "rule": "Rules",
    "reference": "References",
}
_EXPLICIT_PATTERNS = (
    re.compile(r"^(?:please\s+)?remember(?:\s+that)?[,:]?\s+(.+)$", re.I),
    re.compile(
        r"^(?:please\s+)?(?:save|store)\s+(?:this|that)\s+"
        r"(?:to|in)\s+(?:my\s+)?(?:memory|knowledge|profile)[,:]?\s*(.+)$",
        re.I,
    ),
    re.compile(
        r"^(?:please\s+)?(?:add|save|store)\s+(?:to\s+)?"
        r"(?:my\s+)?(?:memory|knowledge|profile)[,:]?\s+(.+)$",
        re.I,
    ),
)
_PROFILE_PATTERNS = (
    (
        "preference",
        re.compile(r"^i\s+prefer\s+(.+)$", re.I),
        "This looks like a lasting preference that may help future conversations.",
    ),
    (
        "goal",
        re.compile(
            r"^my\s+(?:current\s+|long[- ]term\s+)?goal\s+is\s+(.+)$",
            re.I,
        ),
        "This looks like a personal goal that may be useful over time.",
    ),
    (
        "fact",
        re.compile(r"^my\s+name\s+is\s+(.+)$", re.I),
        "This looks like stable personal profile information.",
    ),
    (
        "fact",
        re.compile(r"^i\s+am\s+.+\byears?\s+old\b.*$", re.I),
        "This looks like dated personal profile information.",
    ),
    (
        "fact",
        re.compile(
            r"^i\s+have\s+.+\b(?:wife|husband|partner|son|daughter|"
            r"child|children)\b.*$",
            re.I,
        ),
        "This looks like stable family profile information.",
    ),
)


@dataclass(frozen=True)
class KnowledgeRequirementDefinition:
    id: str
    domain: str
    title: str
    why: str
    suggestion: str
    priority: int
    core: bool
    review_days: int
    match_kinds: tuple[str, ...] = ()
    match_phrases: tuple[str, ...] = ()


_KNOWLEDGE_REQUIREMENTS = (
    KnowledgeRequirementDefinition(
        id="preferred-name",
        domain="personal",
        title="Preferred name",
        why="Lets Nova address you consistently without guessing.",
        suggestion="Tell Nova the name you want it to use.",
        priority=5,
        core=True,
        review_days=365,
        match_phrases=("my name", "preferred name", "call me"),
    ),
    KnowledgeRequirementDefinition(
        id="response-style",
        domain="preferences",
        title="Response style",
        why="Helps Nova present answers in the amount and style you prefer.",
        suggestion="Describe how concise, detailed, or structured you want replies.",
        priority=4,
        core=True,
        review_days=180,
        match_phrases=("response style", "answer style", "reply style"),
    ),
    KnowledgeRequirementDefinition(
        id="current-goals",
        domain="planning",
        title="Current goals",
        why="Lets Nova prioritise recommendations around outcomes you chose.",
        suggestion="Add at least one current goal you want Nova to support.",
        priority=5,
        core=True,
        review_days=90,
        match_kinds=("goal",),
        match_phrases=("current goal", "long term goal", "long-term goal"),
    ),
    KnowledgeRequirementDefinition(
        id="active-projects",
        domain="planning",
        title="Active projects",
        why="Gives Nova the context needed to suggest practical next actions.",
        suggestion="Add the project you are actively working on now.",
        priority=5,
        core=True,
        review_days=90,
        match_kinds=("project",),
        match_phrases=("active project", "current project"),
    ),
    KnowledgeRequirementDefinition(
        id="timezone-location",
        domain="personal",
        title="Timezone or location context",
        why="Prevents mistakes in dates, times, schedules, and local suggestions.",
        suggestion="Add your timezone or general location; an exact address is not needed.",
        priority=4,
        core=True,
        review_days=365,
        match_phrases=("timezone", "time zone", "based in", "live in", "location"),
    ),
    KnowledgeRequirementDefinition(
        id="work-context",
        domain="work",
        title="Work context or schedule",
        why="Helps Nova make realistic plans that fit your working life.",
        suggestion="Add the work context or schedule that affects your planning.",
        priority=4,
        core=True,
        review_days=180,
        match_phrases=(
            "work schedule",
            "working hours",
            "occupation",
            "job",
            "truck driver",
        ),
    ),
    KnowledgeRequirementDefinition(
        id="technology-environment",
        domain="technology",
        title="Technology and device environment",
        why="Helps Nova give compatible technical guidance.",
        suggestion="Add the main devices or software environment Nova should support.",
        priority=3,
        core=True,
        review_days=180,
        match_phrases=(
            "pc build",
            "computer",
            "windows",
            "gpu",
            "device",
            "software",
        ),
    ),
    KnowledgeRequirementDefinition(
        id="household-context",
        domain="personal",
        title="Household or relationship context",
        why="Can improve shared planning when you choose to provide it.",
        suggestion="Optionally add household context that is useful for planning.",
        priority=3,
        core=False,
        review_days=365,
        match_phrases=(
            "wife",
            "husband",
            "partner",
            "son",
            "daughter",
            "household",
            "family",
        ),
    ),
    KnowledgeRequirementDefinition(
        id="vehicle-context",
        domain="vehicles",
        title="Vehicle context",
        why="Can support compatible maintenance and ownership guidance.",
        suggestion="Optionally add a vehicle or maintenance record.",
        priority=3,
        core=False,
        review_days=180,
        match_phrases=("vehicle", "car", "truck", "maintenance"),
    ),
    KnowledgeRequirementDefinition(
        id="home-responsibilities",
        domain="home",
        title="Home responsibilities",
        why="Can help with maintenance, inventories, and household projects.",
        suggestion="Optionally add a current home responsibility or project.",
        priority=2,
        core=False,
        review_days=180,
        match_phrases=("home project", "home maintenance", "appliance", "house"),
    ),
    KnowledgeRequirementDefinition(
        id="financial-goals",
        domain="finance",
        title="Financial goals",
        why="Can improve planning while keeping account credentials out of knowledge.",
        suggestion="Optionally add a high-level financial goal without account secrets.",
        priority=3,
        core=False,
        review_days=180,
        match_phrases=("financial goal", "budget goal", "savings goal"),
    ),
    KnowledgeRequirementDefinition(
        id="health-preferences",
        domain="health",
        title="Health or dietary preferences",
        why="Can tailor general planning when you choose to provide it.",
        suggestion="Optionally add a non-sensitive health or dietary preference.",
        priority=2,
        core=False,
        review_days=180,
        match_phrases=("diet", "dietary", "health preference", "nutrition"),
    ),
    KnowledgeRequirementDefinition(
        id="emergency-plan",
        domain="safety",
        title="Emergency plan",
        why="Can make personal contingency planning easier to retrieve.",
        suggestion="Optionally add a safe, non-secret emergency plan or contact process.",
        priority=4,
        core=False,
        review_days=180,
        match_phrases=("emergency plan", "emergency contact", "contingency plan"),
    ),
)


class KnowledgeCandidateNotFoundError(LookupError):
    """Raised when a requested knowledge proposal does not exist."""


class KnowledgeCandidateStateError(RuntimeError):
    """Raised when a proposal has already been reviewed."""


class KnowledgeRecordWriteError(RuntimeError):
    """Raised when an approved record cannot be written safely."""


class KnowledgeProposalError(RuntimeError):
    """Raised when Nova cannot prepare an optional knowledge proposal."""


class KnowledgeRetrievalError(RuntimeError):
    """Raised when approved knowledge cannot be verified for safe retrieval."""


class KnowledgeDuplicateConfirmationError(RuntimeError):
    """Raised when a likely duplicate needs explicit owner confirmation."""


class KnowledgeRecordNotFoundError(LookupError):
    """Raised when an approved knowledge record does not exist."""


class KnowledgeRecordStateError(RuntimeError):
    """Raised when a lifecycle action is invalid for the record state."""


class KnowledgeBackupError(RuntimeError):
    """Raised when a knowledge snapshot cannot be created and verified."""


@dataclass(frozen=True)
class KnowledgeCandidateRecord:
    id: str
    conversation_id: str
    source_message_id: str
    kind: str
    title: str
    content: str
    source_excerpt: str
    reason: str
    confidence: float
    explicit_request: bool
    status: str
    created_at: str
    reviewed_at: str | None
    record_path: str | None
    duplicate_record_id: str | None
    duplicate_title: str | None
    duplicate_path: str | None
    duplicate_score: float | None


@dataclass(frozen=True)
class KnowledgeRecord:
    id: str
    candidate_id: str
    kind: str
    title: str
    content: str
    relative_path: str
    sha256: str
    created_at: str
    status: str
    revision: int
    updated_at: str
    retired_at: str | None


@dataclass(frozen=True)
class KnowledgeSnapshotRecord:
    filename: str
    size_bytes: int
    sha256: str
    record_count: int
    file_count: int
    created_at: str


@dataclass(frozen=True)
class KnowledgeRequirementStatusRecord:
    id: str
    domain: str
    title: str
    why: str
    suggestion: str
    priority: int
    core: bool
    review_days: int
    status: str
    last_reviewed: str | None
    matched_record_ids: tuple[str, ...]
    matched_record_titles: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalQualityFailureRecord:
    record_id: str
    title: str
    reason: str


@dataclass(frozen=True)
class KnowledgeQualityReportRecord:
    generated_at: str
    active_record_count: int
    retired_record_count: int
    core_covered: int
    core_total: int
    completion_percent: float
    fresh_covered: int
    covered_total: int
    freshness_percent: float
    retrieval_total_records: int
    retrieval_checked: int
    retrieval_passed: int
    retrieval_percent: float
    retrieval_check_limit: int
    requirements: tuple[KnowledgeRequirementStatusRecord, ...]
    retrieval_failures: tuple[RetrievalQualityFailureRecord, ...]
    methodology: str
    limitation: str


@dataclass(frozen=True)
class CandidateDraft:
    kind: str
    title: str
    content: str
    reason: str
    confidence: float
    explicit_request: bool


class KnowledgeService:
    def __init__(
        self,
        database_path: Path,
        knowledge_path: Path,
        backup_path: Path,
        operation_lock: RLock,
    ) -> None:
        self.database_path = database_path
        self.knowledge_path = knowledge_path
        self.backup_path = backup_path
        self.operation_lock = operation_lock

    def initialize(self) -> None:
        self.knowledge_path.mkdir(parents=True, exist_ok=True)
        (self.backup_path / "knowledge").mkdir(parents=True, exist_ok=True)

    def propose_from_message(
        self,
        message: MessageRecord,
    ) -> KnowledgeCandidateRecord | None:
        draft = _candidate_draft(message.content)
        if draft is None:
            return None
        candidate_id = str(uuid4())
        now = _now()
        try:
            with (
                self.operation_lock,
                closing(self._connection()) as connection,
                connection,
            ):
                duplicate = self._find_duplicate(
                    connection,
                    draft.kind,
                    draft.title,
                    draft.content,
                )
                duplicate_record_id = (
                    str(duplicate[0]["id"]) if duplicate is not None else None
                )
                duplicate_score = duplicate[1] if duplicate is not None else None
                connection.execute(
                    """
                    INSERT OR IGNORE INTO knowledge_candidates (
                        id, conversation_id, source_message_id, kind, title,
                        content, source_excerpt, reason, confidence,
                        explicit_request, status, created_at, reviewed_at,
                        duplicate_record_id, duplicate_score
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, NULL, ?, ?
                    )
                    """,
                    (
                        candidate_id,
                        message.conversation_id,
                        message.id,
                        draft.kind,
                        draft.title,
                        draft.content,
                        message.content[:500],
                        draft.reason,
                        draft.confidence,
                        int(draft.explicit_request),
                        now,
                        duplicate_record_id,
                        duplicate_score,
                    ),
                )
                row = connection.execute(
                    _CANDIDATE_QUERY + " WHERE candidate.source_message_id = ?",
                    (message.id,),
                ).fetchone()
                if row is None:
                    raise KnowledgeProposalError(
                        "Nova could not prepare the knowledge proposal."
                    )
                if str(row["id"]) == candidate_id:
                    connection.execute(
                        """
                        INSERT INTO knowledge_events (
                            candidate_id, event_type, detail, created_at
                        ) VALUES (?, 'proposed', ?, ?)
                        """,
                        (candidate_id, draft.reason, now),
                    )
        except sqlite3.Error as error:
            raise KnowledgeProposalError(
                "Chat is available, but Nova could not prepare a memory review."
            ) from error
        return _candidate_from_row(row)

    def list_candidates(
        self,
        status: str | None = None,
    ) -> list[KnowledgeCandidateRecord]:
        query = _CANDIDATE_QUERY
        parameters: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE candidate.status = ?"
            parameters = (status,)
        query += " ORDER BY candidate.created_at DESC"
        with closing(self._connection()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_candidate_from_row(row) for row in rows]

    def list_records(self) -> list[KnowledgeRecord]:
        with closing(self._connection()) as connection:
            rows = connection.execute(
                """
                SELECT
                    id, candidate_id, kind, title, content,
                    relative_path, sha256, created_at, status, revision,
                    updated_at, retired_at
                FROM knowledge_records
                ORDER BY
                    CASE status WHEN 'active' THEN 0 ELSE 1 END,
                    updated_at DESC,
                    id
                """
            ).fetchall()
        return [_knowledge_record_from_row(row) for row in rows]

    def quality_report(self) -> KnowledgeQualityReportRecord:
        generated_at = datetime.now(UTC)
        with closing(self._connection()) as connection:
            rows = connection.execute(
                """
                SELECT
                    record.id, record.candidate_id, record.kind, record.title,
                    record.content, record.relative_path, record.sha256,
                    record.created_at, record.status, record.revision,
                    record.updated_at, record.retired_at
                FROM knowledge_records AS record
                JOIN knowledge_candidates AS candidate
                  ON candidate.id = record.candidate_id
                WHERE candidate.status = 'approved'
                ORDER BY record.updated_at DESC, record.id
                """
            ).fetchall()
        records = [_knowledge_record_from_row(row) for row in rows]
        active_records = [record for record in records if record.status == "active"]
        retired_record_count = sum(
            record.status == "retired" for record in records
        )

        # A quality report must never count an unverified record as knowledge.
        for record in active_records:
            self._verify_record_file(record.relative_path, record.sha256)

        requirement_statuses: list[KnowledgeRequirementStatusRecord] = []
        for definition in _KNOWLEDGE_REQUIREMENTS:
            matched = tuple(
                record
                for record in active_records
                if _requirement_matches(definition, record)
            )
            last_reviewed = max(
                (_parse_timestamp(record.updated_at) for record in matched),
                default=None,
            )
            if last_reviewed is None:
                status = "missing"
            elif generated_at - last_reviewed > timedelta(
                days=definition.review_days
            ):
                status = "stale"
            else:
                status = "covered"
            requirement_statuses.append(
                KnowledgeRequirementStatusRecord(
                    id=definition.id,
                    domain=definition.domain,
                    title=definition.title,
                    why=definition.why,
                    suggestion=definition.suggestion,
                    priority=definition.priority,
                    core=definition.core,
                    review_days=definition.review_days,
                    status=status,
                    last_reviewed=(
                        last_reviewed.isoformat()
                        if last_reviewed is not None
                        else None
                    ),
                    matched_record_ids=tuple(record.id for record in matched),
                    matched_record_titles=tuple(
                        record.title for record in matched
                    ),
                )
            )

        core_requirements = tuple(
            item for item in requirement_statuses if item.core
        )
        core_weight = sum(item.priority for item in core_requirements)
        covered_core_weight = sum(
            item.priority
            for item in core_requirements
            if item.status != "missing"
        )
        covered_requirements = tuple(
            item for item in requirement_statuses if item.status != "missing"
        )
        covered_weight = sum(item.priority for item in covered_requirements)
        fresh_weight = sum(
            item.priority
            for item in covered_requirements
            if item.status == "covered"
        )

        retrieval_limit = 100
        retrieval_sample = active_records[:retrieval_limit]
        retrieval_failures: list[RetrievalQualityFailureRecord] = []
        retrieval_passed = 0
        for record in retrieval_sample:
            sources = self.retrieve_approved(record.title, limit=3)
            if any(source.record_id == record.id for source in sources):
                retrieval_passed += 1
            else:
                retrieval_failures.append(
                    RetrievalQualityFailureRecord(
                        record_id=record.id,
                        title=record.title,
                        reason=(
                            "The record was not returned in the first three "
                            "deterministic title matches."
                        ),
                    )
                )

        return KnowledgeQualityReportRecord(
            generated_at=generated_at.isoformat(),
            active_record_count=len(active_records),
            retired_record_count=retired_record_count,
            core_covered=sum(
                item.status != "missing" for item in core_requirements
            ),
            core_total=len(core_requirements),
            completion_percent=_percentage(
                covered_core_weight,
                core_weight,
            ),
            fresh_covered=sum(
                item.status == "covered" for item in covered_requirements
            ),
            covered_total=len(covered_requirements),
            freshness_percent=_percentage(fresh_weight, covered_weight),
            retrieval_total_records=len(active_records),
            retrieval_checked=len(retrieval_sample),
            retrieval_passed=retrieval_passed,
            retrieval_percent=_percentage(
                retrieval_passed,
                len(retrieval_sample),
            ),
            retrieval_check_limit=retrieval_limit,
            requirements=tuple(requirement_statuses),
            retrieval_failures=tuple(retrieval_failures),
            methodology=(
                "Core coverage is priority-weighted against NOVA's published "
                "seven-item capability checklist. Stale items remain covered "
                "but reduce the priority-weighted freshness score. Optional "
                "items never reduce core coverage. Retrieval quality checks "
                "whether each verified active record appears in the first "
                "three deterministic title matches, up to 100 records."
            ),
            limitation=(
                "This report measures NOVA's approved local knowledge against "
                "a transparent capability checklist. It does not measure or "
                "score the owner, and it never changes knowledge."
            ),
        )

    def retrieve_approved(
        self,
        query: str,
        limit: int = 3,
    ) -> list[KnowledgeSourceRecord]:
        query_tokens = _retrieval_tokens(query)
        if not query_tokens or limit < 1:
            return []
        with closing(self._connection()) as connection:
            rows = connection.execute(
                """
                SELECT
                    record.id,
                    record.kind,
                    record.title,
                    record.content,
                    record.relative_path,
                    record.sha256
                FROM knowledge_records AS record
                JOIN knowledge_candidates AS candidate
                  ON candidate.id = record.candidate_id
                WHERE candidate.status = 'approved'
                  AND record.status = 'active'
                ORDER BY record.created_at DESC, record.id
                """
            ).fetchall()

        ranked: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            score = _retrieval_score(
                query_tokens,
                str(row["title"]),
                str(row["content"]),
                str(row["kind"]),
            )
            if score > 0.0:
                ranked.append((score, row))
        ranked.sort(key=lambda item: (-item[0], str(item[1]["id"])))

        sources: list[KnowledgeSourceRecord] = []
        for position, (score, row) in enumerate(ranked[:limit], start=1):
            relative_path = str(row["relative_path"])
            self._verify_record_file(relative_path, str(row["sha256"]))
            sources.append(
                KnowledgeSourceRecord(
                    record_id=str(row["id"]),
                    citation_label=f"K{position}",
                    title=str(row["title"]),
                    kind=str(row["kind"]),
                    content=str(row["content"]),
                    relative_path=relative_path,
                    sha256=str(row["sha256"]),
                    score=round(score, 6),
                )
            )
        return sources

    def reject_candidate(self, candidate_id: str) -> KnowledgeCandidateRecord:
        now = _now()
        with self.operation_lock, closing(self._connection()) as connection, connection:
            self._pending_row(connection, candidate_id)
            connection.execute(
                """
                    UPDATE knowledge_candidates
                    SET status = 'rejected', reviewed_at = ?
                    WHERE id = ?
                    """,
                (now, candidate_id),
            )
            connection.execute(
                """
                    INSERT INTO knowledge_events (
                        candidate_id, event_type, detail, created_at
                    ) VALUES (?, 'rejected', ?, ?)
                    """,
                (candidate_id, "The owner rejected the proposed record.", now),
            )
            row = connection.execute(
                _CANDIDATE_QUERY + " WHERE candidate.id = ?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            raise KnowledgeCandidateNotFoundError(candidate_id)
        return _candidate_from_row(row)

    def approve_candidate(
        self,
        candidate_id: str,
        kind: str,
        title: str,
        content: str,
        duplicate_confirmation: str | None = None,
    ) -> KnowledgeCandidateRecord:
        normalized_kind, normalized_title, normalized_content = _validate_record_fields(
            kind,
            title,
            content,
        )

        record_id = str(uuid4())
        now = _now()
        relative_path = self._relative_record_path(
            normalized_kind,
            normalized_title,
            record_id,
            now,
        )
        full_path = self.knowledge_path / relative_path
        payload = _markdown_record(
            record_id=record_id,
            candidate_id=candidate_id,
            kind=normalized_kind,
            title=normalized_title,
            content=normalized_content,
            created_at=now,
        )
        encoded = payload.encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()

        with self.operation_lock, closing(self._connection()) as connection:
            self._pending_row(connection, candidate_id)
            duplicate = self._find_duplicate(
                connection,
                normalized_kind,
                normalized_title,
                normalized_content,
            )
            if (
                duplicate is not None
                and duplicate_confirmation != "CREATE SEPARATE RECORD"
            ):
                raise KnowledgeDuplicateConfirmationError(
                    "This looks like an existing active record. Review the "
                    "possible duplicate before choosing Create separate record."
                )
            full_path.parent.mkdir(parents=True, exist_ok=True)
            file_created = False
            try:
                _write_exclusive(full_path, encoded)
                file_created = True
                with connection:
                    connection.execute(
                        """
                            INSERT INTO knowledge_records (
                                id, candidate_id, kind, title, content,
                                relative_path, sha256, created_at, status,
                                revision, updated_at, retired_at
                            ) VALUES (
                                ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1, ?, NULL
                            )
                            """,
                        (
                            record_id,
                            candidate_id,
                            normalized_kind,
                            normalized_title,
                            normalized_content,
                            relative_path.as_posix(),
                            digest,
                            now,
                            now,
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO knowledge_record_revisions (
                            record_id, revision, kind, title, content,
                            relative_path, sha256, status, created_at
                        ) VALUES (?, 1, ?, ?, ?, ?, ?, 'active', ?)
                        """,
                        (
                            record_id,
                            normalized_kind,
                            normalized_title,
                            normalized_content,
                            relative_path.as_posix(),
                            digest,
                            now,
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO knowledge_record_events (
                            record_id, event_type, detail, created_at
                        ) VALUES (?, 'created', ?, ?)
                        """,
                        (
                            record_id,
                            json.dumps(
                                {
                                    "relative_path": relative_path.as_posix(),
                                    "sha256": digest,
                                },
                                sort_keys=True,
                            ),
                            now,
                        ),
                    )
                    connection.execute(
                        """
                            UPDATE knowledge_candidates
                            SET
                                kind = ?,
                                title = ?,
                                content = ?,
                                status = 'approved',
                                reviewed_at = ?
                            WHERE id = ?
                            """,
                        (
                            normalized_kind,
                            normalized_title,
                            normalized_content,
                            now,
                            candidate_id,
                        ),
                    )
                    connection.execute(
                        """
                            INSERT INTO knowledge_events (
                                candidate_id, event_type, detail, created_at
                            ) VALUES (?, 'approved', ?, ?)
                            """,
                        (
                            candidate_id,
                            f"Saved owner-approved record to {relative_path.as_posix()}.",
                            now,
                        ),
                    )
            except Exception as error:
                if file_created and full_path.exists():
                    full_path.unlink()
                if isinstance(error, (ValueError, KnowledgeCandidateStateError)):
                    raise
                raise KnowledgeRecordWriteError(
                    "Nova could not safely save the approved knowledge record."
                ) from error
            row = connection.execute(
                _CANDIDATE_QUERY + " WHERE candidate.id = ?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            raise KnowledgeCandidateNotFoundError(candidate_id)
        return _candidate_from_row(row)

    def update_record(
        self,
        record_id: str,
        kind: str,
        title: str,
        content: str,
        duplicate_confirmation: str | None = None,
    ) -> KnowledgeRecord:
        normalized_kind, normalized_title, normalized_content = _validate_record_fields(
            kind,
            title,
            content,
        )
        now = _now()
        with self.operation_lock, closing(self._connection()) as connection:
            row = self._record_row(connection, record_id)
            if str(row["status"]) != "active":
                raise KnowledgeRecordStateError(
                    "Retired knowledge cannot be edited. Create a new proposal instead."
                )
            self._verify_record_file(
                str(row["relative_path"]),
                str(row["sha256"]),
            )
            duplicate = self._find_duplicate(
                connection,
                normalized_kind,
                normalized_title,
                normalized_content,
                exclude_record_id=record_id,
            )
            if (
                duplicate is not None
                and duplicate_confirmation != "CREATE SEPARATE RECORD"
            ):
                raise KnowledgeDuplicateConfirmationError(
                    "This edit looks like another active record. Review the "
                    "possible duplicate before keeping a separate record."
                )
            revision = int(row["revision"]) + 1
            relative_path = self._relative_record_revision_path(
                normalized_kind,
                normalized_title,
                record_id,
                revision,
                now,
            )
            full_path = self.knowledge_path / relative_path
            payload = _markdown_record(
                record_id=record_id,
                candidate_id=str(row["candidate_id"]),
                kind=normalized_kind,
                title=normalized_title,
                content=normalized_content,
                created_at=now,
                revision=revision,
            )
            encoded = payload.encode("utf-8")
            digest = hashlib.sha256(encoded).hexdigest()
            full_path.parent.mkdir(parents=True, exist_ok=True)
            file_created = False
            try:
                _write_exclusive(full_path, encoded)
                file_created = True
                with connection:
                    connection.execute(
                        """
                        INSERT INTO knowledge_record_revisions (
                            record_id, revision, kind, title, content,
                            relative_path, sha256, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                        """,
                        (
                            record_id,
                            revision,
                            normalized_kind,
                            normalized_title,
                            normalized_content,
                            relative_path.as_posix(),
                            digest,
                            now,
                        ),
                    )
                    connection.execute(
                        """
                        UPDATE knowledge_records
                        SET
                            kind = ?,
                            title = ?,
                            content = ?,
                            relative_path = ?,
                            sha256 = ?,
                            revision = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            normalized_kind,
                            normalized_title,
                            normalized_content,
                            relative_path.as_posix(),
                            digest,
                            revision,
                            now,
                            record_id,
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO knowledge_record_events (
                            record_id, event_type, detail, created_at
                        ) VALUES (?, 'updated', ?, ?)
                        """,
                        (
                            record_id,
                            json.dumps(
                                {
                                    "previous_revision": int(row["revision"]),
                                    "previous_path": str(row["relative_path"]),
                                    "previous_sha256": str(row["sha256"]),
                                    "new_revision": revision,
                                    "new_path": relative_path.as_posix(),
                                    "new_sha256": digest,
                                },
                                sort_keys=True,
                            ),
                            now,
                        ),
                    )
            except Exception as error:
                if file_created and full_path.exists():
                    full_path.unlink()
                if isinstance(
                    error,
                    (
                        ValueError,
                        KnowledgeDuplicateConfirmationError,
                        KnowledgeRecordStateError,
                    ),
                ):
                    raise
                raise KnowledgeRecordWriteError(
                    "Nova could not safely update the approved knowledge record."
                ) from error
            updated = self._record_row(connection, record_id)
        return _knowledge_record_from_row(updated)

    def retire_record(
        self,
        record_id: str,
        confirmation: str,
    ) -> KnowledgeRecord:
        expected = f"RETIRE {record_id[:8]}"
        if not hmac.compare_digest(confirmation, expected):
            raise ValueError(f"Type {expected} to retire this record.")
        now = _now()
        with (
            self.operation_lock,
            closing(self._connection()) as connection,
            connection,
        ):
            row = self._record_row(connection, record_id)
            if str(row["status"]) != "active":
                raise KnowledgeRecordStateError(
                    "This knowledge record is already retired."
                )
            self._verify_record_file(
                str(row["relative_path"]),
                str(row["sha256"]),
            )
            revision = int(row["revision"]) + 1
            connection.execute(
                """
                INSERT INTO knowledge_record_revisions (
                    record_id, revision, kind, title, content,
                    relative_path, sha256, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'retired', ?)
                """,
                (
                    record_id,
                    revision,
                    str(row["kind"]),
                    str(row["title"]),
                    str(row["content"]),
                    str(row["relative_path"]),
                    str(row["sha256"]),
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE knowledge_records
                SET status = 'retired', revision = ?, updated_at = ?,
                    retired_at = ?
                WHERE id = ?
                """,
                (revision, now, now, record_id),
            )
            connection.execute(
                """
                INSERT INTO knowledge_record_events (
                    record_id, event_type, detail, created_at
                ) VALUES (?, 'retired', ?, ?)
                """,
                (
                    record_id,
                    json.dumps(
                        {
                            "revision": revision,
                            "retained_path": str(row["relative_path"]),
                            "sha256": str(row["sha256"]),
                        },
                        sort_keys=True,
                    ),
                    now,
                ),
            )
            updated = self._record_row(connection, record_id)
        return _knowledge_record_from_row(updated)

    def create_snapshot(self) -> KnowledgeSnapshotRecord:
        now = _now()
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        filename = f"nova-knowledge-{timestamp}.zip"
        snapshot_root = self.backup_path / "knowledge"
        final_path = snapshot_root / filename
        temporary_path = snapshot_root / f".{filename}.{uuid4().hex}.tmp"
        sidecar_path = final_path.with_suffix(".zip.sha256")

        with self.operation_lock, closing(self._connection()) as connection:
            records = connection.execute(
                """
                SELECT
                    id, candidate_id, kind, title, content, relative_path,
                    sha256, created_at, status, revision, updated_at, retired_at
                FROM knowledge_records
                ORDER BY id
                """
            ).fetchall()
            revisions = connection.execute(
                """
                SELECT
                    record_id, revision, relative_path, sha256, status,
                    created_at
                FROM knowledge_record_revisions
                ORDER BY record_id, revision
                """
            ).fetchall()
            files: dict[str, tuple[Path, str]] = {}
            try:
                for revision in revisions:
                    relative_path = str(revision["relative_path"])
                    expected_sha256 = str(revision["sha256"])
                    verified_path = self._verify_record_file(
                        relative_path,
                        expected_sha256,
                    )
                    existing = files.get(relative_path)
                    if existing is not None and existing[1] != expected_sha256:
                        raise KnowledgeBackupError(
                            "Knowledge snapshot stopped because one path has "
                            "conflicting recorded checksums."
                        )
                    files[relative_path] = (verified_path, expected_sha256)

                manifest = {
                    "format": "nova-knowledge-snapshot-v1",
                    "created_at": now,
                    "record_count": len(records),
                    "file_count": len(files),
                    "records": [dict(record) for record in records],
                    "revisions": [dict(revision) for revision in revisions],
                }
                with zipfile.ZipFile(
                    temporary_path,
                    "x",
                    compression=zipfile.ZIP_DEFLATED,
                ) as archive:
                    archive.writestr(
                        "manifest.json",
                        json.dumps(
                            manifest,
                            indent=2,
                            sort_keys=True,
                            ensure_ascii=False,
                        )
                        + "\n",
                    )
                    for relative_path, (verified_path, _) in sorted(files.items()):
                        archive.write(
                            verified_path,
                            (Path("knowledge") / relative_path).as_posix(),
                        )
                with zipfile.ZipFile(temporary_path, "r") as archive:
                    if archive.testzip() is not None:
                        raise KnowledgeBackupError(
                            "Knowledge snapshot failed its ZIP integrity check."
                        )
                digest = hashlib.sha256(temporary_path.read_bytes()).hexdigest()
                os.replace(temporary_path, final_path)
                _write_exclusive(
                    sidecar_path,
                    f"{digest}  {filename}\n".encode(),
                )
            except Exception as error:
                temporary_path.unlink(missing_ok=True)
                final_path.unlink(missing_ok=True)
                sidecar_path.unlink(missing_ok=True)
                if isinstance(
                    error,
                    (KnowledgeBackupError, KnowledgeRetrievalError),
                ):
                    raise KnowledgeBackupError(str(error)) from error
                raise KnowledgeBackupError(
                    "Nova could not create a verified knowledge snapshot."
                ) from error

        return KnowledgeSnapshotRecord(
            filename=filename,
            size_bytes=final_path.stat().st_size,
            sha256=digest,
            record_count=len(records),
            file_count=len(files),
            created_at=now,
        )

    def _pending_row(
        self,
        connection: sqlite3.Connection,
        candidate_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT id, status FROM knowledge_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise KnowledgeCandidateNotFoundError(candidate_id)
        if str(row["status"]) != "pending":
            raise KnowledgeCandidateStateError(
                "This knowledge proposal has already been reviewed."
            )
        return cast(sqlite3.Row, row)

    def _relative_record_path(
        self,
        kind: str,
        title: str,
        record_id: str,
        created_at: str,
    ) -> Path:
        created_date = datetime.fromisoformat(created_at).date().isoformat()
        slug = _slug(title)
        return Path(_KIND_DIRECTORIES[kind]) / (
            f"{created_date} - {slug} - {record_id[:8]}.md"
        )

    def _relative_record_revision_path(
        self,
        kind: str,
        title: str,
        record_id: str,
        revision: int,
        created_at: str,
    ) -> Path:
        created_date = datetime.fromisoformat(created_at).date().isoformat()
        slug = _slug(title)
        return Path(_KIND_DIRECTORIES[kind]) / (
            f"{created_date} - {slug} - {record_id[:8]}-r{revision}.md"
        )

    def _record_row(
        self,
        connection: sqlite3.Connection,
        record_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT
                id, candidate_id, kind, title, content, relative_path,
                sha256, created_at, status, revision, updated_at, retired_at
            FROM knowledge_records
            WHERE id = ?
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            raise KnowledgeRecordNotFoundError(record_id)
        return cast(sqlite3.Row, row)

    def _find_duplicate(
        self,
        connection: sqlite3.Connection,
        kind: str,
        title: str,
        content: str,
        *,
        exclude_record_id: str | None = None,
    ) -> tuple[sqlite3.Row, float] | None:
        rows = connection.execute(
            """
            SELECT id, kind, title, content, relative_path
            FROM knowledge_records
            WHERE status = 'active'
              AND (? IS NULL OR id != ?)
            ORDER BY updated_at DESC, id
            """,
            (exclude_record_id, exclude_record_id),
        ).fetchall()
        requested_content = _normalized_duplicate_text(content)
        requested_tokens = _duplicate_tokens(f"{title} {content}")
        best: tuple[sqlite3.Row, float] | None = None
        for row in rows:
            existing_content = _normalized_duplicate_text(str(row["content"]))
            if requested_content == existing_content:
                score = 1.0
            elif str(row["kind"]) != kind:
                continue
            else:
                existing_tokens = _duplicate_tokens(
                    f"{row['title']} {row['content']}"
                )
                union = requested_tokens | existing_tokens
                score = (
                    len(requested_tokens & existing_tokens) / len(union)
                    if union
                    else 0.0
                )
            if score >= 0.8 and (best is None or score > best[1]):
                best = (row, round(score, 6))
        return best

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _verify_record_file(
        self,
        relative_path: str,
        expected_sha256: str,
    ) -> Path:
        try:
            root = self.knowledge_path.resolve(strict=True)
            record_path = (root / relative_path).resolve(strict=True)
            record_path.relative_to(root)
            actual_sha256 = hashlib.sha256(record_path.read_bytes()).hexdigest()
        except (OSError, ValueError) as error:
            raise KnowledgeRetrievalError(
                "Approved knowledge retrieval stopped because a cited local "
                "record could not be verified."
            ) from error
        if not hmac.compare_digest(actual_sha256, expected_sha256):
            raise KnowledgeRetrievalError(
                "Approved knowledge retrieval stopped because a cited local "
                "record failed its integrity check."
            )
        return record_path


_CANDIDATE_QUERY = """
    SELECT
        candidate.id,
        candidate.conversation_id,
        candidate.source_message_id,
        candidate.kind,
        candidate.title,
        candidate.content,
        candidate.source_excerpt,
        candidate.reason,
        candidate.confidence,
        candidate.explicit_request,
        candidate.status,
        candidate.created_at,
        candidate.reviewed_at,
        record.relative_path AS record_path,
        candidate.duplicate_record_id,
        duplicate.title AS duplicate_title,
        duplicate.relative_path AS duplicate_path,
        candidate.duplicate_score
    FROM knowledge_candidates AS candidate
    LEFT JOIN knowledge_records AS record
      ON record.candidate_id = candidate.id
    LEFT JOIN knowledge_records AS duplicate
      ON duplicate.id = candidate.duplicate_record_id
     AND duplicate.status = 'active'
"""


def _candidate_draft(content: str) -> CandidateDraft | None:
    compact = " ".join(content.split())
    if not compact or len(compact) > 4_000:
        return None
    for pattern in _EXPLICIT_PATTERNS:
        match = pattern.fullmatch(compact)
        if match and match.group(1).strip():
            remembered = _strip_terminal_punctuation(match.group(1).strip())
            kind = _infer_kind(remembered)
            return CandidateDraft(
                kind=kind,
                title=_suggest_title(remembered, kind),
                content=remembered,
                reason="You explicitly asked Nova to remember this.",
                confidence=1.0,
                explicit_request=True,
            )
    for kind, pattern, reason in _PROFILE_PATTERNS:
        match = pattern.fullmatch(compact)
        if not match:
            continue
        remembered = _strip_terminal_punctuation(compact)
        if kind == "fact" and "years old" in remembered.casefold():
            remembered = f"{remembered} (stated {datetime.now(UTC).date().isoformat()})"
        return CandidateDraft(
            kind=kind,
            title=_suggest_title(remembered, kind),
            content=remembered,
            reason=reason,
            confidence=0.85,
            explicit_request=False,
        )
    return None


def _infer_kind(content: str) -> str:
    lowered = content.casefold()
    if re.search(r"\b(?:prefer|preference|favourite|favorite)\b", lowered):
        return "preference"
    if re.search(r"\b(?:goal|aim|want to achieve)\b", lowered):
        return "goal"
    if re.search(r"\bproject\b", lowered):
        return "project"
    if re.search(r"\b(?:learned|lesson)\b", lowered):
        return "lesson"
    if re.search(r"\b(?:rule|always|never)\b", lowered):
        return "rule"
    if re.search(r"\b(?:manual|reference|documentation)\b", lowered):
        return "reference"
    return "fact"


def _suggest_title(content: str, kind: str) -> str:
    cleaned = re.sub(r"^(?:i\s+|my\s+)", "", content, flags=re.I)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > 72:
        cleaned = f"{cleaned[:69].rstrip()}..."
    if cleaned:
        return cleaned[0].upper() + cleaned[1:]
    return kind.capitalize()


def _strip_terminal_punctuation(value: str) -> str:
    return value.rstrip(" \t\r\n.!?")


def _validate_record_fields(
    kind: str,
    title: str,
    content: str,
) -> tuple[str, str, str]:
    normalized_kind = kind.strip().lower()
    normalized_title = " ".join(title.split())
    normalized_content = content.strip()
    if normalized_kind not in KNOWLEDGE_KINDS:
        raise ValueError("Choose a valid knowledge type.")
    if not normalized_title or len(normalized_title) > 120:
        raise ValueError("The knowledge title must be between 1 and 120 characters.")
    if not normalized_content or len(normalized_content) > 4_000:
        raise ValueError(
            "The knowledge content must be between 1 and 4,000 characters."
        )
    return normalized_kind, normalized_title, normalized_content


def _normalized_duplicate_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _duplicate_tokens(value: str) -> set[str]:
    return {
        token
        for token in _retrieval_tokens(value)
        if token not in {"remember", "saved", "record"}
    }


_RETRIEVAL_STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "please",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "you",
}
_RETRIEVAL_ALIASES = {
    "aim": "goal",
    "aims": "goal",
    "answer": "answer",
    "answers": "answer",
    "child": "child",
    "children": "child",
    "color": "colour",
    "colours": "colour",
    "colors": "colour",
    "daughter": "child",
    "favorite": "preference",
    "favourite": "preference",
    "favorites": "preference",
    "favourites": "preference",
    "goals": "goal",
    "husband": "partner",
    "objective": "goal",
    "objectives": "goal",
    "partner": "partner",
    "preference": "preference",
    "preferences": "preference",
    "prefer": "preference",
    "prefers": "preference",
    "project": "project",
    "projects": "project",
    "replies": "answer",
    "reply": "answer",
    "response": "answer",
    "responses": "answer",
    "son": "child",
    "spouse": "partner",
    "wife": "partner",
}


def _requirement_matches(
    definition: KnowledgeRequirementDefinition,
    record: KnowledgeRecord,
) -> bool:
    if record.kind in definition.match_kinds:
        return True
    searchable = f" {_normalized_phrase(f'{record.title} {record.content}')} "
    return any(
        f" {_normalized_phrase(phrase)} " in searchable
        for phrase in definition.match_phrases
    )


def _normalized_phrase(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _percentage(numerator: int, denominator: int) -> float:
    if denominator < 1:
        return 0.0
    return round((numerator / denominator) * 100.0, 1)


def _retrieval_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", value.casefold()):
        normalized = _RETRIEVAL_ALIASES.get(token, token)
        if len(normalized) < 3 or normalized in _RETRIEVAL_STOP_WORDS:
            continue
        tokens.add(normalized)
    return tokens


def _retrieval_score(
    query_tokens: set[str],
    title: str,
    content: str,
    kind: str,
) -> float:
    title_tokens = _retrieval_tokens(title)
    record_tokens = title_tokens | _retrieval_tokens(content) | {kind.casefold()}
    overlap = query_tokens & record_tokens
    required = 1 if len(query_tokens) == 1 else 2
    if len(overlap) < required:
        return 0.0
    title_overlap = overlap & title_tokens
    return (
        len(overlap) + (1.5 * len(title_overlap))
    ) / max(len(query_tokens), 1)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (slug[:60].rstrip("-") or "knowledge")


def _markdown_record(
    *,
    record_id: str,
    candidate_id: str,
    kind: str,
    title: str,
    content: str,
    created_at: str,
    revision: int = 1,
) -> str:
    metadata = {
        "id": record_id,
        "type": kind,
        "status": "active",
        "source": f"conversation-candidate:{candidate_id}",
        "owner_approved": True,
        "created": created_at,
        "last_reviewed": created_at,
        "revision": revision,
    }
    lines = ["---"]
    lines.extend(
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in metadata.items()
    )
    lines.extend(
        [
            "---",
            "",
            f"# {title}",
            "",
            content,
            "",
            "## Provenance",
            "",
            "Prepared from a local Nova conversation and saved only after "
            "explicit owner approval.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_exclusive(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _candidate_from_row(row: sqlite3.Row) -> KnowledgeCandidateRecord:
    return KnowledgeCandidateRecord(
        id=str(row["id"]),
        conversation_id=str(row["conversation_id"]),
        source_message_id=str(row["source_message_id"]),
        kind=str(row["kind"]),
        title=str(row["title"]),
        content=str(row["content"]),
        source_excerpt=str(row["source_excerpt"]),
        reason=str(row["reason"]),
        confidence=float(row["confidence"]),
        explicit_request=bool(row["explicit_request"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        reviewed_at=(
            str(row["reviewed_at"]) if row["reviewed_at"] is not None else None
        ),
        record_path=(
            str(row["record_path"]) if row["record_path"] is not None else None
        ),
        duplicate_record_id=(
            str(row["duplicate_record_id"])
            if row["duplicate_title"] is not None
            else None
        ),
        duplicate_title=(
            str(row["duplicate_title"])
            if row["duplicate_title"] is not None
            else None
        ),
        duplicate_path=(
            str(row["duplicate_path"])
            if row["duplicate_path"] is not None
            else None
        ),
        duplicate_score=(
            float(row["duplicate_score"])
            if row["duplicate_title"] is not None
            and row["duplicate_score"] is not None
            else None
        ),
    )


def _knowledge_record_from_row(row: sqlite3.Row) -> KnowledgeRecord:
    return KnowledgeRecord(
        id=str(row["id"]),
        candidate_id=str(row["candidate_id"]),
        kind=str(row["kind"]),
        title=str(row["title"]),
        content=str(row["content"]),
        relative_path=str(row["relative_path"]),
        sha256=str(row["sha256"]),
        created_at=str(row["created_at"]),
        status=str(row["status"]),
        revision=int(row["revision"]),
        updated_at=str(row["updated_at"]),
        retired_at=(
            str(row["retired_at"]) if row["retired_at"] is not None else None
        ),
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()
