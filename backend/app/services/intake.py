import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.schemas.intake import (
    IntakeFile,
    IntakeScanResult,
    IntakeStatus,
    IntakeSummary,
    RecommendationRecord,
    UnderstandingRecord,
    UnderstandingStatus,
)
from app.services.recommendation import RULES_VERSION, recommend_file
from app.services.understanding import understand_file


class IntakeService:
    def __init__(
        self,
        intake_path: Path,
        database_path: Path,
        max_text_bytes: int = 1_000_000,
        max_extracted_text_bytes: int = 1_000_000,
    ) -> None:
        self.intake_path = intake_path
        self.database_path = database_path
        self.max_text_bytes = max_text_bytes
        self.max_extracted_text_bytes = max_extracted_text_bytes
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
                );

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
                );

                UPDATE schema_meta SET version = 4;
                """
            )
            self._add_column_if_missing(connection, "understanding_results", "error_code TEXT")
            self._add_column_if_missing(
                connection,
                "understanding_results",
                "extraction_method TEXT NOT NULL DEFAULT 'none'",
            )
            self._add_column_if_missing(
                connection,
                "understanding_results",
                "retryable INTEGER NOT NULL DEFAULT 0",
            )
            self._add_column_if_missing(connection, "understanding_results", "full_text TEXT")
            self._add_column_if_missing(
                connection,
                "recommendation_results",
                "source_status TEXT NOT NULL DEFAULT 'observed'",
            )
            self._add_column_if_missing(
                connection,
                "recommendation_results",
                "source_understood_at TEXT",
            )

    def scan(self) -> IntakeScanResult:
        scanned = added = updated = 0
        seen_paths: set[str] = set()
        intake_root = self.intake_path.resolve()
        with self._lock, self._connection() as connection:
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
                    ), 0) AS ready_for_review,
                    COALESCE(SUM(files.status = 'duplicate'), 0) AS exact_duplicates
                FROM intake_files AS files
                LEFT JOIN understanding_results AS understanding
                  ON understanding.file_id = files.id
                LEFT JOIN recommendation_results AS recommendation
                  ON recommendation.file_id = files.id
                """
            ).fetchone()
        return IntakeSummary(
            files_observed=row["files_observed"],
            understood=row["understood"],
            ready_for_review=row["ready_for_review"],
            exact_duplicates=row["exact_duplicates"],
        )

    def list_files(
        self,
        query: str | None = None,
        status: IntakeStatus | None = None,
        understanding_status: UnderstandingStatus | None = None,
        extension: str | None = None,
        document_type: str | None = None,
    ) -> list[IntakeFile]:
        clauses: list[str] = []
        parameters: list[str] = []
        if query and (term := query.strip()):
            clauses.append(
                """(
                    files.original_name LIKE ? ESCAPE '\\'
                    OR files.relative_path LIKE ? ESCAPE '\\'
                    OR understanding.title LIKE ? ESCAPE '\\'
                    OR understanding.full_text LIKE ? ESCAPE '\\'
                    OR understanding.evidence LIKE ? ESCAPE '\\'
                    OR understanding.error LIKE ? ESCAPE '\\'
                    OR recommendation.category LIKE ? ESCAPE '\\'
                    OR recommendation.suggested_filename LIKE ? ESCAPE '\\'
                    OR recommendation.destination LIKE ? ESCAPE '\\'
                    OR recommendation.reasons LIKE ? ESCAPE '\\'
                )"""
            )
            pattern = f"%{self._escape_like(term)}%"
            parameters.extend([pattern] * 10)
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
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
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
                       recommendation.generated_at
                FROM intake_files AS files
                LEFT JOIN understanding_results AS understanding
                  ON understanding.file_id = files.id
                LEFT JOIN recommendation_results AS recommendation
                  ON recommendation.file_id = files.id
                {where}
                ORDER BY observed_at DESC, relative_path
                """,
                parameters,
            ).fetchall()
        return [self._intake_file_from_row(row) for row in rows]

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
            if is_current and has_complete_result:
                continue
            result = understand_file(
                self.intake_path / row["relative_path"],
                row["extension"],
                self.max_text_bytes,
                self.max_extracted_text_bytes,
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
                   understanding.title, understanding.full_text,
                   understanding.understood_at AS understanding_understood_at,
                   recommendation.source_sha256,
                   recommendation.source_status,
                   recommendation.source_understood_at,
                   recommendation.rules_version
            FROM intake_files AS files
            LEFT JOIN understanding_results AS understanding
              ON understanding.file_id = files.id
            LEFT JOIN recommendation_results AS recommendation
              ON recommendation.file_id = files.id
            """
        ).fetchall()
        for row in rows:
            if (
                row["source_sha256"] == row["sha256"]
                and row["source_status"] == row["status"]
                and row["source_understood_at"] == row["understanding_understood_at"]
                and row["rules_version"] == RULES_VERSION
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
            connection.execute(
                """
                INSERT INTO recommendation_results (
                    file_id, source_sha256, source_status, source_understood_at,
                    rules_version, outcome, category, suggested_filename,
                    destination, confidence, reasons, generated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    source_sha256 = excluded.source_sha256,
                    source_status = excluded.source_status,
                    source_understood_at = excluded.source_understood_at,
                    rules_version = excluded.rules_version,
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
        )

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
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def _add_column_if_missing(
        connection: sqlite3.Connection,
        table: str,
        definition: str,
    ) -> None:
        column = definition.split()[0]
        columns = {
            row["name"] for row in connection.execute(f"PRAGMA table_info({table})")
        }
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

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
