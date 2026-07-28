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
        yield " Lyle."


class FailingProvider(FakeProvider):
    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        del model, messages
        raise LocalModelProviderError("The local model provider is unavailable.")
        yield


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
            "delta",
            "delta",
            "done",
        ]
        assert events[1]["content"] + events[2]["content"] == "Hello Lyle."

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
            ("assistant", "Hello Lyle."),
        ]


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

        assert [event["type"] for event in events] == ["user", "error"]
        assert events[-1]["message"] == (
            "The local model provider is unavailable."
        )
        conversation = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        assert conversation["message_count"] == 1
        assert conversation["messages"][0]["role"] == "user"


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
