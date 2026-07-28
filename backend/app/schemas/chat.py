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


class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model: str | None
    created_at: datetime
    knowledge_checked: bool = False
    sources: list[ChatKnowledgeSource] = Field(default_factory=list)


class ChatConversationSummary(BaseModel):
    id: str
    title: str
    model: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatConversation(ChatConversationSummary):
    messages: list[ChatMessage]


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=120)


class SendChatMessageRequest(BaseModel):
    model: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
