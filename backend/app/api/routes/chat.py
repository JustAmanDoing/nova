import asyncio
import json
from collections.abc import Iterator
from dataclasses import asdict
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import require_local_action
from app.schemas.chat import (
    ChatConversation,
    ChatConversationSummary,
    ChatModel,
    CreateConversationRequest,
    SendChatMessageRequest,
)
from app.services.chat import (
    ChatNotFoundError,
    ChatService,
    LocalModelProviderError,
)
from app.services.knowledge import KnowledgeProposalError

router = APIRouter(prefix="/chat", tags=["chat"])
LocalAction = Annotated[None, Depends(require_local_action)]


@router.get("/models", response_model=list[ChatModel])
async def list_models(request: Request) -> list[ChatModel]:
    chat = _chat(request)
    try:
        records = await asyncio.to_thread(chat.list_models)
    except LocalModelProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return [ChatModel(**asdict(record)) for record in records]


@router.get(
    "/conversations",
    response_model=list[ChatConversationSummary],
)
async def list_conversations(request: Request) -> list[ChatConversationSummary]:
    records = await asyncio.to_thread(_chat(request).list_conversations)
    return [ChatConversationSummary(**asdict(record)) for record in records]


@router.post(
    "/conversations",
    response_model=ChatConversationSummary,
    status_code=201,
)
async def create_conversation(
    payload: CreateConversationRequest,
    request: Request,
    _local_action: LocalAction,
) -> ChatConversationSummary:
    record = await asyncio.to_thread(
        _chat(request).create_conversation,
        payload.title,
    )
    return ChatConversationSummary(**asdict(record))


@router.get(
    "/conversations/{conversation_id}",
    response_model=ChatConversation,
)
async def get_conversation(
    conversation_id: str,
    request: Request,
) -> ChatConversation:
    try:
        record = await asyncio.to_thread(
            _chat(request).get_conversation,
            conversation_id,
        )
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    return ChatConversation(**asdict(record))


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: str,
    payload: SendChatMessageRequest,
    request: Request,
    _local_action: LocalAction,
) -> StreamingResponse:
    chat = _chat(request)
    try:
        user_message, history = chat.begin_turn(
            conversation_id,
            payload.content,
            payload.model,
        )
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    knowledge_warning: str | None = None
    try:
        request.app.state.knowledge.propose_from_message(user_message)
    except KnowledgeProposalError as error:
        knowledge_warning = str(error)

    def events() -> Iterator[str]:
        yield _event("user", message=asdict(user_message))
        if knowledge_warning is not None:
            yield _event("knowledge_warning", message=knowledge_warning)
        assistant_parts: list[str] = []
        try:
            for content in chat.provider.stream_chat(payload.model, history):
                assistant_parts.append(content)
                yield _event("delta", content=content)
            assistant = chat.complete_turn(
                conversation_id,
                "".join(assistant_parts),
                payload.model,
            )
            yield _event("done", message=asdict(assistant))
        except LocalModelProviderError as error:
            yield _event("error", message=str(error))

    return StreamingResponse(events(), media_type="application/x-ndjson")


def _chat(request: Request) -> ChatService:
    return cast(ChatService, request.app.state.chat)


def _event(kind: str, **payload: object) -> str:
    return json.dumps({"type": kind, **payload}, separators=(",", ":")) + "\n"
