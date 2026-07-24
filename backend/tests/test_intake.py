import asyncio
import sqlite3
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app, watch_intake
from app.schemas.intake import (
    ApprovalAction,
    ApprovalRequest,
    ApprovalStatus,
    UnderstandingStatus,
)
from app.services import understanding as understanding_service
from app.services.intake import ActionConflict, IntakeService


def make_service(tmp_path: Path) -> IntakeService:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
    )
    service.initialize()
    return service


def write_invoice(path: Path, supplier: str = "Example Office Supplies") -> str:
    content = (
        "NOVA TEST DOCUMENT\n"
        "Document type: Invoice\n"
        "Invoice number: TEST-2026-001\n"
        "Invoice date: 24-07-2026\n"
        f"Supplier: {supplier}\n"
        "Total: $35.15 AUD"
    )
    path.write_text(content, encoding="utf-8")
    return content


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
    content = (
        "Invoice\n"
        "Invoice number: INV-001\n"
        "Invoice date: 24-07-2026\n"
        "Supplier: Example Office\n"
        "Total: $35.15 AUD"
    )
    first.write_text(content, encoding="utf-8")
    second.write_text(content, encoding="utf-8")
    service.scan()
    initial_records = {
        record.original_name: record for record in service.list_files()
    }

    assert initial_records["second.txt"].recommendation is not None
    assert initial_records["second.txt"].recommendation.outcome == "insufficient_evidence"

    first.unlink()
    result = service.scan()
    records = service.list_files()

    assert result.removed == 1
    assert result.duplicates == 0
    assert [record.original_name for record in records] == ["second.txt"]
    assert records[0].status == "observed"
    assert records[0].duplicate_of is None
    assert records[0].recommendation is not None
    assert records[0].recommendation.outcome == "suggested"


def test_invoice_gets_an_explainable_deterministic_recommendation(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    content = write_invoice(source)

    service.scan()
    record = service.list_files()[0]

    assert source.read_text(encoding="utf-8") == content
    assert record.recommendation is not None
    assert record.recommendation.outcome == "suggested"
    assert record.recommendation.category == "Financial"
    assert (
        record.recommendation.suggested_filename
        == "24-07-2026_Financial_Invoice_Example-Office-Supplies_v01.txt"
    )
    assert record.recommendation.destination == "Financial/Invoices"
    assert record.recommendation.confidence == 0.96
    assert record.recommendation.reasons[-1] == (
        "No file will change until a later approval step."
    )


def test_recommendation_can_be_edited_and_approved_without_changing_file(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    content = write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id

    edited = service.review_recommendation(
        file_id,
        ApprovalRequest(
            action=ApprovalAction.edit,
            category="Financial",
            suggested_filename="24-07-2026_Financial_Invoice_Office_v02.txt",
            destination="Financial/Invoices/2026",
        ),
    )
    approved = service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )
    record = service.list_files(approval_status=ApprovalStatus.approved)[0]

    assert edited.status == "pending"
    assert approved.status == "approved"
    assert approved.suggested_filename == edited.suggested_filename
    assert approved.destination == "Financial/Invoices/2026"
    assert record.approval == approved
    assert service.summary().ready_for_review == 0
    assert source.read_text(encoding="utf-8") == content


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (ApprovalAction.reject, ApprovalStatus.rejected),
        (ApprovalAction.ignore, ApprovalStatus.ignored),
    ],
)
def test_recommendation_can_be_rejected_or_ignored(
    tmp_path: Path,
    action: ApprovalAction,
    expected: ApprovalStatus,
) -> None:
    service = make_service(tmp_path)
    write_invoice(service.intake_path / "invoice.txt")
    service.scan()
    file_id = service.list_files()[0].id

    result = service.review_recommendation(
        file_id,
        ApprovalRequest(action=action),
    )

    assert result.status == expected
    assert service.list_files(approval_status=expected)[0].approval == result
    assert service.summary().ready_for_review == 0


def test_changed_recommendation_returns_to_the_review_queue(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id
    service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )

    write_invoice(source, supplier="A Different and Longer Supplier Name")
    service.scan()
    record = service.list_files()[0]

    assert record.approval is None
    assert record.recommendation is not None
    assert record.recommendation.outcome == "suggested"
    assert service.summary().ready_for_review == 1


def test_approved_recommendation_moves_without_overwriting_and_can_be_undone(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    content = write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id
    approval = service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )

    moved = service.execute_approved(file_id)
    filed = service.library_path / approval.destination / approval.suggested_filename

    assert moved.kind == "move"
    assert moved.status == "succeeded"
    assert moved.can_undo is True
    assert not source.exists()
    assert filed.read_text(encoding="utf-8") == content
    assert service.list_files() == []
    assert service.list_actions()[0] == moved

    restored = service.undo_action(moved.operation_id)
    actions = service.list_actions()

    assert restored.kind == "undo"
    assert restored.status == "succeeded"
    assert source.read_text(encoding="utf-8") == content
    assert not filed.exists()
    assert len(service.list_files()) == 1
    assert actions[0].operation_id == restored.operation_id
    assert actions[1].operation_id == moved.operation_id
    assert actions[1].can_undo is False

    with sqlite3.connect(service.database_path) as connection:
        events = connection.execute(
            """
            SELECT kind, status
            FROM action_events
            ORDER BY rowid
            """
        ).fetchall()
    assert events == [
        ("move", "started"),
        ("move", "succeeded"),
        ("undo", "started"),
        ("undo", "succeeded"),
    ]


def test_execution_refuses_unapproved_changed_and_existing_destinations(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id

    with pytest.raises(ActionConflict, match="current approved recommendation"):
        service.execute_approved(file_id)

    service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )
    source.write_text("changed after approval", encoding="utf-8")
    with pytest.raises(ActionConflict, match="changed after review"):
        service.execute_approved(file_id)
    assert source.read_text(encoding="utf-8") == "changed after approval"

    write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id
    approval = service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )
    existing = service.library_path / approval.destination / approval.suggested_filename
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("keep me", encoding="utf-8")

    with pytest.raises(ActionConflict, match="will not overwrite"):
        service.execute_approved(file_id)
    assert source.exists()
    assert existing.read_text(encoding="utf-8") == "keep me"


def test_undo_refuses_changed_library_file_and_occupied_intake_path(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id
    approval = service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )
    moved = service.execute_approved(file_id)
    filed = service.library_path / approval.destination / approval.suggested_filename

    filed.write_text("changed after filing", encoding="utf-8")
    with pytest.raises(ActionConflict, match="changed after execution"):
        service.undo_action(moved.operation_id)

    write_invoice(filed)
    source.write_text("occupied", encoding="utf-8")
    with pytest.raises(ActionConflict, match="will not overwrite"):
        service.undo_action(moved.operation_id)
    assert source.read_text(encoding="utf-8") == "occupied"


def test_failed_move_is_journaled_without_removing_the_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    content = write_invoice(source)
    service.scan()
    file_id = service.list_files()[0].id
    service.review_recommendation(
        file_id,
        ApprovalRequest(action=ApprovalAction.approve),
    )

    def fail_move(_source: Path, _destination: Path, _sha256: str) -> None:
        raise OSError("private filesystem detail")

    monkeypatch.setattr(service, "_perform_verified_move", fail_move)

    with pytest.raises(ActionConflict, match="filesystem operation failed"):
        service.execute_approved(file_id)

    action = service.list_actions()[0]
    assert action.status == "failed"
    assert "private filesystem detail" not in action.detail
    assert source.read_text(encoding="utf-8") == content

    with sqlite3.connect(service.database_path) as connection:
        statuses = connection.execute(
            "SELECT status FROM action_events ORDER BY rowid"
        ).fetchall()
    assert statuses == [("started",), ("failed",)]


def test_review_rejects_missing_recommendations_and_unsafe_edits(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    (service.intake_path / "note.txt").write_text("Buy milk", encoding="utf-8")
    service.scan()
    file_id = service.list_files()[0].id

    with pytest.raises(LookupError, match="No current recommendation"):
        service.review_recommendation(
            file_id,
            ApprovalRequest(action=ApprovalAction.approve),
        )

    write_invoice(service.intake_path / "invoice.txt")
    service.scan()
    invoice_id = next(
        record.id
        for record in service.list_files()
        if record.original_name == "invoice.txt"
    )
    with pytest.raises(ValueError, match="unsafe characters"):
        service.review_recommendation(
            invoice_id,
            ApprovalRequest(
                action=ApprovalAction.edit,
                category="Financial",
                suggested_filename="../escape.txt",
                destination="Financial/Invoices",
            ),
        )
    with pytest.raises(ValueError, match="unsafe characters"):
        service.review_recommendation(
            invoice_id,
            ApprovalRequest(
                action=ApprovalAction.edit,
                category="Financial",
                suggested_filename="CON.txt",
                destination="Financial/Invoices",
            ),
        )


def test_project_rule_and_insufficient_evidence_outcomes(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    (service.intake_path / "project.md").write_text(
        "# Nova Project\n\nMilestone roadmap for the local assistant.",
        encoding="utf-8",
    )
    (service.intake_path / "note.txt").write_text(
        "Remember to buy milk.",
        encoding="utf-8",
    )

    service.scan()
    records = {record.original_name: record for record in service.list_files()}

    project = records["project.md"].recommendation
    assert project is not None
    assert project.outcome == "suggested"
    assert project.category == "Project"
    assert project.destination == "Project"
    assert project.suggested_filename is not None
    assert project.suggested_filename.endswith(
        "_Project_Nova-Project_Local_v01.md"
    )

    note = records["note.txt"].recommendation
    assert note is not None
    assert note.outcome == "insufficient_evidence"
    assert note.category is None
    assert note.suggested_filename is None
    assert note.destination is None
    assert note.confidence == 0.0


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


def test_scan_backfills_search_data_from_an_older_understanding_record(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    source = service.intake_path / "invoice.txt"
    source.write_text(
        "NOVA TEST DOCUMENT\nInvoice number: TEST-2026-001",
        encoding="utf-8",
    )
    service.scan()

    with sqlite3.connect(service.database_path) as connection:
        connection.execute(
            """
            UPDATE understanding_results
            SET full_text = NULL, extraction_method = 'none'
            """
        )
        connection.execute(
            """
            UPDATE recommendation_results
            SET outcome = 'insufficient_evidence',
                category = NULL,
                suggested_filename = NULL,
                destination = NULL,
                confidence = 0,
                reasons = '["stale recommendation"]'
            """
        )

    assert service.list_files(query="TEST-2026-001") == []

    service.scan()
    records = service.list_files(query="TEST-2026-001")

    assert [record.original_name for record in records] == ["invoice.txt"]
    assert records[0].understanding is not None
    assert records[0].understanding.extraction_method == "utf-8"
    assert records[0].recommendation is not None
    assert records[0].recommendation.outcome == "suggested"


def test_search_covers_filename_full_text_evidence_and_filters(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    (service.intake_path / "invoice.txt").write_text(
        "Quarterly invoice\n"
        "Invoice number: INV-90210\n"
        "Supplier: Example Office\n"
        "Total: $42.00",
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
        for item in service.list_files(query="Financial/Invoices")
    ] == ["invoice.txt"]
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
        (intake_path / "note.md").write_text(
            "# Nova project\n\nMilestone 3 roadmap",
            encoding="utf-8",
        )

        scan_response = client.post("/api/v1/intake/scan")
        files_response = client.get("/api/v1/intake/files")
        summary_response = client.get("/api/v1/intake/summary")

    assert scan_response.status_code == 200
    assert scan_response.json()["added"] == 1
    assert files_response.status_code == 200
    assert files_response.json()[0]["original_name"] == "note.md"
    assert files_response.json()[0]["understanding"]["status"] == "ready"
    assert files_response.json()[0]["understanding"]["title"] == "Nova project"
    assert files_response.json()[0]["recommendation"]["outcome"] == "suggested"
    assert files_response.json()[0]["recommendation"]["category"] == "Project"
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


def test_intake_api_records_approval_without_executing_it(tmp_path: Path) -> None:
    intake_path = tmp_path / "intake"
    application = create_app(
        Settings(
            intake_path=intake_path,
            database_path=tmp_path / "nova.db",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application) as client:
        source = intake_path / "invoice.txt"
        content = write_invoice(source)
        client.post("/api/v1/intake/scan")
        file_id = client.get("/api/v1/intake/files").json()[0]["id"]

        response = client.put(
            f"/api/v1/intake/files/{file_id}/approval",
            json={"action": "approve"},
        )
        summary = client.get("/api/v1/intake/summary").json()

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["destination"] == "Financial/Invoices"
    assert summary["ready_for_review"] == 0
    assert source.read_text(encoding="utf-8") == content


def test_intake_api_executes_and_undoes_an_approved_move(tmp_path: Path) -> None:
    intake_path = tmp_path / "intake"
    library_path = tmp_path / "library"
    application = create_app(
        Settings(
            intake_path=intake_path,
            library_path=library_path,
            database_path=tmp_path / "nova.db",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application) as client:
        source = intake_path / "invoice.txt"
        content = write_invoice(source)
        client.post("/api/v1/intake/scan")
        file_id = client.get("/api/v1/intake/files").json()[0]["id"]
        approval = client.put(
            f"/api/v1/intake/files/{file_id}/approval",
            json={"action": "approve"},
        ).json()

        execute_response = client.post(
            f"/api/v1/intake/files/{file_id}/execute"
        )
        operation = execute_response.json()
        actions_response = client.get("/api/v1/intake/actions")
        undo_response = client.post(
            f"/api/v1/intake/actions/{operation['operation_id']}/undo"
        )

    filed = library_path / approval["destination"] / approval["suggested_filename"]
    assert execute_response.status_code == 200
    assert operation["status"] == "succeeded"
    assert actions_response.status_code == 200
    assert actions_response.json()[0]["can_undo"] is True
    assert undo_response.status_code == 200
    assert undo_response.json()["kind"] == "undo"
    assert source.read_text(encoding="utf-8") == content
    assert not filed.exists()


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
