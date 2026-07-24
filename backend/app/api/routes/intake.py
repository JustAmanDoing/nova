import asyncio
from typing import cast

from fastapi import APIRouter, Query, Request

from app.schemas.intake import (
    IntakeFile,
    IntakeScanResult,
    IntakeStatus,
    IntakeSummary,
    UnderstandingStatus,
)
from app.services.intake import IntakeService

router = APIRouter(prefix="/intake", tags=["intake"])


def get_intake_service(request: Request) -> IntakeService:
    return cast(IntakeService, request.app.state.intake)


@router.get("/files", response_model=list[IntakeFile])
async def list_intake_files(
    request: Request,
    q: str | None = Query(default=None, max_length=200),
    status: IntakeStatus | None = None,
    understanding_status: UnderstandingStatus | None = None,
    extension: str | None = Query(default=None, max_length=20),
    document_type: str | None = Query(default=None, max_length=50),
) -> list[IntakeFile]:
    service = get_intake_service(request)
    return await asyncio.to_thread(
        service.list_files,
        query=q,
        status=status,
        understanding_status=understanding_status,
        extension=extension,
        document_type=document_type,
    )


@router.post("/scan", response_model=IntakeScanResult)
async def scan_intake(request: Request) -> IntakeScanResult:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.scan)


@router.get("/summary", response_model=IntakeSummary)
async def get_intake_summary(request: Request) -> IntakeSummary:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.summary)
