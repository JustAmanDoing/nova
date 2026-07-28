import hashlib
import json
from collections.abc import Iterator, Sequence
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.chat import ModelRecord
from app.services.knowledge import KnowledgeProposalError

INTENT = {"X-Nova-Intent": "local-user-action"}


class MemoryProvider:
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
        assert messages[0]["role"] == "system"
        assert "nothing becomes permanent" in messages[0]["content"]
        yield (
            "I prepared a local review card. Nothing is saved unless you approve it."
        )


def _application(tmp_path: Path):
    return create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            knowledge_path=tmp_path / "knowledge",
            intake_scan_seconds=60,
        )
    )


def _conversation(client: TestClient) -> str:
    response = client.post(
        "/api/v1/chat/conversations",
        headers=INTENT,
        json={"title": "New conversation"},
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def _send(client: TestClient, conversation_id: str, content: str) -> list[dict]:
    response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=INTENT,
        json={"model": "qwen3:8b", "content": content},
    )
    assert response.status_code == 200
    return [json.loads(line) for line in response.text.splitlines()]


def test_explicit_remember_request_requires_review_before_local_record(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = MemoryProvider()
        conversation_id = _conversation(client)
        events = _send(
            client,
            conversation_id,
            "Remember that I prefer short and direct answers.",
        )

        assert events[-1]["type"] == "done"
        candidates = client.get(
            "/api/v1/knowledge/candidates?status=pending"
        ).json()
        assert len(candidates) == 1
        candidate = candidates[0]
        assert candidate["conversation_id"] == conversation_id
        assert candidate["kind"] == "preference"
        assert candidate["content"] == "I prefer short and direct answers"
        assert candidate["explicit_request"] is True
        assert candidate["status"] == "pending"
        assert list((tmp_path / "knowledge").rglob("*.md")) == []

        denied = client.put(
            f"/api/v1/knowledge/candidates/{candidate['id']}",
            json={
                "action": "approve",
                "kind": "preference",
                "title": "Response style",
                "content": "I prefer concise answers with clear recommendations.",
            },
        )
        assert denied.status_code == 403

        approved = client.put(
            f"/api/v1/knowledge/candidates/{candidate['id']}",
            headers=INTENT,
            json={
                "action": "approve",
                "kind": "preference",
                "title": "Response style",
                "content": "I prefer concise answers with clear recommendations.",
            },
        )
        assert approved.status_code == 200
        approved_body = approved.json()
        assert approved_body["status"] == "approved"
        assert approved_body["record_path"].startswith("Preferences/")

        record_path = tmp_path / "knowledge" / approved_body["record_path"]
        record_bytes = record_path.read_bytes()
        record_text = record_bytes.decode("utf-8")
        assert "# Response style" in record_text
        assert "owner_approved: true" in record_text
        assert "I prefer concise answers with clear recommendations." in record_text

        records = client.get("/api/v1/knowledge/records").json()
        assert len(records) == 1
        assert records[0]["relative_path"] == approved_body["record_path"]
        assert records[0]["sha256"] == hashlib.sha256(record_bytes).hexdigest()

        repeated = client.put(
            f"/api/v1/knowledge/candidates/{candidate['id']}",
            headers=INTENT,
            json={
                "action": "approve",
                "kind": "preference",
                "title": "Response style",
                "content": "Duplicate attempt",
            },
        )
        assert repeated.status_code == 409
        assert len(list((tmp_path / "knowledge").rglob("*.md"))) == 1


def test_high_value_suggestion_can_be_rejected_without_writing(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = MemoryProvider()
        conversation_id = _conversation(client)
        _send(client, conversation_id, "My long-term goal is to finish Nova")

        candidate = client.get(
            "/api/v1/knowledge/candidates?status=pending"
        ).json()[0]
        assert candidate["kind"] == "goal"
        assert candidate["explicit_request"] is False
        assert candidate["reason"] == (
            "This looks like a personal goal that may be useful over time."
        )

        rejected = client.put(
            f"/api/v1/knowledge/candidates/{candidate['id']}",
            headers=INTENT,
            json={"action": "reject"},
        )
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"
        assert client.get("/api/v1/knowledge/records").json() == []
        assert list((tmp_path / "knowledge").rglob("*.md")) == []


def test_ordinary_conversation_does_not_create_a_knowledge_proposal(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = MemoryProvider()
        conversation_id = _conversation(client)
        _send(client, conversation_id, "What is the weather usually like in July?")

        assert client.get("/api/v1/knowledge/candidates").json() == []


def test_age_suggestion_is_dated_instead_of_stored_as_timeless_fact(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = MemoryProvider()
        conversation_id = _conversation(client)
        _send(client, conversation_id, "I am a man who is 45 years old")

        candidate = client.get(
            "/api/v1/knowledge/candidates?status=pending"
        ).json()[0]
        assert candidate["kind"] == "fact"
        assert "stated 2026-" in candidate["content"]
        assert candidate["explicit_request"] is False


def test_existing_record_path_is_never_overwritten(
    tmp_path: Path,
    monkeypatch,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = MemoryProvider()
        conversation_id = _conversation(client)
        _send(client, conversation_id, "Remember that my home city is Brisbane.")
        candidate = client.get(
            "/api/v1/knowledge/candidates?status=pending"
        ).json()[0]

        relative = Path("Facts/existing.md")
        existing = tmp_path / "knowledge" / relative
        existing.parent.mkdir(parents=True)
        existing.write_text("authoritative existing record", encoding="utf-8")
        monkeypatch.setattr(
            application.state.knowledge,
            "_relative_record_path",
            lambda *_args: relative,
        )

        response = client.put(
            f"/api/v1/knowledge/candidates/{candidate['id']}",
            headers=INTENT,
            json={
                "action": "approve",
                "kind": "fact",
                "title": "Home city",
                "content": "My home city is Brisbane.",
            },
        )
        assert response.status_code == 422
        assert existing.read_text(encoding="utf-8") == "authoritative existing record"
        assert client.get("/api/v1/knowledge/records").json() == []


def test_knowledge_proposal_failure_warns_without_breaking_chat(
    tmp_path: Path,
    monkeypatch,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        application.state.chat.provider = MemoryProvider()
        monkeypatch.setattr(
            application.state.knowledge,
            "propose_from_message",
            lambda _message: (_ for _ in ()).throw(
                KnowledgeProposalError(
                    "Chat is available, but memory review is unavailable."
                )
            ),
        )
        conversation_id = _conversation(client)
        events = _send(
            client,
            conversation_id,
            "Remember that this warning is synthetic.",
        )

        assert [event["type"] for event in events] == [
            "user",
            "knowledge_warning",
            "delta",
            "done",
        ]
        assert events[1]["message"] == (
            "Chat is available, but memory review is unavailable."
        )
        conversation = client.get(
            f"/api/v1/chat/conversations/{conversation_id}"
        ).json()
        assert conversation["message_count"] == 2
