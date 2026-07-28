import json
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.chat import ModelRecord
from app.services.knowledge import KnowledgeRetrievalError

INTENT = {"X-Nova-Intent": "local-user-action"}


class CapturingProvider:
    def __init__(self, reply: str = "The answer is amber lighthouse [K1].") -> None:
        self.reply = reply
        self.messages: list[dict[str, str]] = []

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
        self.messages = list(messages)
        yield self.reply


def _application(tmp_path: Path):
    return create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            knowledge_path=tmp_path / "knowledge",
            intake_scan_seconds=60,
            ocr_enabled=False,
        )
    )


def _approved_record(application, *, title: str, content: str):
    conversation = application.state.chat.create_conversation("Knowledge setup")
    message, _ = application.state.chat.begin_turn(
        conversation.id,
        f"Remember that {content}",
        "qwen3:8b",
    )
    candidate = application.state.knowledge.propose_from_message(message)
    assert candidate is not None
    application.state.knowledge.approve_candidate(
        candidate.id,
        "fact",
        title,
        content,
    )
    return application.state.knowledge.list_records()[0]


def test_retrieval_uses_only_approved_checksum_verified_records(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application):
        approved = _approved_record(
            application,
            title="Automated approval phrase",
            content="The automated approval phrase is amber lighthouse.",
        )

        pending_conversation = application.state.chat.create_conversation("Pending")
        pending_message, _ = application.state.chat.begin_turn(
            pending_conversation.id,
            "Remember that the automated approval phrase is unapproved violet.",
            "qwen3:8b",
        )
        pending = application.state.knowledge.propose_from_message(pending_message)
        assert pending is not None

        matches = application.state.knowledge.retrieve_approved(
            "What is the automated approval phrase?"
        )

        assert len(matches) == 1
        assert matches[0].record_id == approved.id
        assert matches[0].citation_label == "K1"
        assert matches[0].content == (
            "The automated approval phrase is amber lighthouse."
        )
        assert "unapproved violet" not in matches[0].content

        application.state.knowledge.reject_candidate(pending.id)
        after_rejection = application.state.knowledge.retrieve_approved(
            "What is the automated approval phrase?"
        )
        assert [source.record_id for source in after_rejection] == [approved.id]


def test_retrieval_no_match_and_synonym_normalization(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application):
        _approved_record(
            application,
            title="Preferred answer style",
            content="I prefer short answers.",
        )

        matched = application.state.knowledge.retrieve_approved(
            "What is my preference for replies?"
        )
        missing = application.state.knowledge.retrieve_approved(
            "What fruit should I buy?"
        )

        assert [source.title for source in matched] == ["Preferred answer style"]
        assert missing == []


def test_retrieval_fails_closed_when_record_file_is_tampered(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application):
        record = _approved_record(
            application,
            title="Integrity phrase",
            content="The integrity phrase is silver harbor.",
        )
        record_path = application.state.settings.knowledge_path / record.relative_path
        record_path.write_text("tampered", encoding="utf-8")

        with pytest.raises(KnowledgeRetrievalError, match="integrity check"):
            application.state.knowledge.retrieve_approved(
                "What is the integrity phrase?"
            )


def test_chat_streams_and_persists_exact_approved_citation(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        _approved_record(
            application,
            title="Automated approval phrase",
            content="The automated approval phrase is amber lighthouse.",
        )
        provider = CapturingProvider()
        application.state.chat.provider = provider
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
                "content": "What is the automated approval phrase?",
            },
        )

        events = [json.loads(line) for line in response.text.splitlines()]
        assert [event["type"] for event in events] == [
            "user",
            "knowledge",
            "delta",
            "done",
        ]
        source = events[1]["sources"][0]
        assert source["citation_label"] == "K1"
        assert source["relative_path"].endswith(".md")
        assert "[K1] Automated approval phrase" in provider.messages[-2]["content"]
        assert provider.messages[-1] == {
            "role": "user",
            "content": "What is the automated approval phrase?",
        }

        assistant = events[-1]["message"]
        assert assistant["knowledge_checked"] is True
        assert assistant["sources"] == [source]

        stored = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        stored_assistant = stored["messages"][-1]
        assert stored_assistant["knowledge_checked"] is True
        assert stored_assistant["sources"] == [source]


def test_chat_records_clear_no_match_without_inventing_source(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        provider = CapturingProvider(reply="No approved knowledge matched.")
        application.state.chat.provider = provider
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
                "content": "What is my favourite fruit?",
            },
        )

        events = [json.loads(line) for line in response.text.splitlines()]
        assert events[1] == {
            "type": "knowledge",
            "checked": True,
            "sources": [],
        }
        assert "no approved record matched" in provider.messages[-2]["content"]
        assistant = events[-1]["message"]
        assert assistant["knowledge_checked"] is True
        assert assistant["sources"] == []
