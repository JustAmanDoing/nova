import asyncio
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.dependencies import require_local_action
from app.schemas.backup import BackupRecord, RestoreRequest, RestoreResult
from app.services.backup import BackupError, BackupService, RestoreError

router = APIRouter(prefix="/backups", tags=["backups"])


def get_backup_service(request: Request) -> BackupService:
    return cast(BackupService, request.app.state.backups)


@router.get("", response_model=list[BackupRecord])
async def list_backups(request: Request) -> list[BackupRecord]:
    service = get_backup_service(request)
    return await asyncio.to_thread(service.list_backups)


@router.post(
    "",
    response_model=BackupRecord,
    status_code=201,
    dependencies=[Depends(require_local_action)],
)
async def create_backup(request: Request) -> BackupRecord:
    service = get_backup_service(request)
    try:
        return await asyncio.to_thread(service.create_backup)
    except BackupError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/{filename}", response_class=FileResponse)
async def download_backup(filename: str, request: Request) -> FileResponse:
    service = get_backup_service(request)
    try:
        path = await asyncio.to_thread(service.get_verified_backup_path, filename)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (BackupError, RestoreError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return FileResponse(
        path,
        media_type="application/vnd.sqlite3",
        filename=path.name,
    )


@router.get("/{filename}/checksum", response_class=FileResponse)
async def download_backup_checksum(filename: str, request: Request) -> FileResponse:
    service = get_backup_service(request)
    try:
        path = await asyncio.to_thread(service.get_verified_checksum_path, filename)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (BackupError, RestoreError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return FileResponse(
        path,
        media_type="text/plain; charset=us-ascii",
        filename=path.name,
    )


@router.post(
    "/{filename}/restore",
    response_model=RestoreResult,
    dependencies=[Depends(require_local_action)],
)
async def restore_backup(
    filename: str,
    restore: RestoreRequest,
    request: Request,
) -> RestoreResult:
    service = get_backup_service(request)
    try:
        return await asyncio.to_thread(
            service.restore_backup,
            filename,
            restore.confirmation,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (BackupError, RestoreError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
