from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NextActionStatus = Literal["open", "completed"]
NextActionEventType = Literal["created", "completed", "reopened"]


class CreateNextActionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    project_record_id: str | None = Field(default=None, min_length=1)


class NextActionResponse(BaseModel):
    id: str
    title: str
    status: NextActionStatus
    project_record_id: str | None
    project_title: str | None
    project_revision: int | None = Field(default=None, ge=1)
    project_unavailable: bool
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class NextActionOverviewResponse(BaseModel):
    generated_at: datetime
    open: list[NextActionResponse]
    completed: list[NextActionResponse]
    limitation: str


class NextActionEventResponse(BaseModel):
    sequence: int = Field(ge=1)
    action_id: str
    event_type: NextActionEventType
    detail: str
    created_at: datetime
