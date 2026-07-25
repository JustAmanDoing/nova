import sqlite3
from dataclasses import dataclass
from uuid import uuid4

MINIMUM_CONFIRMED_EXAMPLES = 3
MINIMUM_PREFERENCE_SHARE = 0.75


@dataclass(frozen=True)
class LearnedDestination:
    destination: str
    supporting_examples: int
    total_examples: int

    @property
    def share(self) -> float:
        return self.supporting_examples / self.total_examples


@dataclass(frozen=True)
class LearningPreference:
    document_type: str
    base_category: str
    candidate_destination: str | None
    supporting_examples: int
    active_examples: int
    stored_examples: int
    eligible: bool
    revision: int

    @property
    def share(self) -> float:
        if self.active_examples == 0:
            return 0
        return self.supporting_examples / self.active_examples


@dataclass(frozen=True)
class LearningReset:
    document_type: str
    base_category: str
    removed_examples: int
    reset_at: str
    detail: str


def current_learning_revision(
    connection: sqlite3.Connection,
    *,
    document_type: str | None,
    base_category: str | None,
) -> int:
    if document_type is None or base_category is None:
        return 0
    row = connection.execute(
        """
        SELECT revision
        FROM learning_state
        WHERE document_type = ?
          AND base_category = ?
        """,
        (document_type, base_category),
    ).fetchone()
    return int(row[0]) if row is not None else 0


def record_confirmed_move(
    connection: sqlite3.Connection,
    *,
    operation_id: str,
    file_id: str,
    source_sha256: str,
    document_type: str,
    base_category: str,
    base_destination: str,
    approved_category: str,
    approved_destination: str,
    approved_filename: str,
    created_at: str,
) -> None:
    connection.execute("SAVEPOINT nova_learning_record")
    try:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO learning_examples (
                id, operation_id, file_id, source_sha256, document_type,
                base_category, base_destination, approved_category,
                approved_destination, approved_filename, created_at, reverted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                str(uuid4()),
                operation_id,
                file_id,
                source_sha256,
                document_type,
                base_category,
                base_destination,
                approved_category,
                approved_destination,
                approved_filename,
                created_at,
            ),
        )
        if cursor.rowcount:
            _advance_revision(
                connection,
                document_type=document_type,
                base_category=base_category,
            )
        connection.execute("RELEASE SAVEPOINT nova_learning_record")
    except sqlite3.Error:
        connection.execute("ROLLBACK TO SAVEPOINT nova_learning_record")
        connection.execute("RELEASE SAVEPOINT nova_learning_record")
        raise


def revert_confirmed_move(
    connection: sqlite3.Connection,
    *,
    operation_id: str,
    reverted_at: str,
) -> None:
    connection.execute("SAVEPOINT nova_learning_revert")
    try:
        example = connection.execute(
            """
            SELECT document_type, base_category
            FROM learning_examples
            WHERE operation_id = ?
              AND reverted_at IS NULL
            """,
            (operation_id,),
        ).fetchone()
        if example is not None:
            cursor = connection.execute(
                """
                UPDATE learning_examples
                SET reverted_at = ?
                WHERE operation_id = ?
                  AND reverted_at IS NULL
                """,
                (reverted_at, operation_id),
            )
            if cursor.rowcount:
                _advance_revision(
                    connection,
                    document_type=str(example["document_type"]),
                    base_category=str(example["base_category"]),
                )
        connection.execute("RELEASE SAVEPOINT nova_learning_revert")
    except sqlite3.Error:
        connection.execute("ROLLBACK TO SAVEPOINT nova_learning_revert")
        connection.execute("RELEASE SAVEPOINT nova_learning_revert")
        raise


def learned_destination(
    connection: sqlite3.Connection,
    *,
    document_type: str,
    base_category: str,
) -> LearnedDestination | None:
    rows = connection.execute(
        """
        SELECT approved_destination, COUNT(*) AS support
        FROM learning_examples
        WHERE document_type = ?
          AND base_category = ?
          AND reverted_at IS NULL
        GROUP BY approved_destination
        ORDER BY support DESC, approved_destination ASC
        """,
        (document_type, base_category),
    ).fetchall()
    if not rows:
        return None
    total = sum(int(row["support"]) for row in rows)
    top_support = int(rows[0]["support"])
    tied = len(rows) > 1 and int(rows[1]["support"]) == top_support
    if (
        tied
        or top_support < MINIMUM_CONFIRMED_EXAMPLES
        or top_support / total < MINIMUM_PREFERENCE_SHARE
    ):
        return None
    return LearnedDestination(
        destination=str(rows[0]["approved_destination"]),
        supporting_examples=top_support,
        total_examples=total,
    )


def list_learning_preferences(
    connection: sqlite3.Connection,
) -> list[LearningPreference]:
    rows = connection.execute(
        """
        SELECT examples.document_type, examples.base_category,
               examples.approved_destination,
               SUM(
                   CASE WHEN examples.reverted_at IS NULL THEN 1 ELSE 0 END
               ) AS active_support,
               COUNT(*) AS stored_support,
               COALESCE(state.revision, 0) AS revision
        FROM learning_examples AS examples
        LEFT JOIN learning_state AS state
          ON state.document_type = examples.document_type
         AND state.base_category = examples.base_category
        GROUP BY examples.document_type, examples.base_category,
                 examples.approved_destination, state.revision
        ORDER BY examples.document_type, examples.base_category,
                 active_support DESC, examples.approved_destination
        """
    ).fetchall()
    groups: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for row in rows:
        key = (str(row["document_type"]), str(row["base_category"]))
        groups.setdefault(key, []).append(row)

    preferences: list[LearningPreference] = []
    for (document_type, base_category), destinations in groups.items():
        active_examples = sum(
            int(destination["active_support"]) for destination in destinations
        )
        stored_examples = sum(
            int(destination["stored_support"]) for destination in destinations
        )
        top_support = (
            max(int(destination["active_support"]) for destination in destinations)
            if active_examples
            else 0
        )
        leaders = [
            destination
            for destination in destinations
            if int(destination["active_support"]) == top_support and top_support > 0
        ]
        candidate = (
            str(leaders[0]["approved_destination"])
            if len(leaders) == 1
            else None
        )
        eligible = (
            candidate is not None
            and top_support >= MINIMUM_CONFIRMED_EXAMPLES
            and top_support / active_examples >= MINIMUM_PREFERENCE_SHARE
        )
        preferences.append(
            LearningPreference(
                document_type=document_type,
                base_category=base_category,
                candidate_destination=candidate,
                supporting_examples=top_support,
                active_examples=active_examples,
                stored_examples=stored_examples,
                eligible=eligible,
                revision=int(destinations[0]["revision"]),
            )
        )
    return preferences


def reset_confirmation(document_type: str, base_category: str) -> str:
    return f"FORGET {document_type} / {base_category}"


def reset_learning_preference(
    connection: sqlite3.Connection,
    *,
    document_type: str,
    base_category: str,
    confirmation: str,
    reset_at: str,
) -> LearningReset:
    if confirmation != reset_confirmation(document_type, base_category):
        raise ValueError("The learning reset confirmation did not match.")
    stored = connection.execute(
        """
        SELECT COUNT(*)
        FROM learning_examples
        WHERE document_type = ?
          AND base_category = ?
        """,
        (document_type, base_category),
    ).fetchone()
    removed_examples = int(stored[0])
    if removed_examples == 0:
        raise LookupError("No stored learning preference exists for that group.")

    detail = (
        "Removed all stored learning examples for this document type and "
        "category. File and action history were not changed."
    )
    connection.execute("SAVEPOINT nova_learning_reset")
    try:
        connection.execute(
            """
            DELETE FROM learning_examples
            WHERE document_type = ?
              AND base_category = ?
            """,
            (document_type, base_category),
        )
        _advance_revision(
            connection,
            document_type=document_type,
            base_category=base_category,
        )
        connection.execute(
            """
            INSERT INTO learning_events (
                event_id, document_type, base_category, kind,
                removed_examples, detail, created_at
            )
            VALUES (?, ?, ?, 'reset', ?, ?, ?)
            """,
            (
                str(uuid4()),
                document_type,
                base_category,
                removed_examples,
                detail,
                reset_at,
            ),
        )
        connection.execute("RELEASE SAVEPOINT nova_learning_reset")
    except sqlite3.Error:
        connection.execute("ROLLBACK TO SAVEPOINT nova_learning_reset")
        connection.execute("RELEASE SAVEPOINT nova_learning_reset")
        raise
    return LearningReset(
        document_type=document_type,
        base_category=base_category,
        removed_examples=removed_examples,
        reset_at=reset_at,
        detail=detail,
    )


def _advance_revision(
    connection: sqlite3.Connection,
    *,
    document_type: str,
    base_category: str,
) -> None:
    connection.execute(
        """
        INSERT INTO learning_state (document_type, base_category, revision)
        VALUES (?, ?, 1)
        ON CONFLICT(document_type, base_category) DO UPDATE SET
            revision = learning_state.revision + 1
        """,
        (document_type, base_category),
    )
