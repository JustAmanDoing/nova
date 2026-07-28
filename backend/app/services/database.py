import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime


class DatabaseMigrationError(RuntimeError):
    """Raised when Nova cannot safely bring a database to the current schema."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]


def _observe_and_understand(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS intake_files (
            id TEXT PRIMARY KEY,
            relative_path TEXT NOT NULL UNIQUE,
            original_name TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            modified_at TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('observed', 'duplicate')),
            duplicate_of TEXT REFERENCES intake_files(id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_intake_files_sha256
        ON intake_files (sha256)
        """,
        """
        CREATE TABLE IF NOT EXISTS understanding_results (
            file_id TEXT PRIMARY KEY REFERENCES intake_files(id) ON DELETE CASCADE,
            source_sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('ready', 'empty', 'unsupported', 'too_large', 'failed')
            ),
            document_type TEXT,
            title TEXT,
            text_preview TEXT,
            word_count INTEGER,
            character_count INTEGER,
            evidence TEXT NOT NULL,
            error TEXT,
            error_code TEXT,
            extraction_method TEXT NOT NULL DEFAULT 'none',
            retryable INTEGER NOT NULL DEFAULT 0,
            full_text TEXT,
            understood_at TEXT NOT NULL
        )
        """,
    )
    _execute_all(connection, statements)


def _structured_extraction_and_search(connection: sqlite3.Connection) -> None:
    _add_column_if_missing(connection, "understanding_results", "error_code TEXT")
    _add_column_if_missing(
        connection,
        "understanding_results",
        "extraction_method TEXT NOT NULL DEFAULT 'none'",
    )
    _add_column_if_missing(
        connection,
        "understanding_results",
        "retryable INTEGER NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(connection, "understanding_results", "full_text TEXT")


def _deterministic_recommendations(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendation_results (
            file_id TEXT PRIMARY KEY
                REFERENCES intake_files(id) ON DELETE CASCADE,
            source_sha256 TEXT NOT NULL,
            source_status TEXT NOT NULL,
            source_understood_at TEXT,
            rules_version INTEGER NOT NULL,
            outcome TEXT NOT NULL CHECK (
                outcome IN ('suggested', 'insufficient_evidence')
            ),
            category TEXT,
            suggested_filename TEXT,
            destination TEXT,
            confidence REAL NOT NULL CHECK (
                confidence >= 0 AND confidence <= 1
            ),
            reasons TEXT NOT NULL,
            generated_at TEXT NOT NULL
        )
        """
    )
    _add_column_if_missing(
        connection,
        "recommendation_results",
        "source_status TEXT NOT NULL DEFAULT 'observed'",
    )
    _add_column_if_missing(
        connection,
        "recommendation_results",
        "source_understood_at TEXT",
    )


def _approval_review(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS approval_reviews (
            file_id TEXT PRIMARY KEY
                REFERENCES intake_files(id) ON DELETE CASCADE,
            recommendation_generated_at TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'approved', 'rejected', 'ignored')
            ),
            category TEXT NOT NULL,
            suggested_filename TEXT NOT NULL,
            destination TEXT NOT NULL,
            reviewed_at TEXT NOT NULL
        )
        """
    )


def _guarded_actions_and_audit(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS action_events (
            event_id TEXT PRIMARY KEY,
            operation_id TEXT NOT NULL,
            file_id TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('move', 'undo')),
            status TEXT NOT NULL CHECK (
                status IN ('started', 'succeeded', 'failed')
            ),
            source_path TEXT NOT NULL,
            destination_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            related_operation_id TEXT,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_action_events_operation
        ON action_events (operation_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_action_events_related
        ON action_events (related_operation_id)
        """,
    )
    _execute_all(connection, statements)


def _confirmed_move_learning(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS learning_examples (
            id TEXT PRIMARY KEY,
            operation_id TEXT NOT NULL UNIQUE,
            file_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            document_type TEXT NOT NULL,
            base_category TEXT NOT NULL,
            base_destination TEXT NOT NULL,
            approved_category TEXT NOT NULL,
            approved_destination TEXT NOT NULL,
            approved_filename TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reverted_at TEXT
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_learning_examples_preference
        ON learning_examples (
            document_type,
            base_category,
            approved_destination
        )
        WHERE reverted_at IS NULL
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_state (
            document_type TEXT NOT NULL,
            base_category TEXT NOT NULL,
            revision INTEGER NOT NULL,
            PRIMARY KEY (document_type, base_category)
        )
        """,
    )
    _execute_all(connection, statements)
    _add_column_if_missing(
        connection,
        "recommendation_results",
        "learning_revision INTEGER NOT NULL DEFAULT 0",
    )


def _learning_preference_controls(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS learning_events (
            event_id TEXT PRIMARY KEY,
            document_type TEXT NOT NULL,
            base_category TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind = 'reset'),
            removed_examples INTEGER NOT NULL CHECK (removed_examples >= 0),
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_learning_events_group
        ON learning_events (document_type, base_category, created_at)
        """,
    )
    _execute_all(connection, statements)


def _no_schema_change(_: sqlite3.Connection) -> None:
    return


def _local_chat_core(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            model TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_chat_conversations_updated
        ON chat_conversations (updated_at DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL
                REFERENCES chat_conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            model TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_chat_messages_conversation
        ON chat_messages (conversation_id, created_at, id)
        """,
    )
    _execute_all(connection, statements)


def _conversation_knowledge_capture(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS knowledge_candidates (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL
                REFERENCES chat_conversations(id) ON DELETE CASCADE,
            source_message_id TEXT NOT NULL
                REFERENCES chat_messages(id) ON DELETE CASCADE,
            kind TEXT NOT NULL CHECK (
                kind IN (
                    'fact', 'preference', 'goal', 'project',
                    'lesson', 'rule', 'reference'
                )
            ),
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_excerpt TEXT NOT NULL,
            reason TEXT NOT NULL,
            confidence REAL NOT NULL CHECK (
                confidence >= 0.0 AND confidence <= 1.0
            ),
            explicit_request INTEGER NOT NULL CHECK (
                explicit_request IN (0, 1)
            ),
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'approved', 'rejected')
            ),
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            UNIQUE (source_message_id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_candidates_status
        ON knowledge_candidates (status, created_at DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_records (
            id TEXT PRIMARY KEY,
            candidate_id TEXT NOT NULL UNIQUE
                REFERENCES knowledge_candidates(id),
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            relative_path TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_records_created
        ON knowledge_records (created_at DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL REFERENCES knowledge_candidates(id),
            event_type TEXT NOT NULL CHECK (
                event_type IN ('proposed', 'approved', 'rejected')
            ),
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_events_candidate
        ON knowledge_events (candidate_id, sequence)
        """,
    )
    _execute_all(connection, statements)


def _approved_knowledge_retrieval(connection: sqlite3.Connection) -> None:
    statements = (
        """
        ALTER TABLE chat_messages
        ADD COLUMN knowledge_checked INTEGER NOT NULL DEFAULT 0
            CHECK (knowledge_checked IN (0, 1))
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_message_knowledge_sources (
            message_id TEXT NOT NULL
                REFERENCES chat_messages(id) ON DELETE CASCADE,
            record_id TEXT NOT NULL
                REFERENCES knowledge_records(id) ON DELETE RESTRICT,
            citation_label TEXT NOT NULL,
            position INTEGER NOT NULL CHECK (position >= 1),
            score REAL NOT NULL CHECK (score > 0.0),
            title TEXT NOT NULL,
            kind TEXT NOT NULL,
            content TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            PRIMARY KEY (message_id, record_id),
            UNIQUE (message_id, citation_label),
            UNIQUE (message_id, position)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_chat_message_knowledge_sources_message
        ON chat_message_knowledge_sources (message_id, position)
        """,
    )
    _execute_all(connection, statements)


def _knowledge_lifecycle_and_duplicates(connection: sqlite3.Connection) -> None:
    _add_column_if_missing(
        connection,
        "knowledge_candidates",
        "duplicate_record_id TEXT REFERENCES knowledge_records(id)",
    )
    _add_column_if_missing(
        connection,
        "knowledge_candidates",
        "duplicate_score REAL",
    )
    _add_column_if_missing(
        connection,
        "knowledge_records",
        "status TEXT NOT NULL DEFAULT 'active' "
        "CHECK (status IN ('active', 'retired'))",
    )
    _add_column_if_missing(
        connection,
        "knowledge_records",
        "revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1)",
    )
    _add_column_if_missing(connection, "knowledge_records", "updated_at TEXT")
    _add_column_if_missing(connection, "knowledge_records", "retired_at TEXT")
    connection.execute(
        """
        UPDATE knowledge_records
        SET updated_at = created_at
        WHERE updated_at IS NULL
        """
    )
    statements = (
        """
        CREATE TABLE IF NOT EXISTS knowledge_record_revisions (
            record_id TEXT NOT NULL
                REFERENCES knowledge_records(id) ON DELETE RESTRICT,
            revision INTEGER NOT NULL CHECK (revision >= 1),
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('active', 'retired')),
            created_at TEXT NOT NULL,
            PRIMARY KEY (record_id, revision)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_record_revisions_path
        ON knowledge_record_revisions (relative_path)
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_record_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT NOT NULL
                REFERENCES knowledge_records(id) ON DELETE RESTRICT,
            event_type TEXT NOT NULL CHECK (
                event_type IN ('created', 'updated', 'retired')
            ),
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_record_events_record
        ON knowledge_record_events (record_id, sequence)
        """,
        """
        INSERT OR IGNORE INTO knowledge_record_revisions (
            record_id, revision, kind, title, content, relative_path,
            sha256, status, created_at
        )
        SELECT
            id, 1, kind, title, content, relative_path, sha256,
            'active', created_at
        FROM knowledge_records
        """,
        """
        INSERT INTO knowledge_record_events (
            record_id, event_type, detail, created_at
        )
        SELECT
            record.id,
            'created',
            'Imported existing approved record into lifecycle history.',
            record.created_at
        FROM knowledge_records AS record
        WHERE NOT EXISTS (
            SELECT 1
            FROM knowledge_record_events AS event
            WHERE event.record_id = record.id
        )
        """,
    )
    _execute_all(connection, statements)


MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "observe-and-understand", _observe_and_understand),
    Migration(2, "structured-extraction-and-search", _structured_extraction_and_search),
    Migration(3, "deterministic-recommendations", _deterministic_recommendations),
    Migration(4, "approval-review", _approval_review),
    Migration(5, "guarded-actions-and-audit", _guarded_actions_and_audit),
    Migration(6, "interrupted-operation-diagnostics", _no_schema_change),
    Migration(7, "verified-local-backups", _no_schema_change),
    Migration(8, "guarded-database-restore", _no_schema_change),
    Migration(9, "confirmed-move-learning", _confirmed_move_learning),
    Migration(10, "learning-preference-controls", _learning_preference_controls),
    Migration(11, "local-chat-core", _local_chat_core),
    Migration(12, "conversation-knowledge-capture", _conversation_knowledge_capture),
    Migration(13, "approved-knowledge-retrieval", _approved_knowledge_retrieval),
    Migration(
        14,
        "knowledge-lifecycle-and-duplicates",
        _knowledge_lifecycle_and_duplicates,
    ),
)
LATEST_SCHEMA_VERSION = MIGRATIONS[-1].version


def migrate_database(
    connection: sqlite3.Connection,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> None:
    _validate_migrations(migrations)
    verify_database_integrity(connection)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            version INTEGER NOT NULL
        )
        """
    )
    _refuse_newer_schema(connection, migrations[-1].version)
    applied = {
        int(row[0]): str(row[1])
        for row in connection.execute(
            "SELECT version, name FROM schema_migrations"
        )
    }
    expected_names = {migration.version: migration.name for migration in migrations}
    if any(
        expected_names.get(version) != name
        for version, name in applied.items()
        if version in expected_names
    ):
        raise DatabaseMigrationError(
            "Nova's recorded database migration history does not match this build."
        )

    for migration in migrations:
        if migration.version in applied:
            continue
        savepoint = f"nova_migration_{migration.version}"
        connection.execute(f"SAVEPOINT {savepoint}")
        try:
            migration.apply(connection)
            connection.execute(
                """
                INSERT INTO schema_migrations (version, name, applied_at)
                VALUES (?, ?, ?)
                """,
                (
                    migration.version,
                    migration.name,
                    datetime.now(UTC).isoformat(),
                ),
            )
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        except Exception as error:
            connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise DatabaseMigrationError(
                f"Database migration {migration.version} ({migration.name}) failed."
            ) from error

    connection.execute("UPDATE schema_meta SET version = ?", (migrations[-1].version,))
    connection.execute(
        """
        INSERT INTO schema_meta (version)
        SELECT ?
        WHERE NOT EXISTS (SELECT 1 FROM schema_meta)
        """,
        (migrations[-1].version,),
    )


def _refuse_newer_schema(
    connection: sqlite3.Connection,
    latest_supported: int,
) -> None:
    recorded_versions = [
        int(row[0])
        for row in connection.execute(
            """
            SELECT version FROM schema_migrations
            UNION ALL
            SELECT version FROM schema_meta
            """
        )
    ]
    if recorded_versions and max(recorded_versions) > latest_supported:
        raise DatabaseMigrationError(
            "This database was created by a newer Nova version and cannot be "
            "opened safely."
        )


def _validate_migrations(migrations: Sequence[Migration]) -> None:
    if not migrations:
        raise DatabaseMigrationError("Nova has no database migrations configured.")
    versions = [migration.version for migration in migrations]
    if versions != list(range(1, len(migrations) + 1)):
        raise DatabaseMigrationError(
            "Nova's database migrations are not a contiguous ordered sequence."
        )


def verify_database_integrity(connection: sqlite3.Connection) -> None:
    try:
        results = [
            str(row[0]) for row in connection.execute("PRAGMA quick_check")
        ]
    except sqlite3.DatabaseError as error:
        raise DatabaseMigrationError(
            "Nova's database could not be read safely. Stop Nova and restore "
            "a verified backup before continuing."
        ) from error
    if results != ["ok"]:
        raise DatabaseMigrationError(
            "Nova's database failed its integrity check. Stop Nova and restore "
            "a verified backup before continuing."
        )


def _execute_all(
    connection: sqlite3.Connection,
    statements: Sequence[str],
) -> None:
    for statement in statements:
        connection.execute(statement)


def _add_column_if_missing(
    connection: sqlite3.Connection,
    table: str,
    definition: str,
) -> None:
    column = definition.split()[0]
    columns = {
        str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")
    }
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
