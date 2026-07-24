import hashlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.schemas.intake import IntakeFile, IntakeScanResult, IntakeStatus


class IntakeService:
    def __init__(self, intake_path: Path, database_path: Path) -> None:
        self.intake_path = intake_path
        self.database_path = database_path
        self._lock = Lock()

    def initialize(self) -> None:
        self.intake_path.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    version INTEGER NOT NULL
                );
                INSERT INTO schema_meta (version)
                SELECT 1
                WHERE NOT EXISTS (SELECT 1 FROM schema_meta);

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
                );

                CREATE INDEX IF NOT EXISTS ix_intake_files_sha256
                ON intake_files (sha256);
                """
            )

    def scan(self) -> IntakeScanResult:
        scanned = added = updated = 0
        with self._lock, self._connection() as connection:
            for path in sorted(self.intake_path.rglob("*")):
                if not path.is_file():
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue

                scanned += 1
                relative_path = path.relative_to(self.intake_path).as_posix()
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
            duplicates = self._reconcile_duplicates(connection)

        return IntakeScanResult(
            scanned=scanned,
            added=added,
            updated=updated,
            duplicates=duplicates,
        )

    def list_files(self) -> list[IntakeFile]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, relative_path, original_name, extension, size_bytes,
                       modified_at, observed_at, sha256, status, duplicate_of
                FROM intake_files
                ORDER BY observed_at DESC, relative_path
                """
            ).fetchall()
        return [IntakeFile.model_validate(dict(row)) for row in rows]

    def _reconcile_duplicates(self, connection: sqlite3.Connection) -> int:
        canonical_by_hash: dict[str, str] = {}
        duplicates = 0
        rows = connection.execute(
            """
            SELECT id, sha256
            FROM intake_files
            ORDER BY observed_at, id
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
