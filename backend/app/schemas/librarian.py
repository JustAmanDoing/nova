from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

LibrarianIssueType = Literal[
    "duplicate",
    "conflict",
    "stale",
    "missing_coverage",
    "missing_file",
    "checksum_mismatch",
    "broken_reference",
]
LibrarianPriority = Literal["critical", "high", "medium", "low"]
LibrarianVerification = Literal[
    "verified",
    "missing_file",
    "checksum_mismatch",
    "broken_reference",
]


class LibrarianSourceResponse(BaseModel):
    record_id: str
    candidate_id: str
    kind: str
    title: str
    content: str
    status: Literal["active", "retired"]
    revision: int = Field(ge=1)
    updated_at: datetime
    relative_path: str
    sha256: str
    verification_status: LibrarianVerification
    candidate_confidence: float = Field(ge=0, le=1)
    explicit_request: bool
    source_reason: str
    conversation_id: str
    source_message_id: str


class LibrarianIssueResponse(BaseModel):
    id: str
    issue_type: LibrarianIssueType
    priority: LibrarianPriority
    title: str
    summary: str
    reason: str
    evidence: list[str]
    confidence: float = Field(ge=0, le=1)
    record_ids: list[str]
    source_titles: list[str]
    suggested_action: str
    review_url: str | None


class LibrarianHealthDimensionsResponse(BaseModel):
    coverage: float = Field(ge=0, le=100)
    freshness: float = Field(ge=0, le=100)
    retrieval: float = Field(ge=0, le=100)
    integrity: float = Field(ge=0, le=100)
    consistency: float = Field(ge=0, le=100)


class LibrarianIssueCountsResponse(BaseModel):
    duplicates: int = Field(ge=0)
    conflicts: int = Field(ge=0)
    stale: int = Field(ge=0)
    missing_coverage: int = Field(ge=0)
    missing_files: int = Field(ge=0)
    checksum_failures: int = Field(ge=0)
    broken_references: int = Field(ge=0)


class LibrarianHealthResponse(BaseModel):
    generated_at: datetime
    health_score: float = Field(ge=0, le=100)
    dimensions: LibrarianHealthDimensionsResponse
    counts: LibrarianIssueCountsResponse
    active_record_count: int = Field(ge=0)
    retired_record_count: int = Field(ge=0)
    verified_source_count: int = Field(ge=0)
    average_source_confidence: float | None = Field(default=None, ge=0, le=1)
    methodology: str
    limitation: str


class LibrarianReviewResponse(BaseModel):
    generated_at: datetime
    total: int = Field(ge=0)
    issues: list[LibrarianIssueResponse]
    limitation: str


class LibrarianRevisionResponse(BaseModel):
    record_id: str
    revision: int = Field(ge=1)
    status: Literal["active", "retired"]
    created_at: datetime
    relative_path: str
    sha256: str


class LibrarianEventResponse(BaseModel):
    sequence: int = Field(ge=1)
    record_id: str
    event_type: Literal["created", "updated", "retired"]
    detail: str
    created_at: datetime


class LibrarianItemResponse(BaseModel):
    generated_at: datetime
    issue: LibrarianIssueResponse
    sources: list[LibrarianSourceResponse]
    revisions: list[LibrarianRevisionResponse]
    events: list[LibrarianEventResponse]
    limitation: str
