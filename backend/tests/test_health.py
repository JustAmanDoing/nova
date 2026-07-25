from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app, create_app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Nova API"
    assert body["version"] == "0.32.0"
    assert body["environment"] == "development"
    assert body["timestamp"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


def test_openapi_document_is_available() -> None:
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Nova API"


def test_unexpected_host_is_rejected() -> None:
    rejected = client.get(
        "/api/v1/health",
        headers={"Host": "unexpected.example"},
    )
    allowed = client.get(
        "/api/v1/health",
        headers={"Host": "localhost"},
    )

    assert rejected.status_code == 400
    assert rejected.text == "Invalid host header"
    assert allowed.status_code == 200


def test_allowed_hosts_accept_comma_separated_configuration() -> None:
    settings = Settings(allowed_hosts="localhost, 127.0.0.1")

    assert settings.allowed_hosts == ["localhost", "127.0.0.1"]


def test_health_uses_the_application_configuration(tmp_path) -> None:
    application = create_app(
        Settings(
            app_name="Nova Review API",
            app_version="9.9.9",
            environment="review",
            intake_path=tmp_path / "intake",
            database_path=tmp_path / "nova.db",
            intake_scan_seconds=60,
        )
    )

    with TestClient(application) as configured_client:
        response = configured_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["service"] == "Nova Review API"
    assert response.json()["version"] == "9.9.9"
    assert response.json()["environment"] == "review"
