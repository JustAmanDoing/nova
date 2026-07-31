from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import LOCAL_ACTION_HEADER, LOCAL_ACTION_VALUE
from app.core.config import Settings
from app.main import create_app


def make_application(tmp_path: Path):
    return create_app(
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )


def test_every_mutating_api_requires_local_action_intent(tmp_path: Path) -> None:
    application = make_application(tmp_path)

    with TestClient(application) as client:
        blocked = [
            client.post("/api/v1/intake/scan"),
            client.post(
                "/api/v1/intake/preferences/reset",
                json={
                    "document_type": "plain_text",
                    "base_category": "Project",
                    "confirmation": "FORGET plain_text / Project",
                },
            ),
            client.put(
                "/api/v1/intake/files/not-present/approval",
                json={"action": "approve"},
            ),
            client.post("/api/v1/intake/files/not-present/execute"),
            client.post("/api/v1/intake/actions/not-present/undo"),
            client.post("/api/v1/backups"),
            client.put(
                "/api/v1/knowledge/candidates/not-present",
                json={"action": "reject"},
            ),
            client.put(
                "/api/v1/knowledge/records/not-present",
                json={
                    "action": "update",
                    "kind": "fact",
                    "title": "Blocked update",
                    "content": "This request must not reach the service.",
                },
            ),
            client.post("/api/v1/knowledge/snapshots"),
            client.post(
                "/api/v1/focus/actions",
                json={"title": "Blocked next action"},
            ),
            client.post("/api/v1/focus/actions/not-present/complete"),
            client.post("/api/v1/focus/actions/not-present/reopen"),
            client.post(
                "/api/v1/backups/nova-20260725T000000.000000Z.db/restore",
                json={"confirmation": "RESTORE nova-20260725T000000.000000Z.db"},
            ),
        ]
        wrong_intent = client.post(
            "/api/v1/intake/scan",
            headers={LOCAL_ACTION_HEADER: "not-nova"},
        )
        read_only = client.get("/api/v1/intake/summary")
        allowed = client.post(
            "/api/v1/intake/scan",
            headers={LOCAL_ACTION_HEADER: LOCAL_ACTION_VALUE},
        )

    assert all(response.status_code == 403 for response in blocked)
    assert all(
        response.json()
        == {"detail": "This change requires a request from Nova's local interface."}
        for response in blocked
    )
    assert wrong_intent.status_code == 403
    assert read_only.status_code == 200
    assert allowed.status_code == 200


def test_cors_preflight_allows_only_the_configured_local_interface(
    tmp_path: Path,
) -> None:
    application = make_application(tmp_path)
    requested_headers = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": LOCAL_ACTION_HEADER,
    }

    with TestClient(application) as client:
        allowed = client.options(
            "/api/v1/intake/scan",
            headers={"Origin": "http://localhost:5173", **requested_headers},
        )
        allowed_loopback = client.options(
            "/api/v1/intake/scan",
            headers={"Origin": "http://127.0.0.1:5173", **requested_headers},
        )
        allowed_private_network = client.options(
            "/api/v1/intake/scan",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": LOCAL_ACTION_HEADER,
                "Access-Control-Request-Private-Network": "true",
            },
        )
        blocked = client.options(
            "/api/v1/intake/scan",
            headers={"Origin": "https://example.invalid", **requested_headers},
        )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert LOCAL_ACTION_HEADER.lower() in allowed.headers[
        "access-control-allow-headers"
    ].lower()
    assert allowed_loopback.status_code == 200
    assert (
        allowed_loopback.headers["access-control-allow-origin"]
        == "http://127.0.0.1:5173"
    )
    assert allowed_private_network.status_code == 200
    assert (
        allowed_private_network.headers["access-control-allow-private-network"]
        == "true"
    )
    assert blocked.status_code == 400
    assert "access-control-allow-origin" not in blocked.headers
