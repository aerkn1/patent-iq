from fastapi.testclient import TestClient

from main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_v1_routes_are_mounted() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/stats/runtime")
    assert response.status_code == 200
    assert response.json()["api_prefix"] == "/api/v1"
