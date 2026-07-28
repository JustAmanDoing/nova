from datetime import datetime

from pydantic import BaseModel, Field


class ChatModel(BaseModel):
    name: str
    size_bytes: int
    parameter_size: str | None = None
    quantization_level: str | None = None


class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model: str | None
    created_at: datetime


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
