import asyncio
from typing import cast

from fastapi import APIRouter, Request

from app.schemas.intake import IntakeFile, IntakeScanResult
from app.services.intake import IntakeService

router = APIRouter(prefix="/intake", tags=["intake"])


def get_intake_service(request: Request) -> IntakeService:
    return cast(IntakeService, request.app.state.intake)


@router.get("/files", response_model=list[IntakeFile])
async def list_intake_files(request: Request) -> list[IntakeFile]:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.list_files)


@router.post("/scan", response_model=IntakeScanResult)
async def scan_intake(request: Request) -> IntakeScanResult:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.scan)
