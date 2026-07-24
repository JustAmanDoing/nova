from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.intake import IntakeService


def make_service(tmp_path: Path) -> IntakeService:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
    )
    service.initialize()
    return service


def test_scan_records_a_file_without_changing_it(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    source.write_text("Invoice 123", encoding="utf-8")

    result = service.scan()
    records = service.list_files()

    assert result.added == 1
    assert result.duplicates == 0
    assert source.read_text(encoding="utf-8") == "Invoice 123"
    assert records[0].original_name == "invoice.txt"
    assert records[0].status == "observed"
    assert len(records[0].sha256) == 64
    assert records[0].understanding is not None
    assert records[0].understanding.status == "ready"
    assert records[0].understanding.document_type == "plain_text"
    assert records[0].understanding.title == "Invoice 123"
    assert records[0].understanding.text_preview == "Invoice 123"


def test_scan_marks_exact_duplicate_and_ignores_unchanged_files(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    first = service.intake_path / "first.txt"
    second = service.intake_path / "second.txt"
    first.write_text("same content", encoding="utf-8")
    service.scan()
    second.write_text("same content", encoding="utf-8")

    result = service.scan()
    unchanged = service.scan()
    records = {record.original_name: record for record in service.list_files()}

    assert result.added == 1
    assert result.duplicates == 1
    assert unchanged.added == 0
    assert unchanged.updated == 0
    assert records["second.txt"].status == "duplicate"
    assert records["second.txt"].duplicate_of == records["first.txt"].id


def test_duplicate_status_is_reconciled_when_content_changes(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    first = service.intake_path / "first.txt"
    second = service.intake_path / "second.txt"
    first.write_text("same content", encoding="utf-8")
    second.write_text("same content", encoding="utf-8")
    service.scan()

    first.write_text("new content with a different size", encoding="utf-8")
    result = service.scan()
    records = service.list_files()

    assert result.updated == 1
    assert result.duplicates == 0
    assert all(record.status == "observed" for record in records)
    assert all(record.duplicate_of is None for record in records)


def test_markdown_understanding_uses_first_heading_as_title(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "project.md"
    content = "Intro text\n\n# Nova project\n\nA private local assistant."
    source.write_text(content, encoding="utf-8")

    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.status == "ready"
    assert understanding.document_type == "markdown"
    assert understanding.title == "Nova project"
    assert understanding.word_count == 8
    assert understanding.character_count == len(content)
    assert understanding.evidence == "Extracted locally from markdown content."


def test_unsupported_and_large_files_are_not_extracted(tmp_path: Path) -> None:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
        max_text_bytes=5,
    )
    service.initialize()
    (service.intake_path / "scan.pdf").write_bytes(b"%PDF")
    (service.intake_path / "large.txt").write_text("too much text", encoding="utf-8")

    service.scan()
    records = {record.original_name: record for record in service.list_files()}

    assert records["scan.pdf"].understanding is not None
    assert records["scan.pdf"].understanding.status == "unsupported"
    assert records["large.txt"].understanding is not None
    assert records["large.txt"].understanding.status == "too_large"


def test_understanding_refreshes_when_file_content_changes(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "note.txt"
    source.write_text("First title", encoding="utf-8")
    service.scan()

    source.write_text("A different and longer title", encoding="utf-8")
    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.title == "A different and longer title"


def test_intake_api_scans_and_lists_files(tmp_path: Path) -> None:
    intake_path = tmp_path / "intake"
    settings = Settings(
        intake_path=intake_path,
        database_path=tmp_path / "nova.db",
        intake_scan_seconds=60,
    )
    application = create_app(settings)

    with TestClient(application) as client:
        (intake_path / "note.md").write_text("# Nova", encoding="utf-8")

        scan_response = client.post("/api/v1/intake/scan")
        files_response = client.get("/api/v1/intake/files")

    assert scan_response.status_code == 200
    assert scan_response.json()["added"] == 1
    assert files_response.status_code == 200
    assert files_response.json()[0]["original_name"] == "note.md"
    assert files_response.json()[0]["understanding"]["status"] == "ready"
    assert files_response.json()[0]["understanding"]["title"] == "Nova"
