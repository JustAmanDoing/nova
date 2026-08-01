from datetime import datetime

from pydantic import BaseModel, Field


class ChatModel(BaseModel):
    name: str
    size_bytes: int
    parameter_size: str | None = None
    quantization_level: str | None = None


class ChatKnowledgeSource(BaseModel):
    record_id: str
    citation_label: str
    title: str
    kind: str
    content: str
    relative_path: str
    sha256: str
    score: float


class ChatDocumentOption(BaseModel):
    file_id: str
    title: str
    original_name: str
    relative_path: str
    sha256: str
    document_type: str | None
    character_count: int
    understood_at: datetime


class ChatDocumentSource(BaseModel):
    file_id: str
    citation_label: str
    title: str
    original_name: str
    relative_path: str
    sha256: str
    document_type: str | None
    character_count: int


class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model: str | None
    created_at: datetime
    knowledge_checked: bool = False
    sources: list[ChatKnowledgeSource] = Field(default_factory=list)
    document_sources: list[ChatDocumentSource] = Field(default_factory=list)


class ChatConversationSummary(BaseModel):
    id: str
    title: str
    model: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int
    archived_at: datetime | None = None
    trashed_at: datetime | None = None


class ChatConversation(ChatConversationSummary):
    messages: list[ChatMessage]


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=120)


class RenameConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class ChatConversationEvent(BaseModel):
    id: str
    conversation_id: str
    event_type: str
    previous_title: str | None = None
    new_title: str | None = None
    previous_status: str | None = None
    new_status: str | None = None
    created_at: datetime


class SendChatMessageRequest(BaseModel):
    model: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
    document_id: str | None = Field(default=None, min_length=1, max_length=200)
