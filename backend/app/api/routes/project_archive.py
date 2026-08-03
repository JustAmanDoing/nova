import asyncio
from dataclasses import asdict
from typing import cast

from fastapi import APIRouter, HTTPException, Request

from app.schemas.project_archive import (
    ProjectArchiveDocumentResponse,
    ProjectArchiveReportResponse,
)
from app.services.project_archive import (
    ProjectArchiveError,
    ProjectArchiveService,
    ProjectArchiveSourceNotFoundError,
    ProjectArchiveSourceUnavailableError,
)

router = APIRouter(prefix="/project-archive", tags=["project archive"])


@router.get("", response_model=ProjectArchiveReportResponse)
async def project_archive_report(request: Request) -> ProjectArchiveReportResponse:
    try:
        report = await asyncio.to_thread(_archive(request).report)
    except ProjectArchiveError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ProjectArchiveReportResponse(**asdict(report))


@router.get(
    "/sources/{source_id}",
    response_model=ProjectArchiveDocumentResponse,
)
async def project_archive_document(
    source_id: str, request: Request
) -> ProjectArchiveDocumentResponse:
    try:
        document = await asyncio.to_thread(_archive(request).document, source_id)
    except ProjectArchiveSourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ProjectArchiveSourceUnavailableError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ProjectArchiveError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ProjectArchiveDocumentResponse(**asdict(document))


def _archive(request: Request) -> ProjectArchiveService:
    return cast(ProjectArchiveService, request.app.state.project_archive)
