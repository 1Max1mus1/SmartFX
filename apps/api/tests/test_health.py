from fastapi.testclient import TestClient

from src.application import app


def test_health_check_returns_ok():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.headers["x-process-time-ms"]
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"]["name"] == "SmartFX API"
    assert payload["app"]["env"] == "development"
    assert payload["components"]["database"] is True
    assert payload["components"]["cache"] is True


def test_live_and_ready_checks_return_ok():
    with TestClient(app) as client:
        live_response = client.get("/api/health/live")
        ready_response = client.get("/api/health/ready")

    assert live_response.status_code == 200
    assert ready_response.status_code == 200
    assert live_response.json()["status"] == "ok"
    assert ready_response.json()["status"] == "ok"
    assert "components" in ready_response.json()
