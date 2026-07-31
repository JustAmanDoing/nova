import re
import sqlite3
from _thread import RLock
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import uuid4

from app.services.knowledge import KnowledgeService, PlanningKnowledgeItemRecord

NextActionStatus = Literal["open", "completed"]
NextActionEventType = Literal["created", "completed", "reopened"]

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
_LIMITATION = (
    "Next actions are entered explicitly by the owner and ordered "
    "deterministically by creation time. NOVA does not infer priority, "
    "progress, dates, deadlines, reminders, or additional actions."
)


class NextActionNotFoundError(LookupError):
    """Raised when a requested next action does not exist."""


class NextActionStateError(RuntimeError):
    """Raised when a state transition is not valid."""


class NextActionProjectError(ValueError):
    """Raised when a project association is not currently safe to use."""


@dataclass(frozen=True)
class NextActionRecord:
    id: str
    title: str
    status: NextActionStatus
    project_record_id: str | None
    project_title: str | None
    project_revision: int | None
    project_unavailable: bool
    created_at: str
    updated_at: str
    completed_at: str | None


@dataclass(frozen=True)
class NextActionOverviewRecord:
    generated_at: str
    open: list[NextActionRecord]
    completed: list[NextActionRecord]
    limitation: str


@dataclass(frozen=True)
class NextActionEventRecord:
    sequence: int
    action_id: str
    event_type: NextActionEventType
    detail: str
    created_at: str


class NextActionService:
    def __init__(
        self,
        database_path: str,
        knowledge: KnowledgeService,
        operation_lock: RLock,
    ) -> None:
        self.database_path = database_path
        self.knowledge = knowledge
        self.operation_lock = operation_lock

    def overview(self) -> NextActionOverviewRecord:
        projects = self._verified_projects()
        with closing(self._connection()) as connection:
            rows = connection.execute(
                """
                SELECT
                    id, title, project_record_id, status,
                    created_at, updated_at, completed_at
                FROM next_actions
                ORDER BY
                    CASE status WHEN 'open' THEN 0 ELSE 1 END,
                    CASE WHEN status = 'open' THEN created_at END ASC,
                    CASE WHEN status = 'completed' THEN completed_at END DESC,
                    id ASC
                """
            ).fetchall()
        actions = [self._record(row, projects) for row in rows]
        return NextActionOverviewRecord(
            generated_at=_timestamp(),
            open=[action for action in actions if action.status == "open"],
            completed=[
                action for action in actions if action.status == "completed"
            ],
            limitation=_LIMITATION,
        )

    def create(
        self,
        title: str,
        project_record_id: str | None = None,
    ) -> NextActionRecord:
        normalized_title = _normalize_title(title)
        projects = self._verified_projects()
        if project_record_id is not None and project_record_id not in projects:
            raise NextActionProjectError(
                "The selected project must be an active, verified local project."
            )
        timestamp = _timestamp()
        action_id = str(uuid4())
        with self.operation_lock, closing(self._connection()) as connection, connection:
            connection.execute(
                """
                INSERT INTO next_actions (
                    id, title, project_record_id, status,
                    created_at, updated_at, completed_at
                )
                VALUES (?, ?, ?, 'open', ?, ?, NULL)
                """,
                (
                    action_id,
                    normalized_title,
                    project_record_id,
                    timestamp,
                    timestamp,
                ),
            )
            self._record_event(
                connection,
                action_id,
                "created",
                "Owner created the next action through NOVA's local interface.",
                timestamp,
            )
            row = self._fetch_action(connection, action_id)
        return self._record(row, projects)

    def complete(self, action_id: str) -> NextActionRecord:
        return self._transition(action_id, "completed")

    def reopen(self, action_id: str) -> NextActionRecord:
        return self._transition(action_id, "open")

    def events(self, action_id: str) -> list[NextActionEventRecord]:
        with closing(self._connection()) as connection:
            self._fetch_action(connection, action_id)
            rows = connection.execute(
                """
                SELECT sequence, action_id, event_type, detail, created_at
                FROM next_action_events
                WHERE action_id = ?
                ORDER BY sequence ASC
                """,
                (action_id,),
            ).fetchall()
        return [
            NextActionEventRecord(
                sequence=int(row["sequence"]),
                action_id=str(row["action_id"]),
                event_type=cast(NextActionEventType, str(row["event_type"])),
                detail=str(row["detail"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def _transition(
        self,
        action_id: str,
        target_status: NextActionStatus,
    ) -> NextActionRecord:
        timestamp = _timestamp()
        event_type: NextActionEventType = (
            "completed" if target_status == "completed" else "reopened"
        )
        detail = (
            "Owner marked the next action complete through NOVA's local interface."
            if target_status == "completed"
            else "Owner reopened the next action through NOVA's local interface."
        )
        with self.operation_lock, closing(self._connection()) as connection, connection:
            existing = self._fetch_action(connection, action_id)
            current_status = cast(NextActionStatus, str(existing["status"]))
            if current_status == target_status:
                state = "complete" if target_status == "completed" else "open"
                raise NextActionStateError(
                    f"This next action is already {state}; nothing was changed."
                )
            connection.execute(
                """
                UPDATE next_actions
                SET status = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    target_status,
                    timestamp,
                    timestamp if target_status == "completed" else None,
                    action_id,
                ),
            )
            self._record_event(
                connection,
                action_id,
                event_type,
                detail,
                timestamp,
            )
            row = self._fetch_action(connection, action_id)
        return self._record(row, self._verified_projects())

    def _verified_projects(self) -> dict[str, PlanningKnowledgeItemRecord]:
        overview = self.knowledge.planning_overview()
        return {project.id: project for project in overview.projects}

    def _record(
        self,
        row: sqlite3.Row,
        projects: dict[str, PlanningKnowledgeItemRecord],
    ) -> NextActionRecord:
        project_record_id = (
            str(row["project_record_id"])
            if row["project_record_id"] is not None
            else None
        )
        project = (
            projects.get(project_record_id)
            if project_record_id is not None
            else None
        )
        return NextActionRecord(
            id=str(row["id"]),
            title=str(row["title"]),
            status=cast(NextActionStatus, str(row["status"])),
            project_record_id=project_record_id,
            project_title=project.title if project else None,
            project_revision=project.revision if project else None,
            project_unavailable=project_record_id is not None and project is None,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            completed_at=(
                str(row["completed_at"])
                if row["completed_at"] is not None
                else None
            ),
        )

    @staticmethod
    def _fetch_action(
        connection: sqlite3.Connection,
        action_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT
                id, title, project_record_id, status,
                created_at, updated_at, completed_at
            FROM next_actions
            WHERE id = ?
            """,
            (action_id,),
        ).fetchone()
        if row is None:
            raise NextActionNotFoundError(action_id)
        return cast(sqlite3.Row, row)

    @staticmethod
    def _record_event(
        connection: sqlite3.Connection,
        action_id: str,
        event_type: NextActionEventType,
        detail: str,
        created_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO next_action_events (
                action_id, event_type, detail, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (action_id, event_type, detail, created_at),
        )

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _normalize_title(title: str) -> str:
    normalized = " ".join(title.split())
    if not normalized:
        raise ValueError("A next action must include a title.")
    if len(normalized) > 200:
        raise ValueError("A next action title cannot exceed 200 characters.")
    if _CONTROL_CHARACTERS.search(normalized):
        raise ValueError("A next action title cannot contain control characters.")
    return normalized


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()
