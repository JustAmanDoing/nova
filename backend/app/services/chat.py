import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


class ChatNotFoundError(LookupError):
    """Raised when a requested local conversation does not exist."""


class LocalModelProviderError(RuntimeError):
    """Raised when the configured local model provider cannot complete a request."""


@dataclass(frozen=True)
class ModelRecord:
    name: str
    size_bytes: int
    parameter_size: str | None
    quantization_level: str | None


@dataclass(frozen=True)
class MessageRecord:
    id: str
    conversation_id: str
    role: str
    content: str
    model: str | None
    created_at: str


@dataclass(frozen=True)
class ConversationRecord:
    id: str
    title: str
    model: str | None
    created_at: str
    updated_at: str
    message_count: int
    messages: tuple[MessageRecord, ...] = ()


class OllamaProvider:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def list_models(self) -> list[ModelRecord]:
        payload = self._request_json("/api/tags")
        models = payload.get("models")
        if not isinstance(models, list):
            raise LocalModelProviderError(
                "The local model provider returned an invalid model list."
            )
        records: list[ModelRecord] = []
        for item in models:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            details = item.get("details")
            detail_map = details if isinstance(details, dict) else {}
            size = item.get("size")
            records.append(
                ModelRecord(
                    name=item["name"],
                    size_bytes=int(size) if isinstance(size, int) else 0,
                    parameter_size=_optional_string(detail_map.get("parameter_size")),
                    quantization_level=_optional_string(
                        detail_map.get("quantization_level")
                    ),
                )
            )
        return sorted(records, key=lambda model: model.name.casefold())

    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(
                {
                    "model": model,
                    "messages": list(messages),
                    "stream": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    payload = json.loads(line)
                    if not isinstance(payload, dict):
                        continue
                    error = payload.get("error")
                    if isinstance(error, str) and error:
                        raise LocalModelProviderError(error)
                    message = payload.get("message")
                    if isinstance(message, dict):
                        content = message.get("content")
                        if isinstance(content, str) and content:
                            yield content
                    if payload.get("done") is True:
                        return
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise LocalModelProviderError(
                "The local model provider is unavailable or returned an invalid response."
            ) from error

    def _request_json(self, path: str) -> dict[str, object]:
        try:
            with urlopen(
                f"{self.base_url}{path}",
                timeout=self.timeout_seconds,
            ) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise LocalModelProviderError(
                "The local model provider is unavailable."
            ) from error
        if not isinstance(payload, dict):
            raise LocalModelProviderError(
                "The local model provider returned an invalid response."
            )
        return payload


class ChatService:
    def __init__(self, database_path: Path, provider: OllamaProvider) -> None:
        self.database_path = database_path
        self.provider = provider

    def list_models(self) -> list[ModelRecord]:
        return self.provider.list_models()

    def create_conversation(self, title: str) -> ConversationRecord:
        conversation_id = str(uuid4())
        now = _now()
        with closing(self._connection()) as connection, connection:
            connection.execute(
                """
                INSERT INTO chat_conversations (
                    id, title, model, created_at, updated_at
                ) VALUES (?, ?, NULL, ?, ?)
                """,
                (conversation_id, title.strip(), now, now),
            )
        return ConversationRecord(
            id=conversation_id,
            title=title.strip(),
            model=None,
            created_at=now,
            updated_at=now,
            message_count=0,
        )

    def list_conversations(self) -> list[ConversationRecord]:
        with closing(self._connection()) as connection:
            rows = connection.execute(
                """
                SELECT
                    conversation.id,
                    conversation.title,
                    conversation.model,
                    conversation.created_at,
                    conversation.updated_at,
                    COUNT(message.id) AS message_count
                FROM chat_conversations AS conversation
                LEFT JOIN chat_messages AS message
                  ON message.conversation_id = conversation.id
                GROUP BY conversation.id
                ORDER BY conversation.updated_at DESC
                """
            ).fetchall()
        return [_conversation_from_row(row) for row in rows]

    def get_conversation(self, conversation_id: str) -> ConversationRecord:
        with closing(self._connection()) as connection:
            row = connection.execute(
                """
                SELECT
                    conversation.id,
                    conversation.title,
                    conversation.model,
                    conversation.created_at,
                    conversation.updated_at,
                    COUNT(message.id) AS message_count
                FROM chat_conversations AS conversation
                LEFT JOIN chat_messages AS message
                  ON message.conversation_id = conversation.id
                WHERE conversation.id = ?
                GROUP BY conversation.id
                """,
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise ChatNotFoundError(conversation_id)
            messages = connection.execute(
                """
                SELECT id, conversation_id, role, content, model, created_at
                FROM chat_messages
                WHERE conversation_id = ?
                ORDER BY created_at, id
                """,
                (conversation_id,),
            ).fetchall()
        conversation = _conversation_from_row(row)
        return ConversationRecord(
            **{
                **conversation.__dict__,
                "messages": tuple(_message_from_row(message) for message in messages),
            }
        )

    def begin_turn(
        self,
        conversation_id: str,
        content: str,
        model: str,
    ) -> tuple[MessageRecord, list[dict[str, str]]]:
        conversation = self.get_conversation(conversation_id)
        message = self._add_message(conversation_id, "user", content.strip(), model)
        history = [
            {"role": previous.role, "content": previous.content}
            for previous in conversation.messages
        ]
        history.append({"role": "user", "content": message.content})
        if conversation.message_count == 0 and conversation.title == "New conversation":
            self._set_title(conversation_id, _suggest_title(message.content))
        return message, history

    def complete_turn(
        self,
        conversation_id: str,
        content: str,
        model: str,
    ) -> MessageRecord:
        return self._add_message(conversation_id, "assistant", content, model)

    def _add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        model: str,
    ) -> MessageRecord:
        message_id = str(uuid4())
        now = _now()
        with closing(self._connection()) as connection, connection:
            exists = connection.execute(
                "SELECT 1 FROM chat_conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if exists is None:
                raise ChatNotFoundError(conversation_id)
            connection.execute(
                """
                INSERT INTO chat_messages (
                    id, conversation_id, role, content, model, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, conversation_id, role, content, model, now),
            )
            connection.execute(
                """
                UPDATE chat_conversations
                SET model = ?, updated_at = ?
                WHERE id = ?
                """,
                (model, now, conversation_id),
            )
        return MessageRecord(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            created_at=now,
        )

    def _set_title(self, conversation_id: str, title: str) -> None:
        with closing(self._connection()) as connection, connection:
            connection.execute(
                "UPDATE chat_conversations SET title = ? WHERE id = ?",
                (title, conversation_id),
            )

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _conversation_from_row(row: sqlite3.Row) -> ConversationRecord:
    return ConversationRecord(
        id=str(row["id"]),
        title=str(row["title"]),
        model=str(row["model"]) if row["model"] is not None else None,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        message_count=int(row["message_count"]),
    )


def _message_from_row(row: sqlite3.Row) -> MessageRecord:
    return MessageRecord(
        id=str(row["id"]),
        conversation_id=str(row["conversation_id"]),
        role=str(row["role"]),
        content=str(row["content"]),
        model=str(row["model"]) if row["model"] is not None else None,
        created_at=str(row["created_at"]),
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _suggest_title(content: str) -> str:
    compact = " ".join(content.split())
    if len(compact) <= 60:
        return compact
    return f"{compact[:57].rstrip()}..."


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None
