from datetime import datetime

from pydantic import BaseModel, Field


class LearningPreferenceRecord(BaseModel):
    document_type: str
    base_category: str
    candidate_destination: str | None
    supporting_examples: int = Field(ge=0)
    active_examples: int = Field(ge=0)
    stored_examples: int = Field(ge=0)
    preference_share: float = Field(ge=0, le=1)
    eligible: bool
    revision: int = Field(ge=0)


class LearningResetRequest(BaseModel):
    document_type: str = Field(min_length=1, max_length=50)
    base_category: str = Field(min_length=1, max_length=80)
    confirmation: str = Field(min_length=1, max_length=300)


class LearningResetResult(BaseModel):
    document_type: str
    base_category: str
    removed_examples: int = Field(ge=1)
    reset_at: datetime
    detail: str
