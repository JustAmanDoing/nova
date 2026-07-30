import hashlib
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


def _approve(
    application,
    client: TestClient,
    *,
    kind: str,
    title: str,
    content: str,
) -> dict:
    conversation = application.state.chat.create_conversation("Planning setup")
    message, _ = application.state.chat.begin_turn(
        conversation.id,
        f"Remember that {content}",
        "qwen3:8b",
    )
    candidate = application.state.knowledge.propose_from_message(message)
    assert candidate is not None
    response = client.put(
        f"/api/v1/knowledge/candidates/{candidate.id}",
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
        if record["candidate_id"] == candidate.id
    )


def test_empty_planning_overview_is_truthful_and_read_only(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        response = client.get("/api/v1/knowledge/planning")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    overview = response.json()
    assert overview["projects"] == []
    assert overview["goals"] == []
    assert overview["excluded_unverified_count"] == 0
    assert overview["warning"] is None
    assert "does not infer progress" in overview["limitation"]


def test_planning_overview_separates_verified_projects_and_goals(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        project = _approve(
            application,
            client,
            kind="project",
            title="Build NOVA",
            content="My active project is building NOVA.",
        )
        goal = _approve(
            application,
            client,
            kind="goal",
            title="Daily-use prototype",
            content="My current goal is a reliable daily-use prototype.",
        )
        _approve(
            application,
            client,
            kind="fact",
            title="Unrelated fact",
            content="The unrelated verification phrase is quiet lantern.",
        )

        overview = client.get("/api/v1/knowledge/planning").json()

    assert [item["id"] for item in overview["projects"]] == [project["id"]]
    assert [item["id"] for item in overview["goals"]] == [goal["id"]]
    for item in overview["projects"] + overview["goals"]:
        assert item["review_state"] == "current"
        assert item["revision"] == 1
        assert item["review_due_at"] > item["updated_at"]
        assert set(item) == {
            "id",
            "kind",
            "title",
            "content",
            "revision",
            "updated_at",
            "review_due_at",
            "review_state",
        }


def test_retired_record_is_not_shown_and_history_is_preserved(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        project = _approve(
            application,
            client,
            kind="project",
            title="Temporary project",
            content="My active project is temporary.",
        )
        retired = client.put(
            f"/api/v1/knowledge/records/{project['id']}",
            headers=INTENT,
            json={
                "action": "retire",
                "confirmation": f"RETIRE {project['id'][:8]}",
            },
        )
        assert retired.status_code == 200

        overview = client.get("/api/v1/knowledge/planning").json()
        records = client.get("/api/v1/knowledge/records").json()

    assert overview["projects"] == []
    assert next(record for record in records if record["id"] == project["id"])[
        "status"
    ] == "retired"


def test_review_due_state_is_deterministic(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        goal = _approve(
            application,
            client,
            kind="goal",
            title="Old goal",
            content="My current goal is ready for review.",
        )
        stale_at = (datetime.now(UTC) - timedelta(days=91)).isoformat()
        connection = sqlite3.connect(tmp_path / "nova.db")
        connection.execute(
            "UPDATE knowledge_records SET updated_at = ? WHERE id = ?",
            (stale_at, goal["id"]),
        )
        connection.commit()
        connection.close()

        overview = client.get("/api/v1/knowledge/planning").json()

    assert overview["goals"][0]["review_state"] == "review_due"
    assert overview["goals"][0]["updated_at"] == stale_at.replace("+00:00", "Z")


def test_unverifiable_record_is_excluded_with_safe_warning(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        project = _approve(
            application,
            client,
            kind="project",
            title="Integrity test",
            content="My active project is the integrity test.",
        )
        record_path = tmp_path / "knowledge" / project["relative_path"]
        record_path.write_text("tampered", encoding="utf-8")
        assert hashlib.sha256(record_path.read_bytes()).hexdigest() != project["sha256"]

        response = client.get("/api/v1/knowledge/planning")

    assert response.status_code == 200
    overview = response.json()
    assert overview["projects"] == []
    assert overview["excluded_unverified_count"] == 1
    assert overview["warning"] == (
        "NOVA excluded 1 planning record because the approved local file "
        "could not be verified."
    )
    assert project["relative_path"] not in overview["warning"]
