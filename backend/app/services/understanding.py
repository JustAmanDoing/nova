import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.intake import UnderstandingStatus

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
PREVIEW_CHARACTERS = 320


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
    understood_at: str


def understand_file(
    path: Path,
    extension: str,
    max_text_bytes: int,
) -> UnderstandingResult:
    understood_at = datetime.now(UTC).isoformat()
    normalized_extension = extension.lower()

    if normalized_extension not in SUPPORTED_TEXT_EXTENSIONS:
        return UnderstandingResult(
            status=UnderstandingStatus.unsupported,
            document_type=None,
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence=f"{normalized_extension or 'Unknown'} files are not supported yet.",
            error=None,
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
                understood_at=understood_at,
            )
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return UnderstandingResult(
            status=UnderstandingStatus.failed,
            document_type=_document_type(normalized_extension),
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence="Nova attempted local UTF-8 text extraction.",
            error="The file is not valid UTF-8 text.",
            understood_at=understood_at,
        )
    except OSError:
        return UnderstandingResult(
            status=UnderstandingStatus.failed,
            document_type=_document_type(normalized_extension),
            title=None,
            text_preview=None,
            word_count=None,
            character_count=None,
            evidence="Nova attempted to read the file locally.",
            error="Nova could not read the file.",
            understood_at=understood_at,
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
        understood_at=understood_at,
    )


def _document_type(extension: str) -> str:
    return "markdown" if extension in {".md", ".markdown"} else "plain_text"


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
