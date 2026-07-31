import sqlite3
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


def _approve_project(application, client: TestClient) -> dict:
    conversation = application.state.chat.create_conversation("Action setup")
    message, _ = application.state.chat.begin_turn(
        conversation.id,
        "Remember that my active project is building NOVA.",
        "qwen3:8b",
    )
    candidate = application.state.knowledge.propose_from_message(message)
    assert candidate is not None
    response = client.put(
        f"/api/v1/knowledge/candidates/{candidate.id}",
        headers=INTENT,
        json={
            "action": "approve",
            "kind": "project",
            "title": "Build NOVA",
            "content": "My active project is building NOVA.",
        },
    )
    assert response.status_code == 200, response.text
    return next(
        record
        for record in client.get("/api/v1/knowledge/records").json()
        if record["candidate_id"] == candidate.id
    )


def test_next_actions_are_explicit_local_writes_with_auditable_events(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        blocked = client.post(
            "/api/v1/focus/actions",
            json={"title": "Review the NOVA plan"},
        )
        created_response = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "  Review   the NOVA plan  "},
        )
        created = created_response.json()
        overview = client.get("/api/v1/focus/actions").json()
        events = client.get(
            f"/api/v1/focus/actions/{created['id']}/events"
        ).json()

    assert blocked.status_code == 403
    assert created_response.status_code == 201
    assert created["title"] == "Review the NOVA plan"
    assert created["status"] == "open"
    assert created["project_record_id"] is None
    assert created["project_title"] is None
    assert created["project_unavailable"] is False
    assert [action["id"] for action in overview["open"]] == [created["id"]]
    assert overview["completed"] == []
    assert "does not infer priority" in overview["limitation"]
    assert [event["event_type"] for event in events] == ["created"]
    assert "Review the NOVA plan" not in events[0]["detail"]


def test_complete_and_reopen_are_guarded_append_only_transitions(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        created = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "Run owner acceptance"},
        ).json()
        blocked = client.post(
            f"/api/v1/focus/actions/{created['id']}/complete"
        )
        completed_response = client.post(
            f"/api/v1/focus/actions/{created['id']}/complete",
            headers=INTENT,
        )
        duplicate_complete = client.post(
            f"/api/v1/focus/actions/{created['id']}/complete",
            headers=INTENT,
        )
        reopened_response = client.post(
            f"/api/v1/focus/actions/{created['id']}/reopen",
            headers=INTENT,
        )
        events = client.get(
            f"/api/v1/focus/actions/{created['id']}/events"
        ).json()

    assert blocked.status_code == 403
    assert completed_response.status_code == 200
    assert completed_response.json()["status"] == "completed"
    assert completed_response.json()["completed_at"] is not None
    assert duplicate_complete.status_code == 409
    assert reopened_response.status_code == 200
    assert reopened_response.json()["status"] == "open"
    assert reopened_response.json()["completed_at"] is None
    assert [event["event_type"] for event in events] == [
        "created",
        "completed",
        "reopened",
    ]


def test_project_association_requires_verified_active_local_knowledge(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        project = _approve_project(application, client)
        created_response = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={
                "title": "Prepare the next NOVA acceptance run",
                "project_record_id": project["id"],
            },
        )
        created = created_response.json()
        retired = client.put(
            f"/api/v1/knowledge/records/{project['id']}",
            headers=INTENT,
            json={
                "action": "retire",
                "confirmation": f"RETIRE {project['id'][:8]}",
            },
        )
        overview = client.get("/api/v1/focus/actions").json()
        rejected = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={
                "title": "Must not use retired project content",
                "project_record_id": project["id"],
            },
        )

    assert created_response.status_code == 201
    assert created["project_title"] == "Build NOVA"
    assert created["project_revision"] == 1
    assert created["project_unavailable"] is False
    assert retired.status_code == 200
    stored = overview["open"][0]
    assert stored["project_record_id"] == project["id"]
    assert stored["project_title"] is None
    assert stored["project_revision"] is None
    assert stored["project_unavailable"] is True
    assert rejected.status_code == 422
    assert "active, verified local project" in rejected.json()["detail"]


def test_integrity_failure_never_exposes_stale_project_content(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        project = _approve_project(application, client)
        action = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={
                "title": "Keep the association safe",
                "project_record_id": project["id"],
            },
        ).json()
        record_path = tmp_path / "knowledge" / project["relative_path"]
        record_path.write_text("tampered project title", encoding="utf-8")

        overview = client.get("/api/v1/focus/actions").json()

    stored = next(item for item in overview["open"] if item["id"] == action["id"])
    assert stored["project_title"] is None
    assert stored["project_revision"] is None
    assert stored["project_unavailable"] is True
    assert "tampered project title" not in str(overview)


def test_actions_have_no_delete_path_and_history_remains_in_database(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        action = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "Preserve this history"},
        ).json()
        removed = client.delete(
            f"/api/v1/focus/actions/{action['id']}",
            headers=INTENT,
        )
        missing = client.get("/api/v1/focus/actions/not-present/events")

    with sqlite3.connect(tmp_path / "nova.db") as connection:
        action_count = connection.execute(
            "SELECT COUNT(*) FROM next_actions WHERE id = ?",
            (action["id"],),
        ).fetchone()[0]
        event_count = connection.execute(
            "SELECT COUNT(*) FROM next_action_events WHERE action_id = ?",
            (action["id"],),
        ).fetchone()[0]

    assert removed.status_code == 404
    assert missing.status_code == 404
    assert action_count == 1
    assert event_count == 1


def test_input_limits_and_deterministic_listing_are_enforced(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        empty = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "   "},
        )
        too_long = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "x" * 201},
        )
        first = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "First owner action"},
        ).json()
        second = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "Second owner action"},
        ).json()
        client.post(
            f"/api/v1/focus/actions/{first['id']}/complete",
            headers=INTENT,
        )
        overview = client.get("/api/v1/focus/actions").json()

    assert empty.status_code == 422
    assert too_long.status_code == 422
    assert [item["id"] for item in overview["open"]] == [second["id"]]
    assert [item["id"] for item in overview["completed"]] == [first["id"]]


def test_backup_and_restore_preserve_next_action_state_and_history(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        action = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={"title": "Restore this open action"},
        ).json()
        backup_response = client.post("/api/v1/backups", headers=INTENT)
        assert backup_response.status_code == 201, backup_response.text
        backup = backup_response.json()
        completed = client.post(
            f"/api/v1/focus/actions/{action['id']}/complete",
            headers=INTENT,
        )
        assert completed.status_code == 200

        restored = client.post(
            f"/api/v1/backups/{backup['filename']}/restore",
            headers=INTENT,
            json={"confirmation": f"RESTORE {backup['filename']}"},
        )
        overview = client.get("/api/v1/focus/actions").json()
        events = client.get(
            f"/api/v1/focus/actions/{action['id']}/events"
        ).json()

    assert restored.status_code == 200, restored.text
    assert [item["id"] for item in overview["open"]] == [action["id"]]
    assert overview["completed"] == []
    assert [event["event_type"] for event in events] == ["created"]


def test_action_lifecycle_does_not_mutate_approved_knowledge(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        project = _approve_project(application, client)
        before = client.get("/api/v1/knowledge/records").json()
        action = client.post(
            "/api/v1/focus/actions",
            headers=INTENT,
            json={
                "title": "Verify the knowledge boundary",
                "project_record_id": project["id"],
            },
        ).json()
        client.post(
            f"/api/v1/focus/actions/{action['id']}/complete",
            headers=INTENT,
        )
        client.post(
            f"/api/v1/focus/actions/{action['id']}/reopen",
            headers=INTENT,
        )
        after = client.get("/api/v1/knowledge/records").json()

    assert after == before
