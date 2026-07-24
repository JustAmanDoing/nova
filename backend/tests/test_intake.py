import asyncio
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app, watch_intake
from app.schemas.intake import UnderstandingStatus
from app.services import understanding as understanding_service
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


def test_scan_removes_missing_records_and_promotes_remaining_duplicate(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    first = service.intake_path / "first.txt"
    second = service.intake_path / "second.txt"
    first.write_text("same content", encoding="utf-8")
    second.write_text("same content", encoding="utf-8")
    service.scan()

    first.unlink()
    result = service.scan()
    records = service.list_files()

    assert result.removed == 1
    assert result.duplicates == 0
    assert [record.original_name for record in records] == ["second.txt"]
    assert records[0].status == "observed"
    assert records[0].duplicate_of is None


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
    (service.intake_path / "scan.png").write_bytes(b"\x89PNG")
    (service.intake_path / "large.txt").write_text("too much text", encoding="utf-8")

    service.scan()
    records = {record.original_name: record for record in service.list_files()}

    assert records["scan.png"].understanding is not None
    assert records["scan.png"].understanding.status == "unsupported"
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


def test_search_covers_filename_full_text_evidence_and_filters(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    (service.intake_path / "invoice.txt").write_text(
        "Quarterly account\nSupplier: Example Office\nReference: INV-90210",
        encoding="utf-8",
    )
    (service.intake_path / "project.md").write_text(
        "# Nova roadmap\n\nPrivate assistant milestones",
        encoding="utf-8",
    )
    (service.intake_path / "scan.png").write_bytes(b"\x89PNG")
    service.scan()

    assert [item.original_name for item in service.list_files(query="INV-90210")] == [
        "invoice.txt"
    ]
    assert [item.original_name for item in service.list_files(query="project.md")] == [
        "project.md"
    ]
    assert [item.original_name for item in service.list_files(query="not supported")] == [
        "scan.png"
    ]
    assert [
        item.original_name
        for item in service.list_files(
            understanding_status=UnderstandingStatus.ready,
            extension="md",
            document_type="markdown",
        )
    ] == ["project.md"]


def test_failed_extraction_has_actionable_diagnostics(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    (service.intake_path / "invalid.txt").write_bytes(b"\xff\xfe\xfa")

    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.status == "failed"
    assert understanding.error_code == "invalid_utf8"
    assert understanding.extraction_method == "utf-8"
    assert understanding.retryable is False
    assert understanding.error == "The file could not be decoded as UTF-8 text."


def test_docx_text_is_extracted_and_searchable(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "brief.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Nova project brief</w:t></w:r></w:p>
        <w:p><w:r><w:t>Reference DOCX-482</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    service.scan()
    record = service.list_files(query="DOCX-482")[0]

    assert record.understanding is not None
    assert record.understanding.status == "ready"
    assert record.understanding.document_type == "word_document"
    assert record.understanding.title == "Nova project brief"
    assert record.understanding.extraction_method == "docx_xml"


def test_pdf_text_is_extracted_and_searchable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePage:
        def extract_text(self) -> str:
            return "PDF project report\nReference PDF-731"

    monkeypatch.setattr(
        understanding_service,
        "PdfReader",
        lambda _: SimpleNamespace(is_encrypted=False, pages=[FakePage()]),
    )
    service = make_service(tmp_path)
    (service.intake_path / "report.pdf").write_bytes(b"%PDF-test")

    service.scan()
    record = service.list_files(query="PDF-731")[0]

    assert record.understanding is not None
    assert record.understanding.status == "ready"
    assert record.understanding.document_type == "pdf"
    assert record.understanding.title == "PDF project report"
    assert record.understanding.extraction_method == "pypdf"


def test_extracted_content_limit_stops_document_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePage:
        def extract_text(self) -> str:
            return "expanded PDF text"

    monkeypatch.setattr(
        understanding_service,
        "PdfReader",
        lambda _: SimpleNamespace(is_encrypted=False, pages=[FakePage()]),
    )
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
        max_text_bytes=1_000,
        max_extracted_text_bytes=5,
    )
    service.initialize()
    (service.intake_path / "report.pdf").write_bytes(b"%PDF")

    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.status == "too_large"
    assert understanding.error_code == "extracted_text_too_large"
    assert understanding.extraction_method == "pypdf"


def test_unexpected_extractor_failure_is_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_reader(_: Path) -> None:
        raise RuntimeError("internal parser detail")

    monkeypatch.setattr(understanding_service, "PdfReader", fail_reader)
    service = make_service(tmp_path)
    (service.intake_path / "report.pdf").write_bytes(b"%PDF")

    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.status == "failed"
    assert understanding.error_code == "extractor_error"
    assert understanding.retryable is True
    assert understanding.error is not None
    assert "internal parser detail" not in understanding.error


def test_invalid_docx_has_structured_diagnostics(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    (service.intake_path / "broken.docx").write_bytes(b"not-a-zip")

    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.status == "failed"
    assert understanding.error_code == "invalid_docx"
    assert understanding.extraction_method == "docx_xml"
    assert understanding.retryable is False


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
        summary_response = client.get("/api/v1/intake/summary")

    assert scan_response.status_code == 200
    assert scan_response.json()["added"] == 1
    assert files_response.status_code == 200
    assert files_response.json()[0]["original_name"] == "note.md"
    assert files_response.json()[0]["understanding"]["status"] == "ready"
    assert files_response.json()[0]["understanding"]["title"] == "Nova"
    assert summary_response.status_code == 200
    assert summary_response.json() == {
        "files_observed": 1,
        "understood": 1,
        "ready_for_review": 1,
        "exact_duplicates": 0,
    }


def test_intake_api_searches_extracted_text_and_status(tmp_path: Path) -> None:
    intake_path = tmp_path / "intake"
    application = create_app(
        Settings(
            intake_path=intake_path,
            database_path=tmp_path / "nova.db",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application) as client:
        (intake_path / "notes.txt").write_text(
            "Internal reference ZX-418",
            encoding="utf-8",
        )
        client.post("/api/v1/intake/scan")
        response = client.get(
            "/api/v1/intake/files",
            params={"q": "ZX-418", "understanding_status": "ready"},
        )

    assert response.status_code == 200
    assert [item["original_name"] for item in response.json()] == ["notes.txt"]


def test_background_watcher_continues_after_scan_failure() -> None:
    class FlakyService:
        def __init__(self) -> None:
            self.calls = 0

        def scan(self) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary failure")

    async def exercise_watcher() -> int:
        service = FlakyService()
        task = asyncio.create_task(watch_intake(service, 0))  # type: ignore[arg-type]
        for _ in range(100):
            if service.calls >= 2:
                break
            await asyncio.sleep(0.001)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return service.calls

    assert asyncio.run(exercise_watcher()) >= 2
