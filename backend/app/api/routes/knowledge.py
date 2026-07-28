import asyncio
from dataclasses import asdict
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import require_local_action
from app.schemas.knowledge import (
    KnowledgeCandidate,
    KnowledgeRecordResponse,
    ReviewKnowledgeCandidateRequest,
)
from app.services.knowledge import (
    KnowledgeCandidateNotFoundError,
    KnowledgeCandidateStateError,
    KnowledgeRecordWriteError,
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
            )
    except KnowledgeCandidateNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Knowledge proposal not found.",
        ) from error
    except KnowledgeCandidateStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (KnowledgeRecordWriteError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return KnowledgeCandidate(**asdict(record))


@router.get("/records", response_model=list[KnowledgeRecordResponse])
async def list_records(request: Request) -> list[KnowledgeRecordResponse]:
    records = await asyncio.to_thread(_knowledge(request).list_records)
    return [KnowledgeRecordResponse(**asdict(record)) for record in records]


def _knowledge(request: Request) -> KnowledgeService:
    return cast(KnowledgeService, request.app.state.knowledge)
