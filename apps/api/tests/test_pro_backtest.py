import time
from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app


def _auth_headers(client: TestClient, plan: str = "pro") -> dict[str, str]:
    email = f"phase5-{uuid4().hex}@example.com"
    password = "StrongPass123"
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "plan": plan},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_records(client: TestClient, headers: dict[str, str]) -> None:
    payloads = [
        {
            "from_currency": "USD",
            "to_currency": "CNY",
            "from_amount": 10000,
            "to_amount": 71800,
            "rate_used": 7.18,
            "exchange_date": "2026-04-10",
            "purpose": "settlement",
            "notes": "seed 1",
        },
        {
            "from_currency": "USD",
            "to_currency": "CNY",
            "from_amount": 15000,
            "to_amount": 107700,
            "rate_used": 7.18,
            "exchange_date": "2026-04-15",
            "purpose": "settlement",
            "notes": "seed 2",
        },
    ]
    for payload in payloads:
        response = client.post("/api/records", headers=headers, json=payload)
        assert response.status_code == 200


def test_backtest_overview_requires_pro_plan():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="free")
        response = client.get("/api/pro/backtest/overview", headers=headers, params={"pair": "USD/CNY", "days": 90})

    assert response.status_code == 403


def test_backtest_overview_returns_signal_statistics():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        response = client.get("/api/pro/backtest/overview", headers=headers, params={"pair": "USD/CNY", "days": 90})

    assert response.status_code == 200
    payload = response.json()
    assert payload["pair"] == "USD/CNY"
    assert payload["days"] == 90
    assert len(payload["signals"]) == 3
    assert payload["best_signal_type"] in {"buy", "hold", "sell"}


def test_personal_backtest_job_completes_and_returns_result():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        _seed_records(client, headers)

        create_response = client.post(
            "/api/pro/backtest/personal",
            headers=headers,
            json={
                "period_start": "2026-04-01",
                "period_end": "2026-04-19",
                "pair": "USD/CNY",
            },
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        status_payload = None
        for _ in range(20):
            status_response = client.get(f"/api/pro/backtest/result/{job_id}", headers=headers)
            assert status_response.status_code == 200
            status_payload = status_response.json()
            if status_payload["job_status"] == "done":
                break
            time.sleep(0.05)

    assert status_payload is not None
    assert status_payload["job_status"] == "done"
    assert status_payload["result"]["record_count"] == 2
    assert "投资建议" in status_payload["result"]["disclaimer"]
