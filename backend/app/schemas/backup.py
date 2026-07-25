from datetime import datetime

from pydantic import BaseModel, Field


class BackupRecord(BaseModel):
    filename: str
    size_bytes: int
    sha256: str | None
    created_at: datetime
    checksum_recorded: bool
    verified: bool


class RestoreRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=300)


class RestoreResult(BaseModel):
    restored_from: str
    restored_from_sha256: str
    safety_backup: BackupRecord
    restored_at: datetime
    detail: str
