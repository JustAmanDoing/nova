import hashlib
import json
import os
import re
import sqlite3
from _thread import RLock
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from app.services.chat import MessageRecord

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


class KnowledgeCandidateNotFoundError(LookupError):
    """Raised when a requested knowledge proposal does not exist."""


class KnowledgeCandidateStateError(RuntimeError):
    """Raised when a proposal has already been reviewed."""


class KnowledgeRecordWriteError(RuntimeError):
    """Raised when an approved record cannot be written safely."""


class KnowledgeProposalError(RuntimeError):
    """Raised when Nova cannot prepare an optional knowledge proposal."""


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
        operation_lock: RLock,
    ) -> None:
        self.database_path = database_path
        self.knowledge_path = knowledge_path
        self.operation_lock = operation_lock

    def initialize(self) -> None:
        self.knowledge_path.mkdir(parents=True, exist_ok=True)

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
                connection.execute(
                    """
                    INSERT OR IGNORE INTO knowledge_candidates (
                        id, conversation_id, source_message_id, kind, title,
                        content, source_excerpt, reason, confidence,
                        explicit_request, status, created_at, reviewed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, NULL)
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
                    relative_path, sha256, created_at
                FROM knowledge_records
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [_knowledge_record_from_row(row) for row in rows]

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
    ) -> KnowledgeCandidateRecord:
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
                                relative_path, sha256, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


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
        record.relative_path AS record_path
    FROM knowledge_candidates AS candidate
    LEFT JOIN knowledge_records AS record
      ON record.candidate_id = candidate.id
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
) -> str:
    metadata = {
        "id": record_id,
        "type": kind,
        "status": "active",
        "source": f"conversation-candidate:{candidate_id}",
        "owner_approved": True,
        "created": created_at,
        "last_reviewed": created_at,
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
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()
