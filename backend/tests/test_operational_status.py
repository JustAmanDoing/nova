from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services import intake as intake_module
from app.services.intake import IntakeService


def make_service(tmp_path: Path) -> IntakeService:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        library_path=tmp_path / "library",
        database_path=tmp_path / "nova.db",
    )
    service.initialize()
    return service


def test_operational_status_reports_successful_scan_and_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service(tmp_path)
    monkeypatch.setattr(
        intake_module.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(
            total=100 * 1024**3,
            used=50 * 1024**3,
            free=50 * 1024**3,
        ),
    )

    service.scan()
    status = service.operational_status()

    assert status.status == "healthy"
    assert status.uptime_seconds >= 0
    assert status.database_size_bytes is not None
    assert status.database_size_bytes > 0
    assert status.storage_total_bytes is not None
    assert status.storage_free_bytes is not None
    assert status.storage_free_percent is not None
    assert status.last_scan_status == "ok"
    assert status.last_scan_completed_at is not None
    assert status.last_scan_duration_ms is not None
    assert status.last_scan_duration_ms >= 0
    assert status.warnings == []


def test_operational_status_warns_after_failure_and_on_low_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service(tmp_path)

    def fail_scan():
        raise RuntimeError("private scan detail")

    monkeypatch.setattr(service, "_scan_once", fail_scan)
    monkeypatch.setattr(
        intake_module.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(
            total=100 * 1024**3,
            used=96 * 1024**3,
            free=4 * 1024**3,
        ),
    )

    with pytest.raises(RuntimeError, match="private scan detail"):
        service.scan()
    status = service.operational_status()

    assert status.status == "attention"
    assert status.last_scan_status == "failed"
    assert status.storage_free_bytes == 4 * 1024**3
    assert len(status.warnings) == 2
    assert "private scan detail" not in " ".join(status.warnings)
    assert any("storage" in warning.lower() for warning in status.warnings)
    assert any("scan failed" in warning.lower() for warning in status.warnings)


def test_operational_status_api_is_read_only(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application) as client:
        response = client.get("/api/v1/system/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "attention"}
    assert body["last_scan_status"] == "ok"
    assert isinstance(body["warnings"], list)
