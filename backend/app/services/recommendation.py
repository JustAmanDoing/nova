import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.intake import RecommendationOutcome

RULES_VERSION = 1


@dataclass(frozen=True)
class RecommendationResult:
    outcome: RecommendationOutcome
    category: str | None
    suggested_filename: str | None
    destination: str | None
    confidence: float
    reasons: list[str]
    generated_at: str


def recommend_file(
    *,
    original_name: str,
    extension: str,
    modified_at: str,
    title: str | None,
    full_text: str | None,
    understanding_status: str | None,
    is_duplicate: bool,
) -> RecommendationResult:
    generated_at = datetime.now(UTC).isoformat()
    if is_duplicate:
        return _insufficient(
            generated_at,
            "Exact duplicates are not recommended for filing independently.",
        )
    if understanding_status != "ready" or not full_text:
        return _insufficient(
            generated_at,
            "A complete local understanding result is required.",
        )

    searchable = f"{title or ''}\n{full_text}".lower()
    invoice_signals = [
        signal
        for signal in ("invoice", "invoice number", "supplier:", "total:")
        if signal in searchable
    ]
    project_signals = [
        signal
        for signal in ("project", "roadmap", "milestone")
        if signal in searchable
    ]

    if len(invoice_signals) >= 2:
        source = _extract_labeled_value(full_text, ("supplier", "vendor")) or "Unknown"
        document_date = _extract_document_date(full_text, modified_at)
        confidence = 0.96 if "invoice number" in invoice_signals else 0.92
        return RecommendationResult(
            outcome=RecommendationOutcome.suggested,
            category="Financial",
            suggested_filename=_filename(
                document_date,
                "Financial",
                "Invoice",
                source,
                extension,
            ),
            destination="Financial/Invoices",
            confidence=confidence,
            reasons=[
                f"Matched invoice signals: {', '.join(invoice_signals)}.",
                "Applied the approved Financial filing category.",
                "No file will change until a later approval step.",
            ],
            generated_at=generated_at,
        )

    if project_signals:
        subject = title or Path(original_name).stem
        document_date = _extract_document_date(full_text, modified_at)
        return RecommendationResult(
            outcome=RecommendationOutcome.suggested,
            category="Project",
            suggested_filename=_filename(
                document_date,
                "Project",
                subject,
                "Local",
                extension,
            ),
            destination="Project",
            confidence=0.92,
            reasons=[
                f"Matched project signals: {', '.join(project_signals)}.",
                "Applied the approved Project filing category.",
                "No file will change until a later approval step.",
            ],
            generated_at=generated_at,
        )

    return _insufficient(
        generated_at,
        "No deterministic filing rule had enough evidence.",
    )


def _insufficient(generated_at: str, reason: str) -> RecommendationResult:
    return RecommendationResult(
        outcome=RecommendationOutcome.insufficient_evidence,
        category=None,
        suggested_filename=None,
        destination=None,
        confidence=0.0,
        reasons=[reason],
        generated_at=generated_at,
    )


def _extract_labeled_value(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        match = re.search(
            rf"(?im)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$",
            text,
        )
        if match:
            return match.group(1).strip()[:80]
    return None


def _extract_document_date(text: str, modified_at: str) -> str:
    day_first = re.search(r"\b(\d{2})-(\d{2})-(\d{4})\b", text)
    if day_first:
        return day_first.group(0)
    year_first = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if year_first:
        return f"{year_first.group(3)}-{year_first.group(2)}-{year_first.group(1)}"
    return datetime.fromisoformat(modified_at).strftime("%d-%m-%Y")


def _filename(
    date: str,
    category: str,
    subject: str,
    source: str,
    extension: str,
) -> str:
    components = (
        date,
        _safe_component(category),
        _safe_component(subject),
        _safe_component(source),
        "v01",
    )
    suffix = (
        extension.lower()
        if extension.startswith(".") or not extension
        else f".{extension.lower()}"
    )
    return f"{'_'.join(components)}{suffix}"


def _safe_component(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    return (normalized or "Unknown")[:80]
