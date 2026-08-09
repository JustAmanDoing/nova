import hashlib
import hmac
import re
import sqlite3
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.services.knowledge import (
    KnowledgeQualityReportRecord,
    KnowledgeRecord,
    KnowledgeRequirementStatusRecord,
    KnowledgeService,
    knowledge_duplicate_score,
)


@dataclass(frozen=True)
class LibrarianSourceRecord:
    record_id: str
    candidate_id: str
    kind: str
    title: str
    content: str
    status: str
    revision: int
    updated_at: str
    relative_path: str
    sha256: str
    verification_status: str
    candidate_confidence: float
    explicit_request: bool
    source_reason: str
    conversation_id: str
    source_message_id: str


@dataclass(frozen=True)
class LibrarianIssueRecord:
    id: str
    issue_type: str
    priority: str
    title: str
    summary: str
    reason: str
    evidence: tuple[str, ...]
    confidence: float
    record_ids: tuple[str, ...]
    source_titles: tuple[str, ...]
    suggested_action: str
    review_url: str | None


@dataclass(frozen=True)
class LibrarianHealthDimensionsRecord:
    coverage: float
    freshness: float
    retrieval: float
    integrity: float
    consistency: float


@dataclass(frozen=True)
class LibrarianIssueCountsRecord:
    duplicates: int
    conflicts: int
    stale: int
    missing_coverage: int
    missing_files: int
    checksum_failures: int
    broken_references: int


@dataclass(frozen=True)
class LibrarianHealthRecord:
    generated_at: str
    health_score: float
    dimensions: LibrarianHealthDimensionsRecord
    counts: LibrarianIssueCountsRecord
    active_record_count: int
    retired_record_count: int
    verified_source_count: int
    average_source_confidence: float | None
    methodology: str
    limitation: str


@dataclass(frozen=True)
class LibrarianReviewRecord:
    generated_at: str
    total: int
    issues: tuple[LibrarianIssueRecord, ...]
    limitation: str


@dataclass(frozen=True)
class LibrarianRevisionRecord:
    record_id: str
    revision: int
    status: str
    created_at: str
    relative_path: str
    sha256: str


@dataclass(frozen=True)
class LibrarianEventRecord:
    sequence: int
    record_id: str
    event_type: str
    detail: str
    created_at: str


@dataclass(frozen=True)
class LibrarianItemRecord:
    generated_at: str
    issue: LibrarianIssueRecord
    sources: tuple[LibrarianSourceRecord, ...]
    revisions: tuple[LibrarianRevisionRecord, ...]
    events: tuple[LibrarianEventRecord, ...]
    limitation: str


class LibrarianItemNotFoundError(LookupError):
    """Raised when a computed Librarian review item no longer exists."""


class LibrarianService:
    """Read-only analysis over NOVA's existing approved knowledge store."""

    def __init__(
        self,
        database_path: Path,
        knowledge_path: Path,
        knowledge: KnowledgeService,
    ) -> None:
        self.database_path = database_path
        self.knowledge_path = knowledge_path
        self.knowledge = knowledge

    def health(self) -> LibrarianHealthRecord:
        generated_at, sources, issues, quality = self._analysis()
        active = tuple(source for source in sources if source.status == "active")
        verified = tuple(source for source in active if source.verification_status == "verified")
        integrity = _percentage(len(verified), len(active), empty=100.0)
        consistency_record_ids = {
            record_id
            for issue in issues
            if issue.issue_type in {"duplicate", "conflict"}
            for record_id in issue.record_ids
        }
        consistency = _percentage(
            max(len(verified) - len(consistency_record_ids), 0),
            len(verified),
            empty=100.0,
        )
        dimensions = LibrarianHealthDimensionsRecord(
            coverage=quality.completion_percent,
            freshness=quality.freshness_percent,
            retrieval=quality.retrieval_percent,
            integrity=integrity,
            consistency=consistency,
        )
        score = round(
            sum(
                (
                    dimensions.coverage,
                    dimensions.freshness,
                    dimensions.retrieval,
                    dimensions.integrity,
                    dimensions.consistency,
                )
            )
            / 5,
            1,
        )
        counts = LibrarianIssueCountsRecord(
            duplicates=_count(issues, "duplicate"),
            conflicts=_count(issues, "conflict"),
            stale=_count(issues, "stale"),
            missing_coverage=_count(issues, "missing_coverage"),
            missing_files=_count(issues, "missing_file"),
            checksum_failures=_count(issues, "checksum_mismatch"),
            broken_references=_count(issues, "broken_reference"),
        )
        confidences = [source.candidate_confidence for source in active]
        return LibrarianHealthRecord(
            generated_at=generated_at,
            health_score=score,
            dimensions=dimensions,
            counts=counts,
            active_record_count=len(active),
            retired_record_count=len(sources) - len(active),
            verified_source_count=len(verified),
            average_source_confidence=(
                round(sum(confidences) / len(confidences), 3) if confidences else None
            ),
            methodology=(
                "Nova checks five things: whether useful information is present, "
                "up to date, easy to find, matches its saved files, and does not "
                "repeat or disagree. The score describes Nova's saved information, "
                "not the owner."
            ),
            limitation=(
                "The Librarian only shows suggestions. It cannot change, combine, "
                "remove, share, or make up saved information."
            ),
        )

    def review(self) -> LibrarianReviewRecord:
        generated_at, _, issues, _ = self._analysis()
        return LibrarianReviewRecord(
            generated_at=generated_at,
            total=len(issues),
            issues=issues,
            limitation=(
                "This list comes from your current saved information. It is not "
                "another copy, and opening an item changes nothing."
            ),
        )

    def item(self, item_id: str) -> LibrarianItemRecord:
        generated_at, sources, issues, _ = self._analysis()
        issue = next((item for item in issues if item.id == item_id), None)
        if issue is None:
            raise LibrarianItemNotFoundError(item_id)
        selected = tuple(source for source in sources if source.record_id in issue.record_ids)
        return LibrarianItemRecord(
            generated_at=generated_at,
            issue=issue,
            sources=selected,
            revisions=self._revisions(issue.record_ids),
            events=self._events(issue.record_ids),
            limitation=(
                "This page only explains the suggestion. Open it in Chat if you "
                "want to review it; nothing changes here."
            ),
        )

    def _analysis(
        self,
    ) -> tuple[
        str,
        tuple[LibrarianSourceRecord, ...],
        tuple[LibrarianIssueRecord, ...],
        KnowledgeQualityReportRecord,
    ]:
        generated_at = datetime.now(UTC).isoformat()
        rows = self._source_rows()
        active_ids = {str(row["id"]) for row in rows if str(row["status"]) == "active"}
        sources = tuple(self._source_from_row(row) for row in rows)
        verified_records = [
            _knowledge_record_from_source(source, "active")
            for source in sources
            if source.record_id in active_ids and source.verification_status == "verified"
        ]
        retired_records = [
            _knowledge_record_from_source(source, "retired")
            for source in sources
            if source.record_id not in active_ids
        ]
        quality = self.knowledge.quality_report_for_verified_records(
            verified_records + retired_records
        )
        source_by_id = {source.record_id: source for source in sources}
        issues = self._issues(
            sources,
            active_ids,
            verified_records,
            source_by_id,
            quality.requirements,
        )
        return generated_at, sources, issues, quality

    def _issues(
        self,
        sources: tuple[LibrarianSourceRecord, ...],
        active_ids: set[str],
        verified_records: list[KnowledgeRecord],
        source_by_id: dict[str, LibrarianSourceRecord],
        requirements: tuple[KnowledgeRequirementStatusRecord, ...],
    ) -> tuple[LibrarianIssueRecord, ...]:
        issues: list[LibrarianIssueRecord] = []
        for source in sources:
            if source.record_id not in active_ids or source.verification_status == "verified":
                continue
            issue_type = source.verification_status
            labels = {
                "missing_file": ("critical", "Saved file is missing"),
                "checksum_mismatch": ("critical", "Saved file changed unexpectedly"),
                "broken_reference": ("critical", "Saved file link does not work"),
            }
            reasons = {
                "missing_file": "The saved file is no longer where Nova expects it.",
                "checksum_mismatch": "The file no longer matches the version you approved.",
                "broken_reference": (
                    "The saved file points outside Nova's allowed knowledge folder."
                ),
            }
            problem_labels = {
                "missing_file": "File missing",
                "checksum_mismatch": "File changed",
                "broken_reference": "File link problem",
            }
            priority, title = labels[issue_type]
            issues.append(
                _issue(
                    issue_type,
                    source.record_id,
                    priority,
                    f"{title}: {source.title}",
                    "Nova cannot safely use this saved item right now.",
                    reasons[issue_type],
                    (
                        f"Problem: {problem_labels[issue_type]}.",
                        f"Expected file: {source.relative_path}.",
                        f"Saved file check code: {source.sha256}.",
                    ),
                    1.0,
                    (source.record_id,),
                    (source.title,),
                    (
                        "Open this item and check the file before making any changes."
                    ),
                    _record_url(source.record_id),
                )
            )

        for index, left in enumerate(verified_records):
            for right in verified_records[index + 1 :]:
                score = knowledge_duplicate_score(
                    left.kind,
                    left.title,
                    left.content,
                    right.kind,
                    right.title,
                    right.content,
                )
                if score < 0.8:
                    continue
                record_ids = tuple(sorted((left.id, right.id)))
                titles = tuple(source_by_id[item].title for item in record_ids)
                issues.append(
                    _issue(
                        "duplicate",
                        "|".join(record_ids),
                        "medium",
                        f"These may say the same thing: {titles[0]} and {titles[1]}",
                        "The two saved items are very similar.",
                        "Nova found a strong match using its usual saved-item comparison.",
                        (
                            f"Similarity: {score * 100:.0f}%.",
                            f"Saved items: {titles[0]} and {titles[1]}.",
                        ),
                        score,
                        record_ids,
                        titles,
                        (
                            "Compare both items. Keep, update, or remove one only "
                            "if you choose."
                        ),
                        _record_url(record_ids[0]),
                    )
                )

        title_groups: dict[str, list[KnowledgeRecord]] = defaultdict(list)
        for record in verified_records:
            title_groups[_normalized(record.title)].append(record)
        for normalized_title, records in title_groups.items():
            contents = {_normalized(record.content) for record in records}
            if not normalized_title or len(records) < 2 or len(contents) < 2:
                continue
            record_ids = tuple(sorted(record.id for record in records))
            titles = tuple(source_by_id[item].title for item in record_ids)
            issues.append(
                _issue(
                    "conflict",
                    "|".join(record_ids),
                    "high",
                    f"These may disagree: {titles[0]}",
                    "Two saved items have the same name but different information.",
                    (
                        "Nova can see that the names match and the text differs. "
                        "It cannot decide which one is right."
                    ),
                    (
                        f"Matching name: {titles[0]}.",
                        f"Different versions found: {len(contents)}.",
                    ),
                    1.0,
                    record_ids,
                    titles,
                    (
                        "Compare both saved items and update one only if you choose."
                    ),
                    _record_url(record_ids[0]),
                )
            )

        for requirement in requirements:
            if requirement.status == "stale":
                issues.append(
                    _issue(
                        "stale",
                        requirement.id,
                        "medium",
                        f"{requirement.title} may need checking",
                        f"This saved information has not been checked for "
                        f"{requirement.review_days} days.",
                        requirement.why,
                        (
                            f"Last checked: {requirement.last_reviewed}.",
                            f"Suggested check: every {requirement.review_days} days.",
                        ),
                        1.0,
                        requirement.matched_record_ids,
                        requirement.matched_record_titles,
                        (
                            "Open the saved item. Update it only if something has changed."
                        ),
                        (
                            _record_url(requirement.matched_record_ids[0])
                            if requirement.matched_record_ids
                            else None
                        ),
                    )
                )
            elif requirement.status == "missing":
                issues.append(
                    _issue(
                        "missing_coverage",
                        requirement.id,
                        "high" if requirement.core else "low",
                        requirement.title,
                        (
                            "You have not saved anything about this in Nova. "
                            "You can ignore this suggestion."
                        ),
                        requirement.why,
                        (
                            f"Area: {requirement.domain.title()}.",
                            (
                                "Suggested for basic Nova setup."
                                if requirement.core
                                else "Optional suggestion."
                            ),
                        ),
                        1.0,
                        (),
                        (),
                        requirement.suggestion,
                        f"/chat.html?knowledge={requirement.id}",
                    )
                )

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(
            key=lambda item: (priority_order[item.priority], item.issue_type, item.title, item.id)
        )
        return tuple(issues)

    def _source_rows(self) -> list[sqlite3.Row]:
        with closing(self._connection()) as connection:
            return connection.execute(
                """
                SELECT
                    record.id, record.candidate_id, record.kind, record.title,
                    record.content, record.relative_path, record.sha256,
                    record.created_at, record.status, record.revision,
                    record.updated_at, record.retired_at,
                    candidate.confidence, candidate.explicit_request,
                    candidate.reason, candidate.conversation_id,
                    candidate.source_message_id
                FROM knowledge_records AS record
                JOIN knowledge_candidates AS candidate
                  ON candidate.id = record.candidate_id
                WHERE candidate.status = 'approved'
                ORDER BY record.updated_at DESC, record.id
                """
            ).fetchall()

    def _source_from_row(self, row: sqlite3.Row) -> LibrarianSourceRecord:
        return LibrarianSourceRecord(
            record_id=str(row["id"]),
            candidate_id=str(row["candidate_id"]),
            kind=str(row["kind"]),
            title=str(row["title"]),
            content=str(row["content"]),
            status=str(row["status"]),
            revision=int(row["revision"]),
            updated_at=str(row["updated_at"]),
            relative_path=str(row["relative_path"]),
            sha256=str(row["sha256"]),
            verification_status=self._verification_status(
                str(row["relative_path"]), str(row["sha256"])
            ),
            candidate_confidence=float(row["confidence"]),
            explicit_request=bool(row["explicit_request"]),
            source_reason=str(row["reason"]),
            conversation_id=str(row["conversation_id"]),
            source_message_id=str(row["source_message_id"]),
        )

    def _verification_status(self, relative_path: str, expected_sha256: str) -> str:
        try:
            root = self.knowledge_path.resolve(strict=True)
            candidate = (root / relative_path).resolve(strict=False)
            candidate.relative_to(root)
        except (OSError, ValueError):
            return "broken_reference"
        if not candidate.is_file():
            return "missing_file"
        try:
            actual_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except OSError:
            return "broken_reference"
        return (
            "verified"
            if hmac.compare_digest(actual_sha256, expected_sha256)
            else "checksum_mismatch"
        )

    def _revisions(self, record_ids: tuple[str, ...]) -> tuple[LibrarianRevisionRecord, ...]:
        if not record_ids:
            return ()
        placeholders = ", ".join("?" for _ in record_ids)
        with closing(self._connection()) as connection:
            rows = connection.execute(
                f"""
                SELECT record_id, revision, status, created_at, relative_path, sha256
                FROM knowledge_record_revisions
                WHERE record_id IN ({placeholders})
                ORDER BY record_id, revision DESC
                """,
                record_ids,
            ).fetchall()
        return tuple(
            LibrarianRevisionRecord(
                record_id=str(row["record_id"]),
                revision=int(row["revision"]),
                status=str(row["status"]),
                created_at=str(row["created_at"]),
                relative_path=str(row["relative_path"]),
                sha256=str(row["sha256"]),
            )
            for row in rows
        )

    def _events(self, record_ids: tuple[str, ...]) -> tuple[LibrarianEventRecord, ...]:
        if not record_ids:
            return ()
        placeholders = ", ".join("?" for _ in record_ids)
        with closing(self._connection()) as connection:
            rows = connection.execute(
                f"""
                SELECT sequence, record_id, event_type, detail, created_at
                FROM knowledge_record_events
                WHERE record_id IN ({placeholders})
                ORDER BY sequence DESC
                """,
                record_ids,
            ).fetchall()
        return tuple(
            LibrarianEventRecord(
                sequence=int(row["sequence"]),
                record_id=str(row["record_id"]),
                event_type=str(row["event_type"]),
                detail=str(row["detail"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        )

    def _connection(self) -> sqlite3.Connection:
        database_uri = self.database_path.resolve().as_posix()
        connection = sqlite3.connect(f"file:{database_uri}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _knowledge_record_from_source(
    source: LibrarianSourceRecord,
    status: str,
) -> KnowledgeRecord:
    return KnowledgeRecord(
        id=source.record_id,
        candidate_id=source.candidate_id,
        kind=source.kind,
        title=source.title,
        content=source.content,
        relative_path=source.relative_path,
        sha256=source.sha256,
        created_at=source.updated_at,
        status=status,
        revision=source.revision,
        updated_at=source.updated_at,
        retired_at=None,
    )


def _issue(
    issue_type: str,
    key: str,
    priority: str,
    title: str,
    summary: str,
    reason: str,
    evidence: tuple[str, ...],
    confidence: float,
    record_ids: tuple[str, ...],
    source_titles: tuple[str, ...],
    suggested_action: str,
    review_url: str | None,
) -> LibrarianIssueRecord:
    digest = hashlib.sha256(f"{issue_type}|{key}".encode()).hexdigest()[:16]
    return LibrarianIssueRecord(
        id=f"lib-{digest}",
        issue_type=issue_type,
        priority=priority,
        title=title,
        summary=summary,
        reason=reason,
        evidence=evidence,
        confidence=confidence,
        record_ids=record_ids,
        source_titles=source_titles,
        suggested_action=suggested_action,
        review_url=review_url,
    )


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _record_url(record_id: str) -> str:
    return f"/chat.html?record={record_id}"


def _count(issues: tuple[LibrarianIssueRecord, ...], issue_type: str) -> int:
    return sum(issue.issue_type == issue_type for issue in issues)


def _percentage(numerator: int, denominator: int, *, empty: float) -> float:
    if denominator < 1:
        return empty
    return round((numerator / denominator) * 100, 1)
