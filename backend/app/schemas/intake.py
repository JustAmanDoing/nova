from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class IntakeStatus(StrEnum):
    observed = "observed"
    duplicate = "duplicate"


class UnderstandingStatus(StrEnum):
    ready = "ready"
    empty = "empty"
    unsupported = "unsupported"
    too_large = "too_large"
    failed = "failed"


class UnderstandingRecord(BaseModel):
    status: UnderstandingStatus
    document_type: str | None
    title: str | None
    text_preview: str | None
    word_count: int | None
    character_count: int | None
    evidence: str
    error: str | None
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


class IntakeScanResult(BaseModel):
    scanned: int
    added: int
    updated: int
    duplicates: int
