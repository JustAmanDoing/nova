import asyncio
from typing import cast

from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas.intake import (
    ActionRecord,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalStatus,
    IntakeFile,
    IntakeScanResult,
    IntakeStatus,
    IntakeSummary,
    UnderstandingStatus,
)
from app.services.intake import ActionConflict, IntakeService

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
    approval_status: ApprovalStatus | None = None,
) -> list[IntakeFile]:
    service = get_intake_service(request)
    return await asyncio.to_thread(
        service.list_files,
        query=q,
        status=status,
        understanding_status=understanding_status,
        extension=extension,
        document_type=document_type,
        approval_status=approval_status,
    )


@router.post("/scan", response_model=IntakeScanResult)
async def scan_intake(request: Request) -> IntakeScanResult:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.scan)


@router.get("/summary", response_model=IntakeSummary)
async def get_intake_summary(request: Request) -> IntakeSummary:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.summary)


@router.put(
    "/files/{file_id}/approval",
    response_model=ApprovalRecord,
)
async def review_recommendation(
    file_id: str,
    review: ApprovalRequest,
    request: Request,
) -> ApprovalRecord:
    service = get_intake_service(request)
    try:
        return await asyncio.to_thread(service.review_recommendation, file_id, review)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/actions", response_model=list[ActionRecord])
async def list_actions(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ActionRecord]:
    service = get_intake_service(request)
    return await asyncio.to_thread(service.list_actions, limit)


@router.post("/files/{file_id}/execute", response_model=ActionRecord)
async def execute_approved(file_id: str, request: Request) -> ActionRecord:
    service = get_intake_service(request)
    try:
        return await asyncio.to_thread(service.execute_approved, file_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ActionConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/actions/{operation_id}/undo", response_model=ActionRecord)
async def undo_action(operation_id: str, request: Request) -> ActionRecord:
    service = get_intake_service(request)
    try:
        return await asyncio.to_thread(service.undo_action, operation_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ActionConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
