import asyncio
from dataclasses import asdict
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import require_local_action
from app.schemas.next_actions import (
    CreateNextActionRequest,
    NextActionEventResponse,
    NextActionOverviewResponse,
    NextActionResponse,
)
from app.services.next_actions import (
    NextActionNotFoundError,
    NextActionProjectError,
    NextActionService,
    NextActionStateError,
)

router = APIRouter(prefix="/focus/actions", tags=["next-actions"])
LocalAction = Annotated[None, Depends(require_local_action)]


@router.get("", response_model=NextActionOverviewResponse)
async def next_action_overview(request: Request) -> NextActionOverviewResponse:
    overview = await asyncio.to_thread(_next_actions(request).overview)
    return NextActionOverviewResponse(**asdict(overview))


@router.post("", response_model=NextActionResponse, status_code=201)
async def create_next_action(
    payload: CreateNextActionRequest,
    request: Request,
    _local_action: LocalAction,
) -> NextActionResponse:
    try:
        action = await asyncio.to_thread(
            _next_actions(request).create,
            payload.title,
            payload.project_record_id,
        )
    except (NextActionProjectError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return NextActionResponse(**asdict(action))


@router.post(
    "/{action_id}/complete",
    response_model=NextActionResponse,
)
async def complete_next_action(
    action_id: str,
    request: Request,
    _local_action: LocalAction,
) -> NextActionResponse:
    return await _transition(request, action_id, "complete")


@router.post(
    "/{action_id}/reopen",
    response_model=NextActionResponse,
)
async def reopen_next_action(
    action_id: str,
    request: Request,
    _local_action: LocalAction,
) -> NextActionResponse:
    return await _transition(request, action_id, "reopen")


@router.get(
    "/{action_id}/events",
    response_model=list[NextActionEventResponse],
)
async def next_action_events(
    action_id: str,
    request: Request,
) -> list[NextActionEventResponse]:
    try:
        events = await asyncio.to_thread(_next_actions(request).events, action_id)
    except NextActionNotFoundError as error:
        raise HTTPException(status_code=404, detail="Next action not found.") from error
    return [NextActionEventResponse(**asdict(event)) for event in events]


async def _transition(
    request: Request,
    action_id: str,
    transition: str,
) -> NextActionResponse:
    service = _next_actions(request)
    operation = service.complete if transition == "complete" else service.reopen
    try:
        action = await asyncio.to_thread(operation, action_id)
    except NextActionNotFoundError as error:
        raise HTTPException(status_code=404, detail="Next action not found.") from error
    except NextActionStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return NextActionResponse(**asdict(action))


def _next_actions(request: Request) -> NextActionService:
    return cast(NextActionService, request.app.state.next_actions)
