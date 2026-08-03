import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.project_archive import ProjectArchiveService


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_index(archive: Path, sources: list[dict[str, object]]) -> None:
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "archive-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-08-03T09:00:00Z",
                "current_release": "0.74.0",
                "current_commit": "d00e35c66ebab1a0e9449f7cf0a4c55013f6e951",
                "migration_summary": "Authoritative NOVA records are local.",
                "sources": sources,
            }
        ),
        encoding="utf-8",
    )


def _source(path: Path, relative_path: str, source_id: str = "status") -> dict:
    return {
        "id": source_id,
        "label": "Current NOVA status",
        "category": "current_status",
        "authority": "verified_runtime",
        "relative_path": relative_path,
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "captured_at": "2026-08-03T09:00:00Z",
    }


def _application(tmp_path: Path):
    return create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            knowledge_path=tmp_path / "knowledge",
            archive_path=tmp_path / "archive",
            intake_scan_seconds=60,
        )
    )


def test_absent_index_returns_safe_empty_report(tmp_path: Path) -> None:
    report = ProjectArchiveService(tmp_path / "archive").report()

    assert report.source_count == 0
    assert report.current_release is None
    assert "has been created" in report.migration_summary
    assert not (tmp_path / "archive").exists()


def test_verified_source_and_plain_text_document(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "Current" / "NOVA-Current-Status.md"
    document.parent.mkdir(parents=True)
    document.write_text("# NOVA\n\nRelease 0.74.0\n", encoding="utf-8")
    _write_index(archive, [_source(document, "Current/NOVA-Current-Status.md")])

    service = ProjectArchiveService(archive)
    report = service.report()
    preview = service.document("status")

    assert report.verified_count == 1
    assert report.sources[0].preview_available is True
    assert preview.content.startswith("# NOVA")
    assert preview.truncated is False


def test_changed_source_is_not_previewed(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "status.md"
    archive.mkdir()
    document.write_text("original", encoding="utf-8")
    _write_index(archive, [_source(document, "status.md")])
    document.write_text("changed", encoding="utf-8")

    report = ProjectArchiveService(archive).report()

    assert report.changed_count == 1
    assert report.sources[0].preview_available is False


def test_missing_and_invalid_sources_do_not_hide_valid_source(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "valid.txt"
    archive.mkdir()
    document.write_text("valid", encoding="utf-8")
    valid = _source(document, "valid.txt", "valid")
    missing = dict(valid, id="missing", relative_path="missing.txt")
    traversal = dict(valid, id="escape", relative_path="../outside.txt")
    _write_index(archive, [missing, traversal, valid, {"id": "broken"}])

    report = ProjectArchiveService(archive).report()

    assert report.source_count == 3
    assert report.verified_count == 1
    assert report.missing_count == 1
    assert report.invalid_count == 2
    assert len(report.warnings) == 1


def test_duplicate_source_ids_are_isolated(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "status.txt"
    archive.mkdir()
    document.write_text("status", encoding="utf-8")
    source = _source(document, "status.txt")
    _write_index(archive, [source, source])

    report = ProjectArchiveService(archive).report()

    assert report.source_count == 1
    assert report.invalid_count == 1
    assert "Duplicate source id" in report.warnings[0]


def test_preview_is_bounded(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "long.txt"
    archive.mkdir()
    document.write_text("abcdefghij", encoding="utf-8")
    _write_index(archive, [_source(document, "long.txt")])

    preview = ProjectArchiveService(
        archive, max_preview_characters=4
    ).document("status")

    assert preview.content == "abcd"
    assert preview.truncated is True


def test_api_returns_report_and_rejects_unverified_document(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "status.md"
    archive.mkdir()
    document.write_text("original", encoding="utf-8")
    _write_index(archive, [_source(document, "status.md")])
    document.write_text("changed", encoding="utf-8")

    with TestClient(_application(tmp_path)) as client:
        report = client.get("/api/v1/project-archive")
        preview = client.get("/api/v1/project-archive/sources/status")

    assert report.status_code == 200
    assert report.json()["changed_count"] == 1
    assert preview.status_code == 409
    assert "checksum is not verified" in preview.json()["detail"]


def test_report_timestamps_are_timezone_aware(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    document = archive / "status.md"
    archive.mkdir()
    document.write_text("status", encoding="utf-8")
    _write_index(archive, [_source(document, "status.md")])

    report = ProjectArchiveService(archive).report()

    assert report.generated_at.tzinfo == UTC
    assert report.index_generated_at == datetime(2026, 8, 3, 9, tzinfo=UTC)
