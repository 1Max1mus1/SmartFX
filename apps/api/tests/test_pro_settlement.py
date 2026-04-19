import time
from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app


def _auth_headers(client: TestClient, plan: str = "pro") -> dict[str, str]:
    email = f"phase4-{uuid4().hex}@example.com"
    password = "StrongPass123"
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "plan": plan},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _settlement_payload() -> dict:
    return {
        "amount": 50000,
        "source_currency": "USD",
        "target_currency": "CNY",
        "arrival_date": "2026-04-25",
        "optimization_goal": "maximize_income",
    }


def test_pro_settlement_requires_pro_plan():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="free")
        response = client.post("/api/pro/settlement", headers=headers, json=_settlement_payload())

    assert response.status_code == 403


def test_pro_settlement_returns_structured_analysis():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        response = client.post("/api/pro/settlement", headers=headers, json=_settlement_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["pair"] == "USD/CNY"
    assert payload["current_rate"] > 0
    assert payload["recommended_window_days"] > 0
    assert "仅供信息参考" in payload["disclaimer"]


def test_generate_pro_report_and_poll_until_done():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        create_response = client.post(
            "/api/pro/report/generate",
            headers=headers,
            json={"settlement_data": _settlement_payload()},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        status_payload = None
        for _ in range(20):
            status_response = client.get(f"/api/pro/report/status/{job_id}", headers=headers)
            assert status_response.status_code == 200
            status_payload = status_response.json()
            if status_payload["job_status"] == "done":
                break
            time.sleep(0.05)

    assert status_payload is not None
    assert status_payload["job_status"] == "done"
    assert status_payload["result"]["title"]
    assert "仅供信息参考" in " ".join(status_payload["result"]["sections"])

