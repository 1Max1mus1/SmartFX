from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app
from src.services import auto_rule_service


def _auth_headers(client: TestClient, plan: str = "pro") -> dict[str, str]:
    email = f"phase6-{uuid4().hex}@example.com"
    password = "StrongPass123"
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "plan": plan},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auto_rules_require_pro_plan():
    with TestClient(app) as client:
        headers = _auth_headers(client, plan="free")
        response = client.get("/api/pro/auto-rules", headers=headers)

    assert response.status_code == 403


def test_rate_rule_crud_and_history():
    real_now = auto_rule_service._now_local

    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        auto_rule_service._now_local = lambda: datetime(2026, 4, 19, 10, 0, tzinfo=auto_rule_service.LOCAL_TZ)

        create_response = client.post(
            "/api/pro/auto-rules",
            headers=headers,
            json={
                "pair": "USD/CNY",
                "trigger_mode": "rate",
                "rate_condition": "above",
                "target_rate": 7.0,
                "watch_amount": 50000,
                "cooldown_minutes": 30,
                "quiet_hours_start": 1,
                "quiet_hours_end": 6,
                "notes": "phase 6 rule",
            },
        )
        assert create_response.status_code == 200
        rule_payload = create_response.json()
        assert rule_payload["pair"] == "USD/CNY"
        assert rule_payload["last_triggered_at"] is not None

        list_response = client.get("/api/pro/auto-rules", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["rules"]) == 1

        update_response = client.patch(
            f"/api/pro/auto-rules/{rule_payload['id']}",
            headers=headers,
            json={"target_rate": 7.3, "notes": "updated"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["target_rate"] == 7.3

        history_response = client.get("/api/pro/auto-rules/history", headers=headers)
        assert history_response.status_code == 200
        history_items = history_response.json()["items"]
        assert len(history_items) == 1
        assert history_items[0]["trigger_mode"] == "rate"
        assert "Notification only" in history_items[0]["message"]

        delete_response = client.delete(f"/api/pro/auto-rules/{rule_payload['id']}", headers=headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["is_active"] is False

        list_after_delete = client.get("/api/pro/auto-rules", headers=headers)
        assert list_after_delete.status_code == 200
        assert list_after_delete.json()["rules"] == []

    auto_rule_service._now_local = real_now


def test_ai_signal_rule_triggers_history_and_quiet_hours_are_respected(monkeypatch):
    real_now = auto_rule_service._now_local

    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        report_response = client.get("/api/report/daily", headers=headers)
        assert report_response.status_code == 200
        signal = report_response.json()["signal_usd_cny"]

        monkeypatch.setattr(auto_rule_service, "_now_local", lambda: datetime(2026, 4, 19, 10, 0, tzinfo=auto_rule_service.LOCAL_TZ))
        create_response = client.post(
            "/api/pro/auto-rules",
            headers=headers,
            json={
                "pair": "USD/CNY",
                "trigger_mode": "ai_signal",
                "signal_condition": signal,
                "cooldown_minutes": 60,
            },
        )
        assert create_response.status_code == 200
        rule_id = create_response.json()["id"]

        history_response = client.get(
            "/api/pro/auto-rules/history",
            headers=headers,
            params={"rule_id": rule_id},
        )
        assert history_response.status_code == 200
        history_items = history_response.json()["items"]
        assert len(history_items) == 1
        assert history_items[0]["signal_value"] == signal

        monkeypatch.setattr(auto_rule_service, "_now_local", lambda: datetime(2026, 4, 19, 2, 0, tzinfo=auto_rule_service.LOCAL_TZ))
        quiet_response = client.post(
            "/api/pro/auto-rules",
            headers=headers,
            json={
                "pair": "USD/CNY",
                "trigger_mode": "rate",
                "rate_condition": "above",
                "target_rate": 7.0,
                "quiet_hours_start": 1,
                "quiet_hours_end": 6,
                "cooldown_minutes": 30,
            },
        )
        assert quiet_response.status_code == 200
        quiet_rule_id = quiet_response.json()["id"]

        quiet_history_response = client.get(
            "/api/pro/auto-rules/history",
            headers=headers,
            params={"rule_id": quiet_rule_id},
        )
        assert quiet_history_response.status_code == 200
        assert quiet_history_response.json()["items"] == []

    monkeypatch.setattr(auto_rule_service, "_now_local", real_now)
