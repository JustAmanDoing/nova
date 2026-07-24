import logging
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from app.schemas.intake import UnderstandingStatus

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf", ".docx"}
PREVIEW_CHARACTERS = 320
WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
logger = logging.getLogger(__name__)


class ExtractedContentTooLarge(Exception):
    """Raised before extracted document content can exhaust local resources."""


@dataclass(frozen=True)
class UnderstandingResult:
    status: UnderstandingStatus
    document_type: str | None
    title: str | None
    text_preview: str | None
    word_count: int | None
    character_count: int | None
    evidence: str
    error: str | None
    error_code: str | None
    extraction_method: str
    retryable: bool
    full_text: str | None
    understood_at: str


def understand_file(
    path: Path,
    extension: str,
    max_text_bytes: int,
    max_extracted_text_bytes: int = 1_000_000,
) -> UnderstandingResult:
    understood_at = datetime.now(UTC).isoformat()
    normalized_extension = extension.lower()

    if normalized_extension not in SUPPORTED_EXTENSIONS:
        return UnderstandingResult(
            status=UnderstandingStatus.unsupported,
            document_type=None,
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence=f"{normalized_extension or 'Unknown'} files are not supported yet.",
            error=None,
            error_code=None,
            extraction_method="none",
            retryable=False,
            full_text=None,
            understood_at=understood_at,
        )

    try:
        if path.stat().st_size > max_text_bytes:
            return UnderstandingResult(
                status=UnderstandingStatus.too_large,
                document_type=_document_type(normalized_extension),
                title=None,
                text_preview=None,
                word_count=None,
                character_count=None,
                evidence=f"Local extraction is limited to {max_text_bytes} bytes.",
                error=None,
                error_code="file_too_large",
                extraction_method=_extraction_method(normalized_extension),
                retryable=False,
                full_text=None,
                understood_at=understood_at,
            )
        text, extraction_method = _extract_text(
            path,
            normalized_extension,
            max_extracted_text_bytes,
        )
    except ExtractedContentTooLarge:
        return UnderstandingResult(
            status=UnderstandingStatus.too_large,
            document_type=_document_type(normalized_extension),
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence=(
                "Extracted text exceeded the configured local limit of "
                f"{max_extracted_text_bytes} bytes."
            ),
            error=None,
            error_code="extracted_text_too_large",
            extraction_method=_extraction_method(normalized_extension),
            retryable=False,
            full_text=None,
            understood_at=understood_at,
        )
    except UnicodeDecodeError:
        return UnderstandingResult(
            status=UnderstandingStatus.failed,
            document_type=_document_type(normalized_extension),
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence="Nova attempted local UTF-8 text extraction.",
            error="The file could not be decoded as UTF-8 text.",
            error_code="invalid_utf8",
            extraction_method=_extraction_method(normalized_extension),
            retryable=False,
            full_text=None,
            understood_at=understood_at,
        )
    except FileNotDecryptedError:
        return _failure(
            normalized_extension,
            understood_at,
            "The PDF is encrypted and cannot be read without its password.",
            "encrypted_pdf",
            retryable=False,
        )
    except PdfReadError as error:
        return _failure(
            normalized_extension,
            understood_at,
            f"The PDF structure could not be read: {error}.",
            "invalid_pdf",
            retryable=False,
        )
    except (zipfile.BadZipFile, ElementTree.ParseError, KeyError) as error:
        return _failure(
            normalized_extension,
            understood_at,
            f"The Word document structure could not be read: {error}.",
            "invalid_docx",
            retryable=False,
        )
    except OSError as error:
        return UnderstandingResult(
            status=UnderstandingStatus.failed,
            document_type=_document_type(normalized_extension),
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence="Nova attempted to read the file locally.",
            error=f"Nova could not read the file: {error.strerror or type(error).__name__}.",
            error_code="file_read_error",
            extraction_method=_extraction_method(normalized_extension),
            retryable=True,
            full_text=None,
            understood_at=understood_at,
        )
    except Exception:
        logger.exception("Unexpected extraction failure for %s", path.name)
        return _failure(
            normalized_extension,
            understood_at,
            "The local extractor failed unexpectedly. Review the Nova logs and retry.",
            "extractor_error",
            retryable=True,
        )

    normalized_text = text.strip()
    if not normalized_text:
        return UnderstandingResult(
            status=UnderstandingStatus.empty,
            document_type=_document_type(normalized_extension),
            title=None,
            text_preview=None,
            word_count=0,
            character_count=0,
            evidence="The file was read locally and contains no text.",
            error=None,
            error_code=None,
            extraction_method=extraction_method,
            retryable=False,
            full_text="",
            understood_at=understood_at,
        )

    document_type = _document_type(normalized_extension)
    return UnderstandingResult(
        status=UnderstandingStatus.ready,
        document_type=document_type,
        title=_extract_title(normalized_text, normalized_extension),
        text_preview=_text_preview(normalized_text),
        word_count=len(re.findall(r"\b[\w'-]+\b", normalized_text, flags=re.UNICODE)),
        character_count=len(normalized_text),
        evidence=f"Extracted locally from {document_type.replace('_', ' ')} content.",
        error=None,
        error_code=None,
        extraction_method=extraction_method,
        retryable=False,
        full_text=normalized_text,
        understood_at=understood_at,
    )


def _document_type(extension: str) -> str:
    if extension in {".md", ".markdown"}:
        return "markdown"
    if extension == ".pdf":
        return "pdf"
    if extension == ".docx":
        return "word_document"
    return "plain_text"


def _extract_text(
    path: Path,
    extension: str,
    max_extracted_text_bytes: int,
) -> tuple[str, str]:
    if extension == ".pdf":
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise FileNotDecryptedError("PDF is encrypted")
        pages: list[str] = []
        extracted_bytes = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            extracted_bytes += len(page_text.encode("utf-8"))
            if extracted_bytes > max_extracted_text_bytes:
                raise ExtractedContentTooLarge
            pages.append(page_text)
        text = "\n\n".join(pages)
        _ensure_extracted_size(text, max_extracted_text_bytes)
        return text, "pypdf"
    if extension == ".docx":
        return _extract_docx(path, max_extracted_text_bytes), "docx_xml"
    text = path.read_text(encoding="utf-8-sig")
    _ensure_extracted_size(text, max_extracted_text_bytes)
    return text, "utf-8"


def _extract_docx(path: Path, max_extracted_text_bytes: int) -> str:
    with zipfile.ZipFile(path) as archive:
        document_info = archive.getinfo("word/document.xml")
        if document_info.file_size > max_extracted_text_bytes * 8:
            raise ExtractedContentTooLarge
        document = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    extracted_bytes = 0
    for paragraph in document.iter(f"{{{WORD_NAMESPACE}}}p"):
        text = "".join(
            node.text or "" for node in paragraph.iter(f"{{{WORD_NAMESPACE}}}t")
        ).strip()
        if text:
            extracted_bytes += len(text.encode("utf-8")) + 1
            if extracted_bytes > max_extracted_text_bytes:
                raise ExtractedContentTooLarge
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _ensure_extracted_size(text: str, max_extracted_text_bytes: int) -> None:
    if len(text.encode("utf-8")) > max_extracted_text_bytes:
        raise ExtractedContentTooLarge


def _extraction_method(extension: str) -> str:
    if extension == ".pdf":
        return "pypdf"
    if extension == ".docx":
        return "docx_xml"
    return "utf-8"


def _failure(
    extension: str,
    understood_at: str,
    error: str,
    error_code: str,
    *,
    retryable: bool,
) -> UnderstandingResult:
    return UnderstandingResult(
        status=UnderstandingStatus.failed,
        document_type=_document_type(extension),
        title=None,
        text_preview=None,
        word_count=None,
        character_count=None,
        evidence=f"Nova attempted local {_extraction_method(extension)} extraction.",
        error=error,
        error_code=error_code,
        extraction_method=_extraction_method(extension),
        retryable=retryable,
        full_text=None,
        understood_at=understood_at,
    )


def _extract_title(text: str, extension: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    if extension in {".md", ".markdown"}:
        heading = next(
            (line.lstrip("#").strip() for line in lines if line.startswith("#")),
            None,
        )
        if heading:
            return heading[:160]
    return lines[0][:160]


def _text_preview(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= PREVIEW_CHARACTERS:
        return collapsed
    return f"{collapsed[: PREVIEW_CHARACTERS - 1].rstrip()}…"
