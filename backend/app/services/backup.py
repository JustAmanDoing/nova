import hashlib
import hmac
import json
import os
import re
import shutil
import sqlite3
from _thread import RLock
from collections.abc import Callable
from contextlib import closing, suppress
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.backup import BackupRecord, RestoreResult

BACKUP_NAME = re.compile(r"^nova-\d{8}T\d{6}\.\d{6}Z\.db$")


class BackupError(RuntimeError):
    """Raised when a consistent local backup cannot be created."""


class RestoreError(RuntimeError):
    """Raised when a backup cannot be restored safely."""


class BackupService:
    def __init__(
        self,
        database_path: Path,
        backup_path: Path,
        operation_lock: RLock | None = None,
        post_restore: Callable[[], object] | None = None,
    ) -> None:
        self.database_path = database_path
        self.backup_path = backup_path
        self._lock = operation_lock or RLock()
        self._post_restore = post_restore

    def initialize(self) -> None:
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> BackupRecord:
        with self._lock:
            return self._create_backup_locked()

    def restore_backup(self, filename: str, confirmation: str) -> RestoreResult:
        expected_confirmation = f"RESTORE {filename}"
        if not hmac.compare_digest(confirmation, expected_confirmation):
            raise RestoreError(
                f"Confirmation must exactly match: {expected_confirmation}"
            )

        with self._lock:
            backup_path = self.get_backup_path(filename)
            restored_from_sha256 = self._verify_restore_source(backup_path)
            safety_backup = self._create_backup_locked()
            replacement = self.database_path.parent / (
                f".nova-restore-{uuid4().hex}.tmp"
            )
            restored_at = datetime.now(UTC)
            database_replaced = False
            try:
                shutil.copyfile(backup_path, replacement)
                if not hmac.compare_digest(
                    self._hash_file(replacement),
                    restored_from_sha256,
                ):
                    raise RestoreError(
                        "The restore copy failed SHA-256 verification."
                    )
                os.replace(replacement, self.database_path)
                database_replaced = True
                if self._post_restore is not None:
                    self._post_restore()
                self._verify_sqlite(self.database_path)
                self._append_restore_event(
                    event="restore_succeeded",
                    restored_from=filename,
                    restored_from_sha256=restored_from_sha256,
                    safety_backup=safety_backup.filename,
                    occurred_at=restored_at,
                )
            except Exception as error:
                self._clean_temporary(replacement)
                if database_replaced:
                    try:
                        self._rollback_from_safety_backup(safety_backup)
                    except Exception as rollback_error:
                        raise RestoreError(
                            "Restore failed and automatic rollback also failed. "
                            "Stop Nova and preserve the data and backup folders."
                        ) from rollback_error
                    with suppress(OSError):
                        self._append_restore_event(
                            event="restore_failed_rolled_back",
                            restored_from=filename,
                            restored_from_sha256=restored_from_sha256,
                            safety_backup=safety_backup.filename,
                            occurred_at=datetime.now(UTC),
                        )
                if isinstance(error, RestoreError):
                    detail = str(error)
                else:
                    detail = "The restored database failed validation."
                outcome = (
                    "Nova restored the pre-restore safety snapshot."
                    if database_replaced
                    else "No database change was made."
                )
                raise RestoreError(
                    f"{detail} {outcome}"
                ) from error

        return RestoreResult(
            restored_from=filename,
            restored_from_sha256=restored_from_sha256,
            safety_backup=safety_backup,
            restored_at=restored_at,
            detail=(
                "Restored the verified database backup after creating a "
                "pre-restore safety snapshot."
            ),
        )

    def _create_backup_locked(self) -> BackupRecord:
        created_at = datetime.now(UTC)
        filename = f"nova-{created_at.strftime('%Y%m%dT%H%M%S.%fZ')}.db"
        final_path = self.backup_path / filename
        temporary_path = self.backup_path / f".{filename}.tmp"
        checksum_path = final_path.with_suffix(".db.sha256")
        temporary_checksum = checksum_path.with_suffix(".sha256.tmp")

        if not self.database_path.is_file():
            raise BackupError("Nova's database is not available for backup.")
        try:
            with (
                closing(
                    sqlite3.connect(
                        f"{self.database_path.resolve().as_uri()}?mode=ro",
                        uri=True,
                        timeout=30,
                    )
                ) as source,
                closing(
                    sqlite3.connect(temporary_path, timeout=30)
                ) as destination,
            ):
                source.backup(destination, pages=256, sleep=0.05)
                integrity = destination.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    raise BackupError(
                        "The backup failed SQLite integrity verification."
                    )
            checksum = self._hash_file(temporary_path)
            os.replace(temporary_path, final_path)
            temporary_checksum.write_text(
                f"{checksum}  {filename}\n",
                encoding="ascii",
            )
            os.replace(temporary_checksum, checksum_path)
        except BackupError:
            self._clean_temporary(
                temporary_path,
                temporary_checksum,
                final_path,
                checksum_path,
            )
            raise
        except (OSError, sqlite3.Error) as error:
            self._clean_temporary(
                temporary_path,
                temporary_checksum,
                final_path,
                checksum_path,
            )
            raise BackupError(
                "Nova could not create a verified local database backup."
            ) from error

        return self._record(final_path, checksum, verified=True)

    def list_backups(self) -> list[BackupRecord]:
        with self._lock:
            paths = sorted(
                (
                    path
                    for path in self.backup_path.glob("nova-*.db")
                    if path.is_file() and BACKUP_NAME.fullmatch(path.name)
                ),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            return [self._record(path, self._read_checksum(path)) for path in paths]

    def get_verified_backup_path(self, filename: str) -> Path:
        """Return a backup only after rechecking its checksum and SQLite integrity."""
        with self._lock:
            path = self.get_backup_path(filename)
            self._verify_restore_source(path)
            return path

    def get_verified_checksum_path(self, filename: str) -> Path:
        """Return the checksum sidecar only after rechecking the backup."""
        backup_path = self.get_verified_backup_path(filename)
        checksum_path = backup_path.with_suffix(".db.sha256")
        if not checksum_path.is_file():
            raise RestoreError(
                "The backup has no valid SHA-256 checksum and cannot be used."
            )
        return checksum_path

    def get_backup_path(self, filename: str) -> Path:
        if not BACKUP_NAME.fullmatch(filename):
            raise LookupError("That backup does not exist.")
        try:
            root = self.backup_path.resolve(strict=True)
            path = (self.backup_path / filename).resolve(strict=True)
        except OSError as error:
            raise LookupError("That backup does not exist.") from error
        if not path.is_relative_to(root) or not path.is_file():
            raise LookupError("That backup does not exist.")
        return path

    def _verify_restore_source(self, path: Path) -> str:
        expected = self._read_checksum(path)
        if expected is None:
            raise RestoreError(
                "The backup has no valid SHA-256 checksum and cannot be used."
            )
        try:
            current = self._hash_file(path)
        except OSError as error:
            raise RestoreError("The backup cannot be read.") from error
        if not hmac.compare_digest(current, expected):
            raise RestoreError(
                "The backup no longer matches its recorded SHA-256 checksum."
            )
        self._verify_sqlite(path)
        return current

    @staticmethod
    def _verify_sqlite(path: Path) -> None:
        try:
            with closing(
                sqlite3.connect(
                    f"{path.resolve().as_uri()}?mode=ro",
                    uri=True,
                    timeout=30,
                )
            ) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
        except (OSError, sqlite3.Error) as error:
            raise RestoreError(
                "The backup failed SQLite integrity verification."
            ) from error
        if integrity is None or integrity[0] != "ok":
            raise RestoreError("The backup failed SQLite integrity verification.")

    def _rollback_from_safety_backup(self, safety_backup: BackupRecord) -> None:
        safety_path = self.get_backup_path(safety_backup.filename)
        if safety_backup.sha256 is None:
            raise RestoreError("The safety backup checksum is unavailable.")
        rollback_path = self.database_path.parent / (
            f".nova-rollback-{uuid4().hex}.tmp"
        )
        try:
            shutil.copyfile(safety_path, rollback_path)
            if not hmac.compare_digest(
                self._hash_file(rollback_path),
                safety_backup.sha256,
            ):
                raise RestoreError("The safety backup copy failed verification.")
            os.replace(rollback_path, self.database_path)
            self._verify_sqlite(self.database_path)
        finally:
            self._clean_temporary(rollback_path)

    def _append_restore_event(
        self,
        *,
        event: str,
        restored_from: str,
        restored_from_sha256: str,
        safety_backup: str,
        occurred_at: datetime,
    ) -> None:
        entry = json.dumps(
            {
                "event": event,
                "restored_from": restored_from,
                "restored_from_sha256": restored_from_sha256,
                "safety_backup": safety_backup,
                "occurred_at": occurred_at.isoformat(),
            },
            sort_keys=True,
        )
        audit_path = self.backup_path / "restore-audit.jsonl"
        with audit_path.open("a", encoding="utf-8") as audit:
            audit.write(f"{entry}\n")
            audit.flush()
            os.fsync(audit.fileno())

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as backup:
            while chunk := backup.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _clean_temporary(*paths: Path) -> None:
        for path in paths:
            with suppress(OSError):
                path.unlink()

    @staticmethod
    def _record(
        path: Path,
        checksum: str | None,
        *,
        verified: bool = False,
    ) -> BackupRecord:
        stat = path.stat()
        return BackupRecord(
            filename=path.name,
            size_bytes=stat.st_size,
            sha256=checksum,
            created_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            checksum_recorded=checksum is not None,
            verified=verified,
        )

    @staticmethod
    def _read_checksum(path: Path) -> str | None:
        checksum_path = path.with_suffix(".db.sha256")
        try:
            lines = checksum_path.read_text(encoding="ascii").splitlines()
        except (OSError, UnicodeError):
            return None
        if len(lines) != 1:
            return None
        match = re.fullmatch(r"(?P<sha256>[0-9a-f]{64})  (?P<filename>.+)", lines[0])
        if match is not None and hmac.compare_digest(
            match.group("filename"),
            path.name,
        ):
            return match.group("sha256")
        return None
