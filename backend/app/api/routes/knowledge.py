import asyncio
from dataclasses import asdict
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import require_local_action
from app.schemas.knowledge import (
    KnowledgeCandidate,
    KnowledgeQualityReportResponse,
    KnowledgeRecordLifecycleRequest,
    KnowledgeRecordResponse,
    KnowledgeSnapshotResponse,
    ReviewKnowledgeCandidateRequest,
)
from app.services.knowledge import (
    KnowledgeBackupError,
    KnowledgeCandidateNotFoundError,
    KnowledgeCandidateStateError,
    KnowledgeDuplicateConfirmationError,
    KnowledgeRecordNotFoundError,
    KnowledgeRecordStateError,
    KnowledgeRecordWriteError,
    KnowledgeRetrievalError,
    KnowledgeService,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
LocalAction = Annotated[None, Depends(require_local_action)]


@router.get("/candidates", response_model=list[KnowledgeCandidate])
async def list_candidates(
    request: Request,
    status: Annotated[
        Literal["pending", "approved", "rejected"] | None,
        Query(),
    ] = None,
) -> list[KnowledgeCandidate]:
    records = await asyncio.to_thread(_knowledge(request).list_candidates, status)
    return [KnowledgeCandidate(**asdict(record)) for record in records]


@router.put(
    "/candidates/{candidate_id}",
    response_model=KnowledgeCandidate,
)
async def review_candidate(
    candidate_id: str,
    payload: ReviewKnowledgeCandidateRequest,
    request: Request,
    _local_action: LocalAction,
) -> KnowledgeCandidate:
    knowledge = _knowledge(request)
    try:
        if payload.action == "reject":
            record = await asyncio.to_thread(
                knowledge.reject_candidate,
                candidate_id,
            )
        else:
            record = await asyncio.to_thread(
                knowledge.approve_candidate,
                candidate_id,
                cast(str, payload.kind),
                cast(str, payload.title),
                cast(str, payload.content),
                payload.duplicate_confirmation,
            )
    except KnowledgeCandidateNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Knowledge proposal not found.",
        ) from error
    except KnowledgeCandidateStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except KnowledgeDuplicateConfirmationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (
        KnowledgeRecordWriteError,
        KnowledgeRetrievalError,
        ValueError,
    ) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return KnowledgeCandidate(**asdict(record))


@router.get("/records", response_model=list[KnowledgeRecordResponse])
async def list_records(request: Request) -> list[KnowledgeRecordResponse]:
    records = await asyncio.to_thread(_knowledge(request).list_records)
    return [KnowledgeRecordResponse(**asdict(record)) for record in records]


@router.get("/quality", response_model=KnowledgeQualityReportResponse)
async def knowledge_quality(request: Request) -> KnowledgeQualityReportResponse:
    try:
        report = await asyncio.to_thread(_knowledge(request).quality_report)
    except KnowledgeRetrievalError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return KnowledgeQualityReportResponse(**asdict(report))


@router.put(
    "/records/{record_id}",
    response_model=KnowledgeRecordResponse,
)
async def update_record_lifecycle(
    record_id: str,
    payload: KnowledgeRecordLifecycleRequest,
    request: Request,
    _local_action: LocalAction,
) -> KnowledgeRecordResponse:
    knowledge = _knowledge(request)
    try:
        if payload.action == "retire":
            record = await asyncio.to_thread(
                knowledge.retire_record,
                record_id,
                cast(str, payload.confirmation),
            )
        else:
            record = await asyncio.to_thread(
                knowledge.update_record,
                record_id,
                cast(str, payload.kind),
                cast(str, payload.title),
                cast(str, payload.content),
                payload.duplicate_confirmation,
            )
    except KnowledgeRecordNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found.",
        ) from error
    except (
        KnowledgeDuplicateConfirmationError,
        KnowledgeRecordStateError,
    ) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (
        KnowledgeRecordWriteError,
        KnowledgeRetrievalError,
        ValueError,
    ) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return KnowledgeRecordResponse(**asdict(record))


@router.post(
    "/snapshots",
    response_model=KnowledgeSnapshotResponse,
)
async def create_knowledge_snapshot(
    request: Request,
    _local_action: LocalAction,
) -> KnowledgeSnapshotResponse:
    try:
        snapshot = await asyncio.to_thread(_knowledge(request).create_snapshot)
    except KnowledgeBackupError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return KnowledgeSnapshotResponse(**asdict(snapshot))


def _knowledge(request: Request) -> KnowledgeService:
    return cast(KnowledgeService, request.app.state.knowledge)
