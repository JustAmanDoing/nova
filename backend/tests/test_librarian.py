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
    duplicate_confirmation: str | None = None,
) -> dict:
    conversation = application.state.chat.create_conversation("Librarian setup")
    message, _ = application.state.chat.begin_turn(
        conversation.id,
        f"Remember that {content}",
        "qwen3:8b",
    )
    candidate = application.state.knowledge.propose_from_message(message)
    assert candidate is not None
    payload = {
        "action": "approve",
        "kind": kind,
        "title": title,
        "content": content,
    }
    if duplicate_confirmation is not None:
        payload["duplicate_confirmation"] = duplicate_confirmation
    response = client.put(
        f"/api/v1/knowledge/candidates/{candidate.id}",
        headers=INTENT,
        json=payload,
    )
    assert response.status_code == 200, response.text
    return next(
        record
        for record in client.get("/api/v1/knowledge/records").json()
        if record["candidate_id"] == candidate.id
    )


def test_librarian_empty_health_and_missing_review_are_transparent(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        health = client.get("/api/v1/librarian/health")
        review = client.get("/api/v1/librarian/review")

    assert health.status_code == 200
    assert health.json()["active_record_count"] == 0
    assert health.json()["counts"]["missing_coverage"] == 13
    assert "not the owner" in health.json()["methodology"]
    assert review.status_code == 200
    assert review.json()["total"] == 13
    assert all(item["issue_type"] == "missing_coverage" for item in review.json()["issues"])
    titles = {item["title"] for item in review.json()["issues"]}
    assert {
        "How you like replies",
        "What you want to achieve",
        "Projects you are working on",
        "Your time zone or area",
        "Your work and schedule",
        "Your devices and software",
        "People you plan with",
        "Money goals",
        "Food or health preferences",
    } <= titles
    home = next(
        item
        for item in review.json()["issues"]
        if item["review_url"].endswith("home-responsibilities")
    )
    assert home["title"] == "Home jobs and projects"
    assert home["summary"] == (
        "You have not saved anything about this in Nova. You can ignore this suggestion."
    )
    assert home["reason"] == "Helps Nova remember home maintenance and projects."
    assert home["evidence"] == ["Area: Home.", "Optional suggestion."]
    assert home["suggested_action"] == (
        "Add a home job or project if you want Nova to help you remember it."
    )
    visible_copy = " ".join(
        str(item[field])
        for item in review.json()["issues"]
        for field in ("title", "summary", "reason", "suggested_action")
    ).lower()
    assert "context" not in visible_copy
    assert "environment" not in visible_copy
    assert "dietary" not in visible_copy


def test_librarian_detects_duplicates_conflicts_and_stale_records(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        first = _approve(
            application,
            client,
            kind="preference",
            title="Response style",
            content="I prefer responses that are concise and direct.",
        )
        duplicate = _approve(
            application,
            client,
            kind="preference",
            title="Concise response style",
            content="I prefer responses that are concise and direct.",
            duplicate_confirmation="CREATE SEPARATE RECORD",
        )
        conflict = _approve(
            application,
            client,
            kind="preference",
            title="Response style",
            content="Use expansive narrative explanations with many examples.",
        )
        stale_at = (datetime.now(UTC) - timedelta(days=400)).isoformat()
        connection = sqlite3.connect(tmp_path / "nova.db")
        connection.execute(
            "UPDATE knowledge_records SET updated_at = ? WHERE id IN (?, ?, ?)",
            (stale_at, first["id"], duplicate["id"], conflict["id"]),
        )
        connection.commit()
        connection.close()

        review = client.get("/api/v1/librarian/review")

    assert review.status_code == 200
    issues = review.json()["issues"]
    assert any(
        item["issue_type"] == "duplicate"
        and {first["id"], duplicate["id"]} <= set(item["record_ids"])
        and item["title"].startswith("These may say the same thing:")
        for item in issues
    )
    assert any(
        item["issue_type"] == "conflict"
        and {first["id"], conflict["id"]} <= set(item["record_ids"])
        and item["title"].startswith("These may disagree:")
        for item in issues
    )
    assert any(
        item["issue_type"] == "stale" and item["title"].endswith("may need checking")
        for item in issues
    )


def test_librarian_distinguishes_missing_checksum_and_broken_sources(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        missing = _approve(
            application,
            client,
            kind="fact",
            title="Missing source",
            content="The local missing source marker is amber.",
        )
        checksum = _approve(
            application,
            client,
            kind="fact",
            title="Checksum source",
            content="The local checksum source marker is blue.",
        )
        broken = _approve(
            application,
            client,
            kind="fact",
            title="Broken source",
            content="The local broken source marker is green.",
        )
        (tmp_path / "knowledge" / missing["relative_path"]).unlink()
        (tmp_path / "knowledge" / checksum["relative_path"]).write_text(
            "tampered", encoding="utf-8"
        )
        connection = sqlite3.connect(tmp_path / "nova.db")
        connection.execute(
            "UPDATE knowledge_records SET relative_path = '../outside.md' WHERE id = ?",
            (broken["id"],),
        )
        connection.commit()
        connection.close()

        health = client.get("/api/v1/librarian/health")
        review = client.get("/api/v1/librarian/review")

    assert health.status_code == 200
    counts = health.json()["counts"]
    assert counts["missing_files"] == 1
    assert counts["checksum_failures"] == 1
    assert counts["broken_references"] == 1
    issue_types = {item["issue_type"] for item in review.json()["issues"]}
    assert {"missing_file", "checksum_mismatch", "broken_reference"} <= issue_types
    issue_titles = {item["issue_type"]: item["title"] for item in review.json()["issues"]}
    assert issue_titles["missing_file"].startswith("Saved file is missing:")
    assert issue_titles["checksum_mismatch"].startswith("Saved file changed unexpectedly:")
    assert issue_titles["broken_reference"].startswith("Saved file link does not work:")


def test_librarian_item_exposes_sources_revisions_and_review_link(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        record = _approve(
            application,
            client,
            kind="fact",
            title="Missing detail source",
            content="The detail source marker is violet.",
        )
        (tmp_path / "knowledge" / record["relative_path"]).unlink()
        issue = next(
            item
            for item in client.get("/api/v1/librarian/review").json()["issues"]
            if item["issue_type"] == "missing_file"
        )
        detail = client.get(f"/api/v1/librarian/item/{issue['id']}")
        missing = client.get("/api/v1/librarian/item/not-current")

    assert detail.status_code == 200
    assert detail.json()["sources"][0]["record_id"] == record["id"]
    assert detail.json()["sources"][0]["candidate_confidence"] == 1
    assert detail.json()["revisions"][0]["revision"] == 1
    assert detail.json()["events"][0]["event_type"] == "created"
    assert detail.json()["issue"]["review_url"].endswith(record["id"])
    assert missing.status_code == 404


def test_librarian_endpoints_make_no_database_or_file_changes(tmp_path: Path) -> None:
    application = _application(tmp_path)
    with TestClient(application) as client:
        _approve(
            application,
            client,
            kind="fact",
            title="Read only source",
            content="The read only source marker is silver.",
        )
        database_path = tmp_path / "nova.db"
        knowledge_path = tmp_path / "knowledge"
        before_database = database_path.read_bytes()
        before_files = {
            path.relative_to(knowledge_path).as_posix(): path.read_bytes()
            for path in knowledge_path.rglob("*")
            if path.is_file()
        }

        health = client.get("/api/v1/librarian/health")
        review = client.get("/api/v1/librarian/review")
        item = client.get(f"/api/v1/librarian/item/{review.json()['issues'][0]['id']}")
        after_database = database_path.read_bytes()
        after_files = {
            path.relative_to(knowledge_path).as_posix(): path.read_bytes()
            for path in knowledge_path.rglob("*")
            if path.is_file()
        }

    assert health.status_code == 200
    assert review.status_code == 200
    assert item.status_code == 200
    assert after_database == before_database
    assert after_files == before_files
