import json
from collections.abc import Iterator, Sequence
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.chat import (
    LocalModelProviderError,
    ModelRecord,
    OllamaProvider,
)

INTENT = {"X-Nova-Intent": "local-user-action"}


class FakeProvider:
    def list_models(self) -> list[ModelRecord]:
        return [
            ModelRecord(
                name="qwen3:8b",
                size_bytes=5_225_388_164,
                parameter_size="8.2B",
                quantization_level="Q4_K_M",
            )
        ]

    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        assert model == "qwen3:8b"
        assert messages[-1] == {"role": "user", "content": "Hello Nova"}
        yield "Hello"
        yield " Example Owner."


class FailingProvider(FakeProvider):
    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        del model, messages
        raise LocalModelProviderError("The local model provider is unavailable.")
        yield


class DocumentProvider(FakeProvider):
    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        assert model == "qwen3:8b"
        assert messages[-1] == {"role": "user", "content": "What is the code?"}
        context = next(
            message["content"]
            for message in messages
            if "BEGIN UNTRUSTED LOCAL DOCUMENT D1" in message["content"]
        )
        assert "The delivery code is amber-42." in context
        assert "Verified SHA-256:" in context
        yield "The delivery code is amber-42 [D1]."


class CapabilityGuidanceProvider(FakeProvider):
    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        assert model == "qwen3:8b"
        assert messages[-1] == {
            "role": "user",
            "content": "I'm looking to improve you to assist me fully",
        }
        guidance = messages[0]["content"]
        assert "owner-approved local knowledge is checked for each turn" in guidance
        assert "explicit remember requests prepare editable local review cards" in guidance
        assert "one eligible local document" in guidance
        assert "Focus plus owner-entered next actions" in guidance
        assert "no web browsing, automatic document retrieval" in guidance
        assert "Never suggest a reminder, scheduled task" in guidance
        assert "conversation organisation" in guidance
        assert "Do not invent citation labels" in guidance
        assert "one-turn document selection" in guidance
        assert "never make a blanket claim" in guidance
        assert (
            "Tools, web access, and automatic document retrieval are not available."
            not in guidance
        )
        yield (
            "Start by adding your response-style preference through NOVA's "
            "review flow; I can already use approved local knowledge and an "
            "explicitly selected document."
        )


def _application(tmp_path: Path):
    return create_app(
        Settings(
            intake_path=tmp_path / "intake",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )


def test_local_chat_streams_and_persists_conversation(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = FakeProvider()

        models = client.get("/api/v1/chat/models")
        assert models.status_code == 200
        assert models.json() == [
            {
                "name": "qwen3:8b",
                "size_bytes": 5_225_388_164,
                "parameter_size": "8.2B",
                "quantization_level": "Q4_K_M",
            }
        ]

        denied = client.post(
            "/api/v1/chat/conversations",
            json={"title": "New conversation"},
        )
        assert denied.status_code == 403

        created = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "New conversation"},
        )
        assert created.status_code == 201
        conversation_id = created.json()["id"]

        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={"model": "qwen3:8b", "content": "Hello Nova"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        events = [json.loads(line) for line in response.text.splitlines()]
        assert [event["type"] for event in events] == [
            "user",
            "knowledge",
            "delta",
            "delta",
            "done",
        ]
        assert events[1] == {
            "type": "knowledge",
            "checked": True,
            "sources": [],
        }
        response_text = events[2]["content"] + events[3]["content"]
        assert response_text == "Hello Example Owner."

        conversation = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        )
        assert conversation.status_code == 200
        body = conversation.json()
        assert body["title"] == "Hello Nova"
        assert body["model"] == "qwen3:8b"
        assert body["message_count"] == 2
        assert [
            (message["role"], message["content"])
            for message in body["messages"]
        ] == [
            ("user", "Hello Nova"),
            ("assistant", "Hello Example Owner."),
        ]


def test_chat_receives_accurate_capability_guidance(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = CapabilityGuidanceProvider()
        conversation_id = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "New conversation"},
        ).json()["id"]

        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={
                "model": "qwen3:8b",
                "content": "I'm looking to improve you to assist me fully",
            },
        )

        assert response.status_code == 200
        events = [json.loads(line) for line in response.text.splitlines()]
        assert [event["type"] for event in events] == [
            "user",
            "knowledge",
            "delta",
            "done",
        ]
        assert "approved local knowledge" in events[2]["content"]


def test_provider_failure_is_streamed_without_inventing_reply(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = FailingProvider()
        created = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "New conversation"},
        )
        conversation_id = created.json()["id"]

        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={"model": "qwen3:8b", "content": "Hello Nova"},
        )
        events = [json.loads(line) for line in response.text.splitlines()]

        assert [event["type"] for event in events] == [
            "user",
            "knowledge",
            "error",
        ]
        assert events[-1]["message"] == (
            "The local model provider is unavailable."
        )
        conversation = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        assert conversation["message_count"] == 1
    assert conversation["messages"][0]["role"] == "user"


def test_conversation_lifecycle_is_guarded_audited_and_recoverable(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = FakeProvider()
        created = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "History"},
        ).json()
        conversation_id = created["id"]
        sent = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={"model": "qwen3:8b", "content": "Hello Nova"},
        )
        assert sent.status_code == 200

        denied = client.patch(
            f"/api/v1/chat/conversations/{conversation_id}",
            json={"title": "Private history"},
        )
        assert denied.status_code == 403
        renamed = client.patch(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=INTENT,
            json={"title": "Private history"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "Private history"

        archived = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/archive",
            headers=INTENT,
        )
        assert archived.status_code == 200
        assert archived.json()["archived_at"] is not None
        assert client.get("/api/v1/chat/conversations").json() == []
        assert [item["id"] for item in client.get(
            "/api/v1/chat/conversations?status=archived"
        ).json()] == [conversation_id]

        blocked = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={"model": "qwen3:8b", "content": "Hello Nova"},
        )
        assert blocked.status_code == 409
        restored = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/restore",
            headers=INTENT,
        )
        assert restored.status_code == 200

        trashed = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/trash",
            headers=INTENT,
        )
        assert trashed.status_code == 200
        assert trashed.json()["trashed_at"] is not None
        assert client.get("/api/v1/chat/conversations").json() == []
        assert [item["id"] for item in client.get(
            "/api/v1/chat/conversations?status=trash"
        ).json()] == [conversation_id]

        restored_from_trash = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/trash/restore",
            headers=INTENT,
        )
        assert restored_from_trash.status_code == 200
        body = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        assert body["message_count"] == 2
        assert [message["content"] for message in body["messages"]] == [
            "Hello Nova",
            "Hello Example Owner.",
        ]
        events = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/events"
        ).json()
        assert [event["event_type"] for event in events] == [
            "created",
            "renamed",
            "archived",
            "restored",
            "trashed",
            "restored_from_trash",
        ]


def test_invalid_conversation_lifecycle_transitions_do_not_write_events(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        conversation_id = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "Lifecycle"},
        ).json()["id"]
        conflict = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/restore",
            headers=INTENT,
        )
        assert conflict.status_code == 409
        events = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/events"
        ).json()
        assert [event["event_type"] for event in events] == ["created"]


def test_unexpected_prestream_failure_releases_conversation_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        conversation_id = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "Recovery"},
        ).json()["id"]

        def fail_retrieval(_query: str) -> None:
            raise RuntimeError("unexpected retrieval failure")

        monkeypatch.setattr(
            application.state.knowledge,
            "retrieve_approved",
            fail_retrieval,
        )
        with pytest.raises(RuntimeError, match="unexpected retrieval failure"):
            client.post(
                f"/api/v1/chat/conversations/{conversation_id}/messages",
                headers=INTENT,
                json={"model": "qwen3:8b", "content": "Hello Nova"},
            )

        archived = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/archive",
            headers=INTENT,
        )
        assert archived.status_code == 200


def test_explicit_document_context_is_verified_used_and_cited(
    tmp_path: Path,
) -> None:
    intake_path = tmp_path / "intake"
    intake_path.mkdir()
    document_path = intake_path / "delivery.txt"
    document_path.write_text(
        "The delivery code is amber-42.",
        encoding="utf-8",
    )
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = DocumentProvider()
        documents = client.get("/api/v1/chat/documents")
        assert documents.status_code == 200
        assert len(documents.json()) == 1
        document = documents.json()[0]
        assert document["original_name"] == "delivery.txt"
        assert "full_text" not in document
        assert "content" not in document

        created = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "New conversation"},
        )
        conversation_id = created.json()["id"]
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={
                "model": "qwen3:8b",
                "content": "What is the code?",
                "document_id": document["file_id"],
            },
        )
        assert response.status_code == 200
        events = [json.loads(line) for line in response.text.splitlines()]
        assert [event["type"] for event in events] == [
            "user",
            "knowledge",
            "document",
            "delta",
            "done",
        ]
        source = events[2]["source"]
        assert source["citation_label"] == "D1"
        assert source["original_name"] == "delivery.txt"
        assert "content" not in source

        conversation = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        assistant = conversation["messages"][-1]
        assert assistant["content"].endswith("[D1].")
        assert assistant["document_sources"] == [source]
        assert "content" not in assistant["document_sources"][0]


def test_document_change_is_rejected_before_user_message_is_saved(
    tmp_path: Path,
) -> None:
    intake_path = tmp_path / "intake"
    intake_path.mkdir()
    document_path = intake_path / "mutable.txt"
    document_path.write_text("Original verified text.", encoding="utf-8")
    application = _application(tmp_path)
    with TestClient(application) as client:
        document_id = client.get("/api/v1/chat/documents").json()[0]["file_id"]
        created = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "New conversation"},
        )
        conversation_id = created.json()["id"]
        document_path.write_text("Changed after indexing.", encoding="utf-8")

        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={
                "model": "qwen3:8b",
                "content": "Use this document",
                "document_id": document_id,
            },
        )
        assert response.status_code == 409
        assert "changed after indexing" in response.json()["detail"]
        conversation = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        assert conversation["message_count"] == 0


def test_ollama_provider_lists_models_and_streams_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            BytesIO(
                json.dumps(
                    {
                        "models": [
                            {
                                "name": "qwen3:8b",
                                "size": 5_225_388_164,
                                "details": {
                                    "parameter_size": "8.2B",
                                    "quantization_level": "Q4_K_M",
                                },
                            }
                        ]
                    }
                ).encode()
            ),
            BytesIO(
                b'{"message":{"content":"Hello"},"done":false}\n'
                b'{"message":{"content":" Nova"},"done":false}\n'
                b'{"done":true}\n'
            ),
        ]
    )
    monkeypatch.setattr(
        "app.services.chat.urlopen",
        lambda request, timeout: next(responses),
    )
    provider = OllamaProvider("http://127.0.0.1:11434/", 30)

    models = provider.list_models()
    chunks = list(
        provider.stream_chat(
            "qwen3:8b",
            [{"role": "user", "content": "Hello"}],
        )
    )

    assert models == [
        ModelRecord(
            name="qwen3:8b",
            size_bytes=5_225_388_164,
            parameter_size="8.2B",
            quantization_level="Q4_K_M",
        )
    ]
    assert chunks == ["Hello", " Nova"]


def test_missing_conversation_and_unavailable_model_provider_are_clear(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> BytesIO:
        raise OSError("provider offline")

    monkeypatch.setattr("app.services.chat.urlopen", unavailable)
    application = _application(tmp_path)
    with TestClient(application) as client:
        models = client.get("/api/v1/chat/models")
        missing = client.get("/api/v1/chat/conversations/missing")
        conversations = client.get("/api/v1/chat/conversations")

    assert models.status_code == 503
    assert models.json()["detail"] == "The local model provider is unavailable."
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Conversation not found."
    assert conversations.status_code == 200
    assert conversations.json() == []
