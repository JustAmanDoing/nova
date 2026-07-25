from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str
    timestamp: datetime


class OperationalStatus(BaseModel):
    status: Literal["healthy", "attention"]
    uptime_seconds: int = Field(ge=0)
    database_size_bytes: int | None = Field(default=None, ge=0)
    storage_free_bytes: int | None = Field(default=None, ge=0)
    storage_total_bytes: int | None = Field(default=None, ge=1)
    storage_free_percent: float | None = Field(default=None, ge=0, le=100)
    last_scan_status: Literal["ok", "failed", "never"]
    last_scan_completed_at: datetime | None
    last_scan_duration_ms: int | None = Field(default=None, ge=0)
    warnings: list[str]
