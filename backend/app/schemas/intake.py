from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IntakeStatus(StrEnum):
    observed = "observed"
    duplicate = "duplicate"


class UnderstandingStatus(StrEnum):
    ready = "ready"
    empty = "empty"
    unsupported = "unsupported"
    too_large = "too_large"
    failed = "failed"


class RecommendationOutcome(StrEnum):
    suggested = "suggested"
    insufficient_evidence = "insufficient_evidence"


class ApprovalAction(StrEnum):
    edit = "edit"
    approve = "approve"
    reject = "reject"
    ignore = "ignore"


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    ignored = "ignored"


class RecommendationRecord(BaseModel):
    outcome: RecommendationOutcome
    category: str | None
    suggested_filename: str | None
    destination: str | None
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1)
    generated_at: datetime


class ApprovalRequest(BaseModel):
    action: ApprovalAction
    category: str | None = Field(default=None, max_length=80)
    suggested_filename: str | None = Field(default=None, max_length=255)
    destination: str | None = Field(default=None, max_length=500)


class ApprovalRecord(BaseModel):
    status: ApprovalStatus
    category: str
    suggested_filename: str
    destination: str
    recommendation_generated_at: datetime
    reviewed_at: datetime


class UnderstandingRecord(BaseModel):
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
    understood_at: datetime


class IntakeFile(BaseModel):
    id: str
    relative_path: str
    original_name: str
    extension: str
    size_bytes: int
    modified_at: datetime
    observed_at: datetime
    sha256: str
    status: IntakeStatus
    duplicate_of: str | None
    understanding: UnderstandingRecord | None
    recommendation: RecommendationRecord | None
    approval: ApprovalRecord | None


class IntakeScanResult(BaseModel):
    scanned: int
    added: int
    updated: int
    removed: int
    duplicates: int


class IntakeSummary(BaseModel):
    files_observed: int
    understood: int
    ready_for_review: int
    exact_duplicates: int
