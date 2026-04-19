from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"phase3-{uuid4().hex}@example.com"
    password = "StrongPass123"
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_daily_report_generates_and_returns_same_day_payload():
    with TestClient(app) as client:
        headers = _auth_headers(client)
        first = client.get("/api/report/daily", headers=headers)
        second = client.get("/api/report/daily", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["report_date"] == second_payload["report_date"]
    assert "summary_markdown" in first_payload
    assert "仅供信息参考" in first_payload["summary_markdown"]


def test_ai_chat_returns_session_and_disclaimer():
    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "现在美元高还是低？"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert "仅供信息参考" in payload["answer"]
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][1]["role"] == "assistant"

