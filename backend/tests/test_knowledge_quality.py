import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

INTENT = {"X-Nova-Intent": "local-user-action"}


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


def _proposal(application, content: str):
    conversation = application.state.chat.create_conversation("Quality setup")
    message, _ = application.state.chat.begin_turn(
        conversation.id,
        f"Remember that {content}",
        "qwen3:8b",
    )
    candidate = application.state.knowledge.propose_from_message(message)
    assert candidate is not None
    return candidate


def _approve(
    client: TestClient,
    candidate_id: str,
    *,
    kind: str,
    title: str,
    content: str,
) -> dict:
    response = client.put(
        f"/api/v1/knowledge/candidates/{candidate_id}",
        headers=INTENT,
        json={
            "action": "approve",
            "kind": kind,
            "title": title,
            "content": content,
        },
    )
    assert response.status_code == 200, response.text
    return next(
        record
        for record in client.get("/api/v1/knowledge/records").json()
        if record["candidate_id"] == candidate_id
    )


def test_empty_quality_report_is_transparent_and_prioritised(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        response = client.get("/api/v1/knowledge/quality")

    assert response.status_code == 200
    report = response.json()
    assert report["completion_percent"] == 0
    assert report["freshness_percent"] == 0
    assert report["retrieval_percent"] == 0
    assert report["core_covered"] == 0
    assert report["core_total"] == 7
    assert report["retrieval_checked"] == 0
    assert all(requirement["status"] == "missing" for requirement in report["requirements"])
    assert report["requirements"][0]["title"] == "Preferred name"
    assert "does not measure or score the owner" in report["limitation"]


def test_all_requirements_expose_curated_privacy_safe_examples(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        report = client.get("/api/v1/knowledge/quality").json()

    requirements = {item["id"]: item for item in report["requirements"]}
    assert len(requirements) == 13
    assert all(len(item["examples"]) == 2 for item in requirements.values())
    assert all(item["prompt_starter"].startswith("Remember that") for item in requirements.values())
    assert all(
        example["draft"].startswith("Remember that")
        for item in requirements.values()
        for example in item["examples"]
    )
    example_copy = " ".join(
        example["text"] + " " + example["draft"]
        for item in requirements.values()
        for example in item["examples"]
    )
    assert not re.search(r"\b\d{6,}\b", example_copy)
    assert "@" not in example_copy
    assert (
        "account numbers, passwords, or other secrets"
        in requirements["financial-goals"]["suggestion"]
    )
    assert "exact address" in requirements["timezone-location"]["suggestion"]
    assert "unnecessary medical details" in requirements["health-preferences"]["suggestion"]
    assert "cannot send reminders yet" in requirements["vehicle-context"]["suggestion"]
    assert "cannot send reminders yet" in requirements["home-responsibilities"]["suggestion"]


def test_only_approved_active_records_count_toward_coverage(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        name = _proposal(application, "my preferred name is Example Owner")
        _approve(
            client,
            name.id,
            kind="fact",
            title="Preferred name",
            content="My preferred name is Example Owner.",
        )

        pending = _proposal(application, "my current project is still pending")
        assert pending.status == "pending"

        rejected = _proposal(application, "my current goal is rejected")
        rejected_response = client.put(
            f"/api/v1/knowledge/candidates/{rejected.id}",
            headers=INTENT,
            json={"action": "reject"},
        )
        assert rejected_response.status_code == 200

        retired_candidate = _proposal(
            application,
            "my current goal is complete the retirement test",
        )
        retired = _approve(
            client,
            retired_candidate.id,
            kind="goal",
            title="Retired current goal",
            content="My current goal is complete the retirement test.",
        )
        retired_response = client.put(
            f"/api/v1/knowledge/records/{retired['id']}",
            headers=INTENT,
            json={
                "action": "retire",
                "confirmation": f"RETIRE {retired['id'][:8]}",
            },
        )
        assert retired_response.status_code == 200

        report = client.get("/api/v1/knowledge/quality").json()

    requirements = {item["id"]: item for item in report["requirements"]}
    assert requirements["preferred-name"]["status"] == "covered"
    assert requirements["current-goals"]["status"] == "missing"
    assert requirements["active-projects"]["status"] == "missing"
    assert report["active_record_count"] == 1
    assert report["retired_record_count"] == 1


def test_stale_record_remains_covered_but_reduces_freshness(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(
            application,
            "my preferred name is Example Owner",
        )
        record = _approve(
            client,
            candidate.id,
            kind="fact",
            title="Preferred name",
            content="My preferred name is Example Owner.",
        )
        stale_at = (datetime.now(UTC) - timedelta(days=500)).isoformat()
        connection = sqlite3.connect(tmp_path / "nova.db")
        connection.execute(
            "UPDATE knowledge_records SET updated_at = ? WHERE id = ?",
            (stale_at, record["id"]),
        )
        connection.commit()
        connection.close()

        report = client.get("/api/v1/knowledge/quality").json()

    preferred_name = next(item for item in report["requirements"] if item["id"] == "preferred-name")
    assert preferred_name["status"] == "stale"
    assert report["core_covered"] == 1
    assert report["freshness_percent"] == 0


def test_guided_prompt_records_close_their_matching_gaps(tmp_path: Path) -> None:
    application = _application(tmp_path)
    cases = (
        (
            "response-style",
            "preference",
            "Prefer responses that are concise",
            "I prefer responses that are concise and direct.",
        ),
        (
            "work-context",
            "reference",
            "Work context",
            "My work context is weekday long-haul trucking.",
        ),
        (
            "technology-environment",
            "reference",
            "Main technology environment",
            "My main technology environment is Windows and Ollama.",
        ),
        (
            "home-responsibilities",
            "fact",
            "Current home responsibility",
            "My current home responsibility is appliance maintenance.",
        ),
        (
            "health-preferences",
            "preference",
            "Dietary preference",
            "My health or dietary preference is vegetarian food.",
        ),
    )

    with TestClient(application) as client:
        approved_records: dict[str, str] = {}
        for requirement_id, kind, title, content in cases:
            candidate = _proposal(application, content)
            record = _approve(
                client,
                candidate.id,
                kind=kind,
                title=title,
                content=content,
            )
            approved_records[requirement_id] = record["id"]

        report = client.get("/api/v1/knowledge/quality").json()

    requirements = {item["id"]: item for item in report["requirements"]}
    for requirement_id, record_id in approved_records.items():
        assert requirements[requirement_id]["status"] == "covered"
        assert record_id in requirements[requirement_id]["matched_record_ids"]


def test_retrieval_self_check_finds_verified_active_records(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(
            application,
            "the local verification phrase is cobalt sunrise",
        )
        _approve(
            client,
            candidate.id,
            kind="fact",
            title="Local verification phrase",
            content="The local verification phrase is cobalt sunrise.",
        )

        report = client.get("/api/v1/knowledge/quality").json()

    assert report["retrieval_total_records"] == 1
    assert report["retrieval_checked"] == 1
    assert report["retrieval_passed"] == 1
    assert report["retrieval_percent"] == 100
    assert report["retrieval_failures"] == []


def test_quality_report_fails_closed_when_active_file_is_tampered(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(
            application,
            "the integrity phrase is silver compass",
        )
        record = _approve(
            client,
            candidate.id,
            kind="fact",
            title="Integrity phrase",
            content="The integrity phrase is silver compass.",
        )
        path = tmp_path / "knowledge" / record["relative_path"]
        path.write_text("tampered", encoding="utf-8")

        response = client.get("/api/v1/knowledge/quality")

    assert response.status_code == 422
    assert "integrity check" in response.json()["detail"]


def test_quality_report_is_read_only_and_needs_no_mutation_header(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        database_path = tmp_path / "nova.db"
        before_database = database_path.read_bytes()
        response = client.get("/api/v1/knowledge/quality")
        after_database = database_path.read_bytes()

    assert response.status_code == 200
    assert after_database == before_database
    assert list((tmp_path / "knowledge").rglob("*")) == []
