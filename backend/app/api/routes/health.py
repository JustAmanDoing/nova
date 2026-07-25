import asyncio
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Request

from app.core.config import Settings
from app.schemas.health import (
    DatabaseIntegrityStatus,
    HealthResponse,
    OperationalStatus,
)
from app.services.intake import IntakeService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = cast(Settings, request.app.state.settings)
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/system/status", response_model=OperationalStatus)
async def operational_status(request: Request) -> OperationalStatus:
    intake = cast(IntakeService, request.app.state.intake)
    return await asyncio.to_thread(intake.operational_status)


@router.get(
    "/system/integrity",
    response_model=DatabaseIntegrityStatus,
)
async def database_integrity(request: Request) -> DatabaseIntegrityStatus:
    intake = cast(IntakeService, request.app.state.intake)
    return await asyncio.to_thread(intake.database_integrity)
