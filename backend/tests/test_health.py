from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Nova API"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "development"
    assert body["timestamp"]


def test_openapi_document_is_available() -> None:
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Nova API"

