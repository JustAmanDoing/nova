from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ArchiveVerificationStatus = Literal["verified", "changed", "missing", "invalid"]


class ProjectArchiveSourceResponse(BaseModel):
    id: str
    label: str
    category: str
    authority: str
    relative_path: str
    expected_sha256: str
    actual_sha256: str | None
    expected_size_bytes: int = Field(ge=0)
    actual_size_bytes: int | None = Field(default=None, ge=0)
    captured_at: datetime
    verification_status: ArchiveVerificationStatus
    preview_available: bool


class ProjectArchiveReportResponse(BaseModel):
    generated_at: datetime
    index_generated_at: datetime | None
    current_release: str | None
    current_commit: str | None
    migration_summary: str
    source_count: int = Field(ge=0)
    verified_count: int = Field(ge=0)
    changed_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)
    raw_chat_source_count: int = Field(ge=0)
    sources: list[ProjectArchiveSourceResponse]
    warnings: list[str]


class ProjectArchiveDocumentResponse(BaseModel):
    id: str
    label: str
    relative_path: str
    sha256: str
    content: str
    truncated: bool
