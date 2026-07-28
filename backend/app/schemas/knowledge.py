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


class KnowledgeRecordResponse(BaseModel):
    id: str
    candidate_id: str
    kind: KnowledgeKind
    title: str
    content: str
    relative_path: str
    sha256: str
    created_at: datetime


class ReviewKnowledgeCandidateRequest(BaseModel):
    action: Literal["approve", "reject"]
    kind: KnowledgeKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=4_000)

    @model_validator(mode="after")
    def approved_fields_are_required(self) -> "ReviewKnowledgeCandidateRequest":
        if self.action == "approve" and (
            self.kind is None or self.title is None or self.content is None
        ):
            raise ValueError(
                "Approving knowledge requires its type, title, and content."
            )
        return self
