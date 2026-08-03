import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PREVIEW_EXTENSIONS = {".html", ".json", ".md", ".txt"}


class ProjectArchiveError(RuntimeError):
    pass


class ProjectArchiveSourceNotFoundError(ProjectArchiveError):
    pass


class ProjectArchiveSourceUnavailableError(ProjectArchiveError):
    pass


@dataclass(frozen=True)
class ProjectArchiveSource:
    id: str
    label: str
    category: str
    authority: str
    relative_path: str
    expected_sha256: str
    actual_sha256: str | None
    expected_size_bytes: int
    actual_size_bytes: int | None
    captured_at: datetime
    verification_status: str
    preview_available: bool


@dataclass(frozen=True)
class ProjectArchiveReport:
    generated_at: datetime
    index_generated_at: datetime | None
    current_release: str | None
    current_commit: str | None
    migration_summary: str
    source_count: int
    verified_count: int
    changed_count: int
    missing_count: int
    invalid_count: int
    raw_chat_source_count: int
    sources: list[ProjectArchiveSource]
    warnings: list[str]


@dataclass(frozen=True)
class ProjectArchiveDocument:
    id: str
    label: str
    relative_path: str
    sha256: str
    content: str
    truncated: bool


class ProjectArchiveService:
    def __init__(
        self,
        archive_path: Path,
        *,
        max_sources: int = 1_000,
        max_source_bytes: int = 25_000_000,
        max_preview_characters: int = 50_000,
    ) -> None:
        self.archive_path = archive_path.resolve()
        self.index_path = self.archive_path / "archive-index.json"
        self.max_sources = max_sources
        self.max_source_bytes = max_source_bytes
        self.max_preview_characters = max_preview_characters

    def report(self) -> ProjectArchiveReport:
        if not self.index_path.is_file():
            return ProjectArchiveReport(
                generated_at=datetime.now(UTC),
                index_generated_at=None,
                current_release=None,
                current_commit=None,
                migration_summary=(
                    "No local project-record index has been created yet. "
                    "Existing NOVA data was not changed."
                ),
                source_count=0,
                verified_count=0,
                changed_count=0,
                missing_count=0,
                invalid_count=0,
                raw_chat_source_count=0,
                sources=[],
                warnings=[],
            )

        payload = self._load_index()
        raw_sources = payload.get("sources")
        if not isinstance(raw_sources, list):
            raise ProjectArchiveError("The project-record index has no source list.")
        if len(raw_sources) > self.max_sources:
            raise ProjectArchiveError(
                f"The project-record index exceeds the {self.max_sources}-source limit."
            )

        sources: list[ProjectArchiveSource] = []
        warnings: list[str] = []
        seen_ids: set[str] = set()
        for position, raw_source in enumerate(raw_sources, start=1):
            try:
                source = self._read_source(raw_source, seen_ids)
            except ProjectArchiveError as error:
                warnings.append(f"Source {position}: {error}")
                continue
            seen_ids.add(source.id)
            sources.append(source)

        sources.sort(key=lambda item: (item.category, item.label.casefold(), item.id))
        statuses = [source.verification_status for source in sources]
        raw_chat_source_count = sum(
            source.category == "raw_chat_source" for source in sources
        )
        return ProjectArchiveReport(
            generated_at=datetime.now(UTC),
            index_generated_at=self._parse_datetime(
                payload.get("generated_at"), "generated_at"
            ),
            current_release=self._optional_text(payload.get("current_release")),
            current_commit=self._optional_text(payload.get("current_commit")),
            migration_summary=self._required_text(
                payload.get("migration_summary"), "migration_summary"
            ),
            source_count=len(sources),
            verified_count=statuses.count("verified"),
            changed_count=statuses.count("changed"),
            missing_count=statuses.count("missing"),
            invalid_count=statuses.count("invalid") + len(warnings),
            raw_chat_source_count=raw_chat_source_count,
            sources=sources,
            warnings=warnings,
        )

    def document(self, source_id: str) -> ProjectArchiveDocument:
        report = self.report()
        source = next((item for item in report.sources if item.id == source_id), None)
        if source is None:
            raise ProjectArchiveSourceNotFoundError("Archive source not found.")
        if source.verification_status != "verified":
            raise ProjectArchiveSourceUnavailableError(
                "The source is not available because its checksum is not verified."
            )
        if not source.preview_available:
            raise ProjectArchiveSourceUnavailableError(
                "This source type is preserved locally but has no text preview."
            )

        path = self._resolve_source_path(source.relative_path)
        with path.open("rb") as source_file:
            preview_bytes = source_file.read(self.max_preview_characters * 4 + 1)
        content = preview_bytes.decode("utf-8", errors="replace")
        truncated = len(content) > self.max_preview_characters
        return ProjectArchiveDocument(
            id=source.id,
            label=source.label,
            relative_path=source.relative_path,
            sha256=source.expected_sha256,
            content=content[: self.max_preview_characters],
            truncated=truncated,
        )

    def _load_index(self) -> dict[str, object]:
        if self.index_path.stat().st_size > self.max_source_bytes:
            raise ProjectArchiveError("The project-record index is too large.")
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ProjectArchiveError(
                "The project-record index is unreadable or malformed."
            ) from error
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ProjectArchiveError("The project-record index schema is unsupported.")
        return payload

    def _read_source(
        self, raw_source: object, seen_ids: set[str]
    ) -> ProjectArchiveSource:
        if not isinstance(raw_source, dict):
            raise ProjectArchiveError("A source entry is not an object.")
        source_id = self._required_text(raw_source.get("id"), "id")
        if source_id in seen_ids:
            raise ProjectArchiveError(f"Duplicate source id: {source_id}.")
        label = self._required_text(raw_source.get("label"), "label")
        category = self._required_text(raw_source.get("category"), "category")
        authority = self._required_text(raw_source.get("authority"), "authority")
        relative_path = self._required_text(
            raw_source.get("relative_path"), "relative_path"
        ).replace("\\", "/")
        expected_sha256 = self._required_text(
            raw_source.get("sha256"), "sha256"
        ).lower()
        if not _SHA256.fullmatch(expected_sha256):
            raise ProjectArchiveError(f"Source {source_id} has an invalid SHA-256.")
        expected_size = raw_source.get("size_bytes")
        if not isinstance(expected_size, int) or expected_size < 0:
            raise ProjectArchiveError(f"Source {source_id} has an invalid size.")
        captured_at = self._parse_datetime(raw_source.get("captured_at"), "captured_at")

        try:
            path = self._resolve_source_path(relative_path)
        except ProjectArchiveError:
            return ProjectArchiveSource(
                id=source_id,
                label=label,
                category=category,
                authority=authority,
                relative_path=relative_path,
                expected_sha256=expected_sha256,
                actual_sha256=None,
                expected_size_bytes=expected_size,
                actual_size_bytes=None,
                captured_at=captured_at,
                verification_status="invalid",
                preview_available=False,
            )

        if not path.is_file():
            return ProjectArchiveSource(
                id=source_id,
                label=label,
                category=category,
                authority=authority,
                relative_path=relative_path,
                expected_sha256=expected_sha256,
                actual_sha256=None,
                expected_size_bytes=expected_size,
                actual_size_bytes=None,
                captured_at=captured_at,
                verification_status="missing",
                preview_available=False,
            )

        actual_size = path.stat().st_size
        if actual_size > self.max_source_bytes:
            return ProjectArchiveSource(
                id=source_id,
                label=label,
                category=category,
                authority=authority,
                relative_path=relative_path,
                expected_sha256=expected_sha256,
                actual_sha256=None,
                expected_size_bytes=expected_size,
                actual_size_bytes=actual_size,
                captured_at=captured_at,
                verification_status="invalid",
                preview_available=False,
            )

        actual_sha256 = self._hash_file(path)
        verified = actual_sha256 == expected_sha256 and actual_size == expected_size
        return ProjectArchiveSource(
            id=source_id,
            label=label,
            category=category,
            authority=authority,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
            actual_sha256=actual_sha256,
            expected_size_bytes=expected_size,
            actual_size_bytes=actual_size,
            captured_at=captured_at,
            verification_status="verified" if verified else "changed",
            preview_available=(verified and path.suffix.casefold() in _PREVIEW_EXTENSIONS),
        )

    def _resolve_source_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ProjectArchiveError("Archive paths must be relative.")
        resolved = (self.archive_path / candidate).resolve()
        if not resolved.is_relative_to(self.archive_path):
            raise ProjectArchiveError("Archive source escapes the configured root.")
        return resolved

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source_file:
            for block in iter(lambda: source_file.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ProjectArchiveError(f"The {field} field is missing or invalid.")
        return value.strip()

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _parse_datetime(value: object, field: str) -> datetime:
        if not isinstance(value, str):
            raise ProjectArchiveError(f"The {field} field is missing or invalid.")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ProjectArchiveError(f"The {field} field is invalid.") from error
        if parsed.tzinfo is None:
            raise ProjectArchiveError(f"The {field} field must include a timezone.")
        return parsed
