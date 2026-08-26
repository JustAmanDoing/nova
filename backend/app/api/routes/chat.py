import asyncio
import json
import logging
from collections.abc import Callable, Iterator
from dataclasses import asdict
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import require_local_action
from app.schemas.chat import (
    ChatConversation,
    ChatConversationEvent,
    ChatConversationSummary,
    ChatDocumentOption,
    ChatModel,
    CreateConversationRequest,
    RenameConversationRequest,
    SendChatMessageRequest,
)
from app.schemas.conductor import ConductorCapabilityResponse
from app.services.chat import (
    ChatConflictError,
    ChatNotFoundError,
    ChatService,
    ConversationRecord,
    DocumentContextError,
    KnowledgeSourceRecord,
    LocalModelProviderError,
    MessageRecord,
)
from app.services.conductor import ConductorService
from app.services.knowledge import (
    KnowledgeProposalError,
    KnowledgeRetrievalError,
)
from app.services.timesheet import TimesheetIntent, TimesheetService

router = APIRouter(prefix="/chat", tags=["chat"])
LocalAction = Annotated[None, Depends(require_local_action)]
logger = logging.getLogger(__name__)


@router.get("/capabilities", response_model=list[ConductorCapabilityResponse])
async def list_capabilities(request: Request) -> list[ConductorCapabilityResponse]:
    return [
        ConductorCapabilityResponse(
            id=record.id,
            label=record.label,
            description=record.description,
            prompt=record.prompt,
            source_title=record.source_title,
            source_url=record.source_url,
        )
        for record in _conductor(request).capabilities()
    ]


@router.get("/models", response_model=list[ChatModel])
async def list_models(request: Request) -> list[ChatModel]:
    chat = _chat(request)
    try:
        records = await asyncio.to_thread(chat.list_models)
    except LocalModelProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return [ChatModel(**asdict(record)) for record in records]


@router.get("/documents", response_model=list[ChatDocumentOption])
async def list_documents(request: Request) -> list[ChatDocumentOption]:
    records = await asyncio.to_thread(_chat(request).list_context_documents)
    return [ChatDocumentOption(**asdict(record)) for record in records]


@router.get(
    "/conversations",
    response_model=list[ChatConversationSummary],
)
async def list_conversations(
    request: Request,
    status: Literal["active", "archived", "trash", "all"] = "active",
) -> list[ChatConversationSummary]:
    records = await asyncio.to_thread(_chat(request).list_conversations, status)
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


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ChatConversationSummary,
)
async def rename_conversation(
    conversation_id: str,
    payload: RenameConversationRequest,
    request: Request,
    _local_action: LocalAction,
) -> ChatConversationSummary:
    return await _conversation_change(
        _chat(request).rename_conversation,
        conversation_id,
        payload.title,
    )


@router.post(
    "/conversations/{conversation_id}/archive",
    response_model=ChatConversationSummary,
)
async def archive_conversation(
    conversation_id: str,
    request: Request,
    _local_action: LocalAction,
) -> ChatConversationSummary:
    return await _conversation_change(
        _chat(request).archive_conversation, conversation_id
    )


@router.post(
    "/conversations/{conversation_id}/restore",
    response_model=ChatConversationSummary,
)
async def restore_conversation(
    conversation_id: str,
    request: Request,
    _local_action: LocalAction,
) -> ChatConversationSummary:
    return await _conversation_change(
        _chat(request).restore_conversation, conversation_id
    )


@router.post(
    "/conversations/{conversation_id}/trash",
    response_model=ChatConversationSummary,
)
async def trash_conversation(
    conversation_id: str,
    request: Request,
    _local_action: LocalAction,
) -> ChatConversationSummary:
    return await _conversation_change(
        _chat(request).trash_conversation, conversation_id
    )


@router.post(
    "/conversations/{conversation_id}/trash/restore",
    response_model=ChatConversationSummary,
)
async def restore_conversation_from_trash(
    conversation_id: str,
    request: Request,
    _local_action: LocalAction,
) -> ChatConversationSummary:
    return await _conversation_change(
        _chat(request).restore_from_trash, conversation_id
    )


@router.get(
    "/conversations/{conversation_id}/events",
    response_model=list[ChatConversationEvent],
)
async def list_conversation_events(
    conversation_id: str,
    request: Request,
) -> list[ChatConversationEvent]:
    try:
        records = await asyncio.to_thread(
            _chat(request).list_conversation_events, conversation_id
        )
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    return [ChatConversationEvent(**asdict(record)) for record in records]


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: str,
    payload: SendChatMessageRequest,
    request: Request,
    _local_action: LocalAction,
) -> StreamingResponse:
    chat = _chat(request)
    conductor = _conductor(request)
    timesheet = _timesheet(request)
    try:
        latest_capability_id = chat.latest_assistant_capability_id(conversation_id)
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    pending_timesheet_field: Literal["odometer_finish"] | None = (
        "odometer_finish"
        if latest_capability_id == "timesheet.awaiting_odometer_finish"
        else None
    )
    timesheet_intent = timesheet.match(
        payload.content,
        pending_field=pending_timesheet_field,
    )
    capability_id = (
        conductor.match(payload.content)
        if payload.document_id is None and timesheet_intent is None
        else None
    )
    if capability_id is None and timesheet_intent is None and payload.model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Local AI is unavailable. The listed NOVA status requests still work "
                "without it."
            ),
        )
    document = None
    if payload.document_id is not None and timesheet_intent is None:
        try:
            document = chat.prepare_document_context(payload.document_id)
        except DocumentContextError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
    try:
        user_message, history = chat.begin_turn(
            conversation_id,
            payload.content,
            payload.model,
        )
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except ChatConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if timesheet_intent is not None:
        return _timesheet_response(
            chat,
            timesheet,
            conversation_id,
            timesheet_intent,
            user_message,
        )
    if capability_id is not None:
        return _conductor_response(
            chat,
            conductor,
            conversation_id,
            capability_id,
            user_message,
        )
    model = cast(str, payload.model)
    try:
        knowledge_warnings: list[str] = []
        knowledge_checked = False
        knowledge_sources: list[KnowledgeSourceRecord] = []
        try:
            knowledge_sources = request.app.state.knowledge.retrieve_approved(
                user_message.content
            )
            history = chat.add_approved_knowledge_context(history, knowledge_sources)
            knowledge_checked = True
        except KnowledgeRetrievalError as error:
            knowledge_warnings.append(str(error))
        if document is not None:
            history = chat.add_document_context(history, document)
        try:
            request.app.state.knowledge.propose_from_message(user_message)
        except KnowledgeProposalError as error:
            knowledge_warnings.append(str(error))
    except Exception:
        chat.end_turn(conversation_id)
        raise

    def events() -> Iterator[str]:
        yield _event("user", message=asdict(user_message))
        if knowledge_checked:
            yield _event(
                "knowledge",
                checked=True,
                sources=[asdict(source) for source in knowledge_sources],
            )
        if document is not None:
            yield _event(
                "document",
                source=asdict(document.source),
            )
        for knowledge_warning in knowledge_warnings:
            yield _event("knowledge_warning", message=knowledge_warning)
        assistant_parts: list[str] = []
        try:
            for content in chat.provider.stream_chat(model, history):
                assistant_parts.append(content)
                yield _event("delta", content=content)
            assistant = chat.complete_turn(
                conversation_id,
                "".join(assistant_parts),
                model,
                knowledge_checked=knowledge_checked,
                sources=knowledge_sources,
                document_sources=(
                    [document.source] if document is not None else []
                ),
            )
            yield _event("done", message=asdict(assistant))
        except LocalModelProviderError as error:
            yield _event("error", message=str(error))
        finally:
            chat.end_turn(conversation_id)

    return StreamingResponse(events(), media_type="application/x-ndjson")


def _chat(request: Request) -> ChatService:
    return cast(ChatService, request.app.state.chat)


def _conductor(request: Request) -> ConductorService:
    return cast(ConductorService, request.app.state.conductor)


def _timesheet(request: Request) -> TimesheetService:
    return cast(TimesheetService, request.app.state.timesheets)


def _timesheet_response(
    chat: ChatService,
    timesheet: TimesheetService,
    conversation_id: str,
    intent: TimesheetIntent,
    user_message: MessageRecord,
) -> StreamingResponse:
    def events() -> Iterator[str]:
        yield _event("user", message=asdict(user_message))
        try:
            result = timesheet.execute(intent)
            yield _event("capability", source=asdict(result.source))
            yield _event("delta", content=result.content)
            assistant = chat.complete_turn(
                conversation_id,
                result.content,
                None,
                capability_sources=[result.source],
            )
            yield _event("done", message=asdict(assistant))
        except Exception:
            logger.exception("Structured timesheet operation failed")
            yield _event(
                "error",
                message=(
                    "NOVA could not update the timesheet right now. "
                    "No unconfirmed value was saved."
                ),
            )
        finally:
            chat.end_turn(conversation_id)

    return StreamingResponse(events(), media_type="application/x-ndjson")


def _conductor_response(
    chat: ChatService,
    conductor: ConductorService,
    conversation_id: str,
    capability_id: str,
    user_message: MessageRecord,
) -> StreamingResponse:
    def events() -> Iterator[str]:
        yield _event("user", message=asdict(user_message))
        try:
            result = conductor.execute(capability_id)
            yield _event("capability", source=asdict(result.source))
            yield _event("delta", content=result.content)
            assistant = chat.complete_turn(
                conversation_id,
                result.content,
                None,
                capability_sources=[result.source],
            )
            yield _event("done", message=asdict(assistant))
        except Exception:
            logger.exception("Conductor capability %s failed", capability_id)
            yield _event(
                "error",
                message=(
                    "NOVA could not read that local capability right now. "
                    "Nothing was changed."
                ),
            )
        finally:
            chat.end_turn(conversation_id)

    return StreamingResponse(events(), media_type="application/x-ndjson")


async def _conversation_change(
    operation: Callable[..., ConversationRecord],
    conversation_id: str,
    *args: object,
) -> ChatConversationSummary:
    try:
        record = await asyncio.to_thread(operation, conversation_id, *args)
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except ChatConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ChatConversationSummary(**asdict(record))


def _event(kind: str, **payload: object) -> str:
    return json.dumps({"type": kind, **payload}, separators=(",", ":")) + "\n"
