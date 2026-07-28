from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

KnowledgeKind = Literal[
    "fact",
    "preference",
    "goal",
    "project",
    "lesson",
    "rule",
    "reference",
]
KnowledgeCandidateStatus = Literal["pending", "approved", "rejected"]
KnowledgeRecordStatus = Literal["active", "retired"]


class KnowledgeCandidate(BaseModel):
    id: str
    conversation_id: str
    source_message_id: str
    kind: KnowledgeKind
    title: str
    content: str
    source_excerpt: str
    reason: str
    confidence: float
    explicit_request: bool
    status: KnowledgeCandidateStatus
    created_at: datetime
    reviewed_at: datetime | None
    record_path: str | None
    duplicate_record_id: str | None
    duplicate_title: str | None
    duplicate_path: str | None
    duplicate_score: float | None


class KnowledgeRecordResponse(BaseModel):
    id: str
    candidate_id: str
    kind: KnowledgeKind
    title: str
    content: str
    relative_path: str
    sha256: str
    created_at: datetime
    status: KnowledgeRecordStatus
    revision: int
    updated_at: datetime
    retired_at: datetime | None


class ReviewKnowledgeCandidateRequest(BaseModel):
    action: Literal["approve", "reject"]
    kind: KnowledgeKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=4_000)
    duplicate_confirmation: str | None = None

    @model_validator(mode="after")
    def approved_fields_are_required(self) -> "ReviewKnowledgeCandidateRequest":
        if self.action == "approve" and (
            self.kind is None or self.title is None or self.content is None
        ):
            raise ValueError(
                "Approving knowledge requires its type, title, and content."
            )
        return self


class KnowledgeRecordLifecycleRequest(BaseModel):
    action: Literal["update", "retire"]
    kind: KnowledgeKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=4_000)
    confirmation: str | None = None
    duplicate_confirmation: str | None = None

    @model_validator(mode="after")
    def lifecycle_fields_are_consistent(self) -> "KnowledgeRecordLifecycleRequest":
        if self.action == "update" and (
            self.kind is None or self.title is None or self.content is None
        ):
            raise ValueError(
                "Updating knowledge requires its type, title, and content."
            )
        if self.action == "retire" and self.confirmation is None:
            raise ValueError("Retiring knowledge requires typed confirmation.")
        return self


class KnowledgeSnapshotResponse(BaseModel):
    filename: str
    size_bytes: int
    sha256: str
    record_count: int
    file_count: int
    created_at: datetime
