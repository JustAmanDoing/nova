from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class IntakeStatus(StrEnum):
    observed = "observed"
    duplicate = "duplicate"


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


class IntakeScanResult(BaseModel):
    scanned: int
    added: int
    updated: int
    duplicates: int
