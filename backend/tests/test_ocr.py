import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import understanding as understanding_service
from app.services.intake import IntakeService
from app.services.ocr import LocalOcrService, OcrError


class FakeOcr:
    def extract_image(self, _: Path, max_output_bytes: int) -> str:
        assert max_output_bytes == 1_000_000
        return "Scanned vehicle receipt\nReference OCR-417"

    def extract_pdf(
        self,
        _: Path,
        page_count: int,
        max_output_bytes: int,
    ) -> str:
        assert page_count == 2
        assert max_output_bytes == 1_000_000
        return "Scanned project report\nReference OCR-PDF-82"


class FailingOcr:
    def extract_image(self, _: Path, __: int) -> str:
        raise OcrError(
            "The local OCR process could not read this document.",
            "ocr_process_error",
            retryable=True,
        )

    def extract_pdf(self, _: Path, __: int, ___: int) -> str:
        raise AssertionError("PDF OCR was not expected")


def test_image_ocr_is_indexed_and_searchable(tmp_path: Path) -> None:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
        ocr_engine=FakeOcr(),
    )
    service.initialize()
    (service.intake_path / "receipt.png").write_bytes(b"\x89PNG\r\n")

    service.scan()
    record = service.list_files(query="OCR-417")[0]

    assert record.understanding is not None
    assert record.understanding.status == "ready"
    assert record.understanding.document_type == "image"
    assert record.understanding.title == "Scanned vehicle receipt"
    assert record.understanding.extraction_method == "tesseract"


def test_existing_unsupported_image_is_refreshed_when_ocr_becomes_available(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    without_ocr = IntakeService(tmp_path / "intake", database_path)
    without_ocr.initialize()
    (without_ocr.intake_path / "receipt.png").write_bytes(b"\x89PNG\r\n")
    without_ocr.scan()
    initial = without_ocr.list_files()[0]
    assert initial.understanding is not None
    assert initial.understanding.status == "unsupported"

    with_ocr = IntakeService(
        tmp_path / "intake",
        database_path,
        ocr_engine=FakeOcr(),
    )
    with_ocr.initialize()
    with_ocr.scan()
    refreshed = with_ocr.list_files()[0]

    assert refreshed.understanding is not None
    assert refreshed.understanding.status == "ready"
    assert refreshed.understanding.extraction_method == "tesseract"


def test_scanned_pdf_uses_ocr_only_when_text_layer_is_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class EmptyPage:
        def extract_text(self) -> str:
            return ""

    monkeypatch.setattr(
        understanding_service,
        "PdfReader",
        lambda _: SimpleNamespace(
            is_encrypted=False,
            pages=[EmptyPage(), EmptyPage()],
        ),
    )
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
        ocr_engine=FakeOcr(),
    )
    service.initialize()
    (service.intake_path / "scan.pdf").write_bytes(b"%PDF-scan")

    service.scan()
    record = service.list_files(query="OCR-PDF-82")[0]

    assert record.understanding is not None
    assert record.understanding.status == "ready"
    assert record.understanding.document_type == "pdf"
    assert record.understanding.extraction_method == "pypdf+tesseract"


def test_ocr_failure_is_structured_without_process_details(tmp_path: Path) -> None:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        database_path=tmp_path / "nova.db",
        ocr_engine=FailingOcr(),
    )
    service.initialize()
    (service.intake_path / "broken.jpg").write_bytes(b"not-an-image")

    service.scan()
    understanding = service.list_files()[0].understanding

    assert understanding is not None
    assert understanding.status == "failed"
    assert understanding.error_code == "ocr_process_error"
    assert understanding.extraction_method == "tesseract"
    assert understanding.retryable is True


def test_local_ocr_requires_tools_and_enforces_page_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"image")
    service = LocalOcrService(max_pages=2)
    monkeypatch.setattr(shutil, "which", lambda _: None)

    with pytest.raises(OcrError, match="required tool") as unavailable:
        service.extract_image(image, 1_000)
    with pytest.raises(OcrError, match="limited to 2 pages") as page_limit:
        service.extract_pdf(tmp_path / "scan.pdf", 3, 1_000)

    assert unavailable.value.code == "ocr_unavailable"
    assert unavailable.value.retryable is True
    assert page_limit.value.code == "ocr_page_limit"
    assert page_limit.value.retryable is False


def test_local_image_ocr_uses_argument_list_and_bounds_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"image")
    observed_command: list[str] = []

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        check: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[bytes]:
        observed_command.extend(command)
        assert capture_output is True
        assert check is False
        assert timeout == 5
        return subprocess.CompletedProcess(command, 0, stdout=b"hello", stderr=b"")

    monkeypatch.setattr(shutil, "which", lambda name: f"/tools/{name}")
    monkeypatch.setattr(subprocess, "run", fake_run)
    service = LocalOcrService(timeout_seconds=5)

    assert service.extract_image(image, 5) == "hello"
    assert observed_command[:3] == ["/tools/tesseract", str(image), "stdout"]
    with pytest.raises(OcrError, match="extraction limit") as too_large:
        service.extract_image(image, 4)
    assert too_large.value.code == "extracted_text_too_large"


def test_local_ocr_maps_process_timeout_to_safe_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"image")

    def timeout_run(
        command: list[str],
        **_: object,
    ) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr(shutil, "which", lambda name: f"/tools/{name}")
    monkeypatch.setattr(subprocess, "run", timeout_run)

    with pytest.raises(OcrError, match="timed out") as timeout:
        LocalOcrService(timeout_seconds=1).extract_image(image, 1_000)

    assert timeout.value.code == "ocr_timeout"
    assert timeout.value.retryable is True


def test_local_pdf_ocr_renders_bounded_pages_in_numeric_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF")

    def fake_process(
        command: Sequence[str],
        _: float,
        __: str,
    ) -> bytes:
        if command[0].endswith("pdftoppm"):
            prefix = Path(command[-1])
            prefix.with_name("page-2.png").write_bytes(b"page two")
            prefix.with_name("page-1.png").write_bytes(b"page one")
            return b""
        return f"text from {Path(command[1]).stem}".encode()

    monkeypatch.setattr(shutil, "which", lambda name: f"/tools/{name}")
    monkeypatch.setattr(LocalOcrService, "_run", staticmethod(fake_process))
    service = LocalOcrService(
        max_pages=2,
        timeout_seconds=30,
        max_rendered_bytes=100,
    )

    text = service.extract_pdf(pdf, page_count=2, max_output_bytes=100)

    assert text == "text from page-1\n\ntext from page-2"
