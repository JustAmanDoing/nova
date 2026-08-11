import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.services.database import (
    LATEST_SCHEMA_VERSION,
    MIGRATIONS,
    DatabaseMigrationError,
    Migration,
    migrate_database,
)
from app.services.intake import IntakeService


def test_new_database_records_ordered_migration_history(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    service = IntakeService(tmp_path / "intake", database_path)

    service.initialize()
    service.initialize()

    with closing(sqlite3.connect(database_path)) as connection:
        applied = connection.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
        compatibility_version = connection.execute(
            "SELECT version FROM schema_meta"
        ).fetchall()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        recommendation_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(recommendation_results)")
        }

    assert [version for version, _ in applied] == list(
        range(1, LATEST_SCHEMA_VERSION + 1)
    )
    assert compatibility_version == [(LATEST_SCHEMA_VERSION,)]
    assert {
        "intake_files",
        "understanding_results",
        "recommendation_results",
        "approval_reviews",
        "action_events",
        "learning_examples",
        "learning_events",
        "learning_state",
        "chat_conversations",
        "chat_messages",
        "chat_message_capability_sources",
        "next_actions",
        "next_action_events",
        "schema_migrations",
    }.issubset(tables)
    assert "learning_revision" in recommendation_columns


def test_legacy_database_is_adopted_without_losing_records(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(
            """
            CREATE TABLE schema_meta (version INTEGER NOT NULL);
            INSERT INTO schema_meta VALUES (6);

            CREATE TABLE intake_files (
                id TEXT PRIMARY KEY,
                relative_path TEXT NOT NULL UNIQUE,
                original_name TEXT NOT NULL,
                extension TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                modified_at TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                duplicate_of TEXT
            );

            CREATE TABLE understanding_results (
                file_id TEXT PRIMARY KEY,
                source_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                document_type TEXT,
                title TEXT,
                text_preview TEXT,
                word_count INTEGER,
                character_count INTEGER,
                evidence TEXT NOT NULL,
                error TEXT,
                understood_at TEXT NOT NULL
            );

            CREATE TABLE recommendation_results (
                file_id TEXT PRIMARY KEY,
                source_sha256 TEXT NOT NULL,
                rules_version INTEGER NOT NULL,
                outcome TEXT NOT NULL,
                category TEXT,
                suggested_filename TEXT,
                destination TEXT,
                confidence REAL NOT NULL,
                reasons TEXT NOT NULL,
                generated_at TEXT NOT NULL
            );

            INSERT INTO intake_files VALUES (
                'legacy-file',
                'legacy.txt',
                'legacy.txt',
                '.txt',
                6,
                '2026-07-25T00:00:00+00:00',
                '2026-07-25T00:00:00+00:00',
                'abcdef',
                'observed',
                NULL
            );
            """
        )
        connection.commit()

    service = IntakeService(tmp_path / "intake", database_path)
    service.initialize()

    with closing(sqlite3.connect(database_path)) as connection:
        file_rows = connection.execute(
            "SELECT id, relative_path FROM intake_files"
        ).fetchall()
        understanding_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(understanding_results)")
        }
        recommendation_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(recommendation_results)")
        }
        applied = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()

    assert file_rows == [("legacy-file", "legacy.txt")]
    assert {
        "error_code",
        "extraction_method",
        "retryable",
        "full_text",
    }.issubset(understanding_columns)
    assert {
        "source_status",
        "source_understood_at",
        "learning_revision",
    }.issubset(
        recommendation_columns
    )
    assert applied == [
        (version,) for version in range(1, LATEST_SCHEMA_VERSION + 1)
    ]


def test_database_from_newer_nova_version_is_refused(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("CREATE TABLE schema_meta (version INTEGER NOT NULL)")
        connection.execute("INSERT INTO schema_meta VALUES (99)")
        connection.commit()

    service = IntakeService(tmp_path / "intake", database_path)

    with pytest.raises(DatabaseMigrationError, match="newer Nova version"):
        service.initialize()


def test_conversation_organisation_migration_preserves_existing_history(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        migrate_database(connection, MIGRATIONS[:-2])
        connection.execute(
            """
            INSERT INTO chat_conversations (
                id, title, model, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "existing-conversation",
                "Existing history",
                "qwen3:8b",
                "2026-07-31T00:00:00+00:00",
                "2026-07-31T00:01:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO chat_messages (
                id, conversation_id, role, content, model, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "existing-message",
                "existing-conversation",
                "user",
                "Existing private message",
                "qwen3:8b",
                "2026-07-31T00:01:00+00:00",
            ),
        )
        connection.commit()

    IntakeService(tmp_path / "intake", database_path).initialize()

    with closing(sqlite3.connect(database_path)) as connection:
        conversation = connection.execute(
            """
            SELECT title, model, archived_at, trashed_at
            FROM chat_conversations
            WHERE id = 'existing-conversation'
            """
        ).fetchone()
        message = connection.execute(
            "SELECT content FROM chat_messages WHERE id = 'existing-message'"
        ).fetchone()
        events = connection.execute(
            """
            SELECT event_type, new_status, created_at
            FROM chat_conversation_events
            WHERE conversation_id = 'existing-conversation'
            """
        ).fetchall()

    assert conversation == ("Existing history", "qwen3:8b", None, None)
    assert message == ("Existing private message",)
    assert events == [("created", "active", "2026-07-31T00:00:00+00:00")]


def test_conductor_evidence_migration_preserves_existing_chat(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        migrate_database(connection, MIGRATIONS[:-1])
        connection.execute(
            """
            INSERT INTO chat_conversations (
                id, title, model, created_at, updated_at
            ) VALUES ('existing-conversation', 'History', 'qwen3:8b', ?, ?)
            """,
            ("2026-08-09T00:00:00+00:00", "2026-08-09T00:01:00+00:00"),
        )
        connection.execute(
            """
            INSERT INTO chat_messages (
                id, conversation_id, role, content, model, created_at
            ) VALUES (
                'existing-message', 'existing-conversation', 'user',
                'Existing private message', 'qwen3:8b', ?
            )
            """,
            ("2026-08-09T00:01:00+00:00",),
        )
        connection.commit()

    IntakeService(tmp_path / "intake", database_path).initialize()

    with closing(sqlite3.connect(database_path)) as connection:
        message = connection.execute(
            "SELECT content FROM chat_messages WHERE id = 'existing-message'"
        ).fetchone()
        table = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'chat_message_capability_sources'
            """
        ).fetchone()
        version = connection.execute("SELECT version FROM schema_meta").fetchone()

    assert message == ("Existing private message",)
    assert table == ("chat_message_capability_sources",)
    assert version == (18,)


def test_unreadable_database_is_refused_before_migration(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    original_bytes = b"this is not a SQLite database"
    database_path.write_bytes(original_bytes)
    service = IntakeService(tmp_path / "intake", database_path)

    with pytest.raises(DatabaseMigrationError, match="restore a verified backup"):
        service.initialize()

    assert database_path.read_bytes() == original_bytes


def test_failed_migration_rolls_back_only_its_partial_schema() -> None:
    connection = sqlite3.connect(":memory:")

    def first(current: sqlite3.Connection) -> None:
        current.execute("CREATE TABLE stable (value TEXT)")

    def second(current: sqlite3.Connection) -> None:
        current.execute("CREATE TABLE partial (value TEXT)")
        raise RuntimeError("private migration failure")

    migrations = (
        Migration(1, "stable", first),
        Migration(2, "fails", second),
    )

    with pytest.raises(DatabaseMigrationError, match=r"migration 2 \(fails\)"):
        migrate_database(connection, migrations)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    applied = connection.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall()
    connection.close()

    assert "stable" in tables
    assert "partial" not in tables
    assert applied == [(1,)]


@pytest.mark.parametrize(
    "migrations",
    [
        (),
        (
            Migration(1, "first", lambda _: None),
            Migration(3, "gap", lambda _: None),
        ),
    ],
)
def test_invalid_migration_sequences_are_refused(
    migrations: tuple[Migration, ...],
) -> None:
    connection = sqlite3.connect(":memory:")

    with pytest.raises(DatabaseMigrationError, match="migrations"):
        migrate_database(connection, migrations)

    connection.close()


def test_changed_migration_history_is_refused() -> None:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        );
        INSERT INTO schema_migrations VALUES (
            1,
            'unexpected-history',
            '2026-07-25T00:00:00+00:00'
        );
        """
    )

    with pytest.raises(DatabaseMigrationError, match="history does not match"):
        migrate_database(connection)

    connection.close()
