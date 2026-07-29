import hashlib
import json
import sqlite3
import zipfile
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
    conversation = application.state.chat.create_conversation("Lifecycle setup")
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
    title: str,
    content: str,
    duplicate_confirmation: str | None = None,
) -> dict:
    response = client.put(
        f"/api/v1/knowledge/candidates/{candidate_id}",
        headers=INTENT,
        json={
            "action": "approve",
            "kind": "fact",
            "title": title,
            "content": content,
            "duplicate_confirmation": duplicate_confirmation,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_possible_duplicate_requires_explicit_keep_separate_confirmation(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        first = _proposal(application, "the test phrase is amber lighthouse")
        _approve(
            client,
            first.id,
            title="Test phrase",
            content="The test phrase is amber lighthouse.",
        )

        second = _proposal(application, "the test phrase is amber lighthouse")
        candidates = client.get(
            "/api/v1/knowledge/candidates?status=pending"
        ).json()
        candidate = next(item for item in candidates if item["id"] == second.id)
        assert candidate["duplicate_record_id"] is not None
        assert candidate["duplicate_title"] == "Test phrase"
        assert candidate["duplicate_path"].endswith(".md")
        assert candidate["duplicate_score"] == 1.0

        blocked = client.put(
            f"/api/v1/knowledge/candidates/{second.id}",
            headers=INTENT,
            json={
                "action": "approve",
                "kind": "fact",
                "title": "Separate test phrase",
                "content": "The test phrase is amber lighthouse.",
            },
        )
        assert blocked.status_code == 409
        assert len(client.get("/api/v1/knowledge/records").json()) == 1

        _approve(
            client,
            second.id,
            title="Separate test phrase",
            content="The test phrase is amber lighthouse.",
            duplicate_confirmation="CREATE SEPARATE RECORD",
        )
        assert len(client.get("/api/v1/knowledge/records").json()) == 2


def test_update_creates_immutable_revision_and_changes_retrieval(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(application, "the project colour is blue")
        _approve(
            client,
            candidate.id,
            title="Project colour",
            content="The project colour is blue.",
        )
        original = client.get("/api/v1/knowledge/records").json()[0]
        original_path = tmp_path / "knowledge" / original["relative_path"]
        original_bytes = original_path.read_bytes()

        denied = client.put(
            f"/api/v1/knowledge/records/{original['id']}",
            json={
                "action": "update",
                "kind": "fact",
                "title": "Project colour",
                "content": "The project colour is green.",
            },
        )
        assert denied.status_code == 403

        updated_response = client.put(
            f"/api/v1/knowledge/records/{original['id']}",
            headers=INTENT,
            json={
                "action": "update",
                "kind": "fact",
                "title": "Project colour",
                "content": "The project colour is green.",
            },
        )
        assert updated_response.status_code == 200
        updated = updated_response.json()
        assert updated["revision"] == 2
        assert updated["status"] == "active"
        assert updated["relative_path"] != original["relative_path"]
        assert original_path.read_bytes() == original_bytes
        new_path = tmp_path / "knowledge" / updated["relative_path"]
        assert new_path.exists()
        assert updated["sha256"] == hashlib.sha256(new_path.read_bytes()).hexdigest()

        sources = application.state.knowledge.retrieve_approved(
            "What is the project colour?"
        )
        assert [source.content for source in sources] == [
            "The project colour is green."
        ]

        connection = sqlite3.connect(tmp_path / "nova.db")
        assert connection.execute(
            "SELECT COUNT(1) FROM knowledge_record_revisions WHERE record_id = ?",
            (original["id"],),
        ).fetchone()[0] == 2
        assert connection.execute(
            """
            SELECT event_type FROM knowledge_record_events
            WHERE record_id = ? ORDER BY sequence
            """,
            (original["id"],),
        ).fetchall() == [("created",), ("updated",)]
        connection.close()


def test_retirement_is_confirmed_non_destructive_and_excluded_from_retrieval(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(application, "the retirement phrase is coral moon")
        _approve(
            client,
            candidate.id,
            title="Retirement phrase",
            content="The retirement phrase is coral moon.",
        )
        record = client.get("/api/v1/knowledge/records").json()[0]
        record_path = tmp_path / "knowledge" / record["relative_path"]

        wrong = client.put(
            f"/api/v1/knowledge/records/{record['id']}",
            headers=INTENT,
            json={"action": "retire", "confirmation": "RETIRE wrong"},
        )
        assert wrong.status_code == 422

        retired_response = client.put(
            f"/api/v1/knowledge/records/{record['id']}",
            headers=INTENT,
            json={
                "action": "retire",
                "confirmation": f"RETIRE {record['id'][:8]}",
            },
        )
        assert retired_response.status_code == 200
        retired = retired_response.json()
        assert retired["status"] == "retired"
        assert retired["revision"] == 2
        assert retired["retired_at"] is not None
        assert record_path.exists()
        assert application.state.knowledge.retrieve_approved(
            "What is the retirement phrase?"
        ) == []


def test_verified_snapshot_contains_every_tracked_revision_and_manifest(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(application, "the snapshot phrase is violet harbor")
        _approve(
            client,
            candidate.id,
            title="Snapshot phrase",
            content="The snapshot phrase is violet harbor.",
        )

        denied = client.post("/api/v1/knowledge/snapshots")
        assert denied.status_code == 403
        created = client.post("/api/v1/knowledge/snapshots", headers=INTENT)
        assert created.status_code == 200
        snapshot = created.json()
        assert snapshot["record_count"] == 1
        assert snapshot["file_count"] == 1

        snapshot_path = tmp_path / "backups" / "knowledge" / snapshot["filename"]
        sidecar = snapshot_path.with_suffix(".zip.sha256")
        assert snapshot["sha256"] == hashlib.sha256(
            snapshot_path.read_bytes()
        ).hexdigest()
        assert snapshot["sha256"] in sidecar.read_text(encoding="utf-8")
        with zipfile.ZipFile(snapshot_path) as archive:
            assert archive.testzip() is None
            names = archive.namelist()
            assert "manifest.json" in names
            assert len([name for name in names if name.startswith("knowledge/")]) == 1
            manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format"] == "nova-knowledge-snapshot-v1"
        assert manifest["record_count"] == 1
        assert manifest["file_count"] == 1


def test_snapshot_fails_closed_if_any_tracked_revision_is_changed(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        candidate = _proposal(application, "the backup phrase is copper star")
        _approve(
            client,
            candidate.id,
            title="Backup phrase",
            content="The backup phrase is copper star.",
        )
        record = client.get("/api/v1/knowledge/records").json()[0]
        (tmp_path / "knowledge" / record["relative_path"]).write_text(
            "tampered",
            encoding="utf-8",
        )

        response = client.post("/api/v1/knowledge/snapshots", headers=INTENT)
        assert response.status_code == 422
        assert "integrity check" in response.json()["detail"]
        assert list((tmp_path / "backups" / "knowledge").glob("*.zip")) == []
