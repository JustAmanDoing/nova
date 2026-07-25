import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import LOCAL_ACTION_HEADER, LOCAL_ACTION_VALUE
from app.core.config import Settings
from app.main import create_app
from app.services.backup import BackupError, BackupService, RestoreError
from app.services.intake import IntakeService

LOCAL_ACTION_HEADERS = {LOCAL_ACTION_HEADER: LOCAL_ACTION_VALUE}


def test_backup_service_creates_and_lists_verified_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    intake = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=database_path,
    )
    intake.initialize()
    (intake.intake_path / "note.txt").write_text(
        "Nova backup test",
        encoding="utf-8",
    )
    intake.scan()
    backups = BackupService(database_path, tmp_path / "backups")
    backups.initialize()

    created = backups.create_backup()
    listed = backups.list_backups()
    backup_path = backups.get_backup_path(created.filename)

    assert created.verified is True
    assert created.sha256 is not None
    assert len(created.sha256) == 64
    assert created.size_bytes > 0
    assert listed == [created]
    assert backup_path.is_file()
    assert backup_path.with_suffix(".db.sha256").is_file()
    with sqlite3.connect(backup_path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("SELECT COUNT(*) FROM intake_files").fetchone() == (1,)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM intake_files").fetchone() == (1,)


def test_backup_service_refuses_missing_database_and_unsafe_names(
    tmp_path: Path,
) -> None:
    backups = BackupService(tmp_path / "missing.db", tmp_path / "backups")
    backups.initialize()

    with pytest.raises(BackupError, match="not available"):
        backups.create_backup()
    with pytest.raises(LookupError, match="does not exist"):
        backups.get_backup_path("../nova.db")


def test_backup_list_marks_missing_checksum_as_unverified(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
    backups = BackupService(database_path, tmp_path / "backups")
    backups.initialize()
    created = backups.create_backup()
    backups.get_backup_path(created.filename).with_suffix(".db.sha256").unlink()

    listed = backups.list_backups()

    assert listed[0].filename == created.filename
    assert listed[0].sha256 is None
    assert listed[0].verified is False


def test_backup_failure_removes_unpublished_temporary_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "nova.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
    backup_path = tmp_path / "backups"
    backups = BackupService(database_path, backup_path)
    backups.initialize()

    def fail_hash(_: Path) -> str:
        raise OSError("private storage detail")

    monkeypatch.setattr(backups, "_hash_file", fail_hash)

    with pytest.raises(BackupError, match="verified local database backup"):
        backups.create_backup()

    assert list(backup_path.iterdir()) == []


def test_backup_service_restores_verified_snapshot_with_safety_backup(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('before')")
        connection.commit()
    backups = BackupService(database_path, tmp_path / "backups")
    backups.initialize()
    restore_source = backups.create_backup()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("INSERT INTO sample VALUES ('after')")
        connection.commit()

    restored = backups.restore_backup(
        restore_source.filename,
        f"RESTORE {restore_source.filename}",
    )

    assert restored.restored_from == restore_source.filename
    assert restored.restored_from_sha256 == restore_source.sha256
    assert restored.safety_backup.filename != restore_source.filename
    assert restored.safety_backup.verified is True
    with closing(sqlite3.connect(database_path)) as connection:
        assert connection.execute("SELECT value FROM sample").fetchall() == [
            ("before",),
        ]
    with closing(
        sqlite3.connect(backups.get_backup_path(restored.safety_backup.filename))
    ) as connection:
        assert connection.execute("SELECT value FROM sample").fetchall() == [
            ("before",),
            ("after",),
        ]
    audit = (backups.backup_path / "restore-audit.jsonl").read_text(
        encoding="utf-8"
    )
    assert '"event": "restore_succeeded"' in audit
    assert restore_source.filename in audit


def test_backup_service_requires_exact_restore_confirmation(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('current')")
        connection.commit()
    backups = BackupService(database_path, tmp_path / "backups")
    backups.initialize()
    restore_source = backups.create_backup()

    with pytest.raises(RestoreError, match="Confirmation must exactly match"):
        backups.restore_backup(restore_source.filename, "restore")

    assert len(backups.list_backups()) == 1
    with closing(sqlite3.connect(database_path)) as connection:
        assert connection.execute("SELECT value FROM sample").fetchall() == [
            ("current",),
        ]


def test_backup_service_refuses_tampered_restore_source(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('before')")
        connection.commit()
    backups = BackupService(database_path, tmp_path / "backups")
    backups.initialize()
    restore_source = backups.create_backup()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("INSERT INTO sample VALUES ('current')")
        connection.commit()
    with backups.get_backup_path(restore_source.filename).open("ab") as backup:
        backup.write(b"tampered")

    with pytest.raises(RestoreError, match="no longer matches"):
        backups.restore_backup(
            restore_source.filename,
            f"RESTORE {restore_source.filename}",
        )

    assert len(backups.list_backups()) == 1
    with closing(sqlite3.connect(database_path)) as connection:
        assert connection.execute("SELECT value FROM sample").fetchall() == [
            ("before",),
            ("current",),
        ]


def test_backup_service_rolls_back_when_post_restore_validation_fails(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('before')")
        connection.commit()
    initial = BackupService(database_path, tmp_path / "backups")
    initial.initialize()
    restore_source = initial.create_backup()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("INSERT INTO sample VALUES ('current')")
        connection.commit()

    def fail_validation() -> None:
        raise RuntimeError("private validation detail")

    backups = BackupService(
        database_path,
        tmp_path / "backups",
        post_restore=fail_validation,
    )

    with pytest.raises(RestoreError, match="safety snapshot"):
        backups.restore_backup(
            restore_source.filename,
            f"RESTORE {restore_source.filename}",
        )

    with closing(sqlite3.connect(database_path)) as connection:
        assert connection.execute("SELECT value FROM sample").fetchall() == [
            ("before",),
            ("current",),
        ]
    audit = (backups.backup_path / "restore-audit.jsonl").read_text(
        encoding="utf-8"
    )
    assert '"event": "restore_failed_rolled_back"' in audit
    assert "private validation detail" not in audit


def test_backup_api_creates_lists_and_downloads_snapshot(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application, headers=LOCAL_ACTION_HEADERS) as client:
        create_response = client.post("/api/v1/backups")
        list_response = client.get("/api/v1/backups")
        filename = create_response.json()["filename"]
        download_response = client.get(f"/api/v1/backups/{filename}")
        missing_response = client.get("/api/v1/backups/not-a-backup.db")

    assert create_response.status_code == 201
    assert create_response.json()["verified"] is True
    assert list_response.status_code == 200
    assert list_response.json()[0]["filename"] == filename
    assert download_response.status_code == 200
    assert download_response.content.startswith(b"SQLite format 3")
    assert missing_response.status_code == 404


def test_backup_api_restores_only_after_exact_confirmation(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application, headers=LOCAL_ACTION_HEADERS) as client:
        with closing(sqlite3.connect(tmp_path / "nova.db")) as connection:
            connection.execute("CREATE TABLE restore_probe (value TEXT)")
            connection.execute("INSERT INTO restore_probe VALUES ('before')")
            connection.commit()
        created = client.post("/api/v1/backups").json()
        filename = created["filename"]
        with closing(sqlite3.connect(tmp_path / "nova.db")) as connection:
            connection.execute("INSERT INTO restore_probe VALUES ('after')")
            connection.commit()

        rejected = client.post(
            f"/api/v1/backups/{filename}/restore",
            json={"confirmation": "RESTORE wrong-file.db"},
        )
        restored = client.post(
            f"/api/v1/backups/{filename}/restore",
            json={"confirmation": f"RESTORE {filename}"},
        )

    assert rejected.status_code == 409
    assert restored.status_code == 200
    assert restored.json()["restored_from"] == filename
    assert restored.json()["safety_backup"]["verified"] is True
    with closing(sqlite3.connect(tmp_path / "nova.db")) as connection:
        assert connection.execute("SELECT value FROM restore_probe").fetchall() == [
            ("before",),
        ]


def test_backup_api_returns_safe_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = create_app(
        Settings(
            intake_path=tmp_path / "intake",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application, headers=LOCAL_ACTION_HEADERS) as client:
        def fail_backup() -> None:
            raise BackupError("The backup destination is unavailable.")

        monkeypatch.setattr(application.state.backups, "create_backup", fail_backup)
        response = client.post("/api/v1/backups")

    assert response.status_code == 503
    assert response.json() == {"detail": "The backup destination is unavailable."}
