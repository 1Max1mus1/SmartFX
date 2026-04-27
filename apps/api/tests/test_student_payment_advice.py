from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app
from src.clients.kimi_client import DISCLAIMER, KimiClient
from src.schemas.format import ResponseFormatter
from src.services.rate_service import RateService

RESPONSE = ResponseFormatter(prefix="[Test]")


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"student-payment-{uuid4().hex}@example.com"
    password = "StrongPass123"
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _history_points(values: list[float]) -> list[dict]:
    start = date.today() - timedelta(days=len(values) - 1)
    return [
        {
            "day": (start + timedelta(days=index)).isoformat(),
            "rate": value,
        }
        for index, value in enumerate(values)
    ]


def test_student_payment_advice_returns_split_plan_for_medium_deadline(monkeypatch):
    async def fake_live_conversion_rate(from_currency: str, to_currency: str) -> float:
        assert (from_currency, to_currency) == ("USD", "CNY")
        return 7.2

    async def fake_history(pair: str, days: int) -> tuple[dict, object]:
        assert pair == "USD/CNY"
        if days == 30:
            points = _history_points(
                [
                    6.8,
                    6.85,
                    6.9,
                    6.95,
                    7.0,
                    7.02,
                    7.04,
                    7.05,
                    7.06,
                    7.08,
                    7.1,
                    7.12,
                    7.14,
                    7.16,
                    7.18,
                    7.19,
                    7.2,
                    7.21,
                    7.22,
                    7.23,
                    7.24,
                    7.25,
                    7.26,
                    7.27,
                    7.28,
                    7.29,
                    7.3,
                    7.31,
                    7.32,
                    7.33,
                ]
            )
        else:
            points = _history_points([6.7 + (index * 0.01) for index in range(days)])
        return {"pair": pair, "days": days, "points": points}, RESPONSE.ok("history ready")

    monkeypatch.setattr(RateService, "get_live_conversion_rate", fake_live_conversion_rate)
    monkeypatch.setattr(RateService, "get_history", fake_history)

    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() + timedelta(days=5)).isoformat(),
                "amount": 20000,
                "source_currency": "USD",
                "target_currency": "CNY",
                "can_split_payment": True,
                "risk_preference": "balanced",
                "notes": "Family can split payment this week.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_level"] == "split_now"
    assert payload["split_payment_plan"] is not None
    assert payload["market_snapshot"]["requested_pair"] == "USD/CNY"
    assert payload["market_snapshot"]["reference_pair"] == "USD/CNY"
    assert payload["market_snapshot"]["percentile_30d"] >= 45
    assert DISCLAIMER in payload["disclaimer"]
    assert "Family can split payment this week." in payload["analysis_markdown"]


def test_student_payment_advice_uses_ai_enhanced_markdown(monkeypatch):
    async def fake_live_conversion_rate(from_currency: str, to_currency: str) -> float:
        return 7.18

    async def fake_history(pair: str, days: int) -> tuple[dict, object]:
        points = _history_points([6.9 + (index * 0.01) for index in range(days)])
        return {"pair": pair, "days": days, "points": points}, RESPONSE.ok("history ready")

    async def fake_generate_student_payment_advice(self, request: dict, advice_context: dict, fallback_markdown: str) -> str:
        assert request["source_currency"] == "USD"
        assert advice_context["decision_level"] in {"pay_now", "split_now", "watch_short"}
        assert DISCLAIMER in fallback_markdown
        return f"## AI Enhanced Summary\n\nNatural explanation.\n\n{DISCLAIMER}"

    monkeypatch.setattr(RateService, "get_live_conversion_rate", fake_live_conversion_rate)
    monkeypatch.setattr(RateService, "get_history", fake_history)
    monkeypatch.setattr(KimiClient, "generate_student_payment_advice", fake_generate_student_payment_advice)

    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() + timedelta(days=6)).isoformat(),
                "source_currency": "USD",
                "target_currency": "CNY",
                "can_split_payment": True,
                "risk_preference": "balanced",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert "AI Enhanced Summary" in payload["analysis_markdown"]


def test_student_payment_advice_falls_back_when_ai_generation_returns_fallback(monkeypatch):
    async def fake_live_conversion_rate(from_currency: str, to_currency: str) -> float:
        return 7.0

    async def fake_history(pair: str, days: int) -> tuple[dict, object]:
        points = _history_points([6.7 + (index * 0.015) for index in range(days)])
        return {"pair": pair, "days": days, "points": points}, RESPONSE.ok("history ready")

    async def fake_generate_student_payment_advice(self, request: dict, advice_context: dict, fallback_markdown: str) -> str:
        return fallback_markdown

    monkeypatch.setattr(RateService, "get_live_conversion_rate", fake_live_conversion_rate)
    monkeypatch.setattr(RateService, "get_history", fake_history)
    monkeypatch.setattr(KimiClient, "generate_student_payment_advice", fake_generate_student_payment_advice)

    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() + timedelta(days=10)).isoformat(),
                "source_currency": "USD",
                "target_currency": "CNY",
                "can_split_payment": False,
                "risk_preference": "balanced",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_markdown"].startswith("## ")
    assert DISCLAIMER in payload["analysis_markdown"]


def test_student_payment_advice_forces_pay_now_when_deadline_is_imminent(monkeypatch):
    async def fake_live_conversion_rate(from_currency: str, to_currency: str) -> float:
        return 0.1388

    async def fake_history(pair: str, days: int) -> tuple[dict, object]:
        assert pair == "USD/CNY"
        points = _history_points([7.05 + (index * 0.01) for index in range(days)])
        return {"pair": pair, "days": days, "points": points}, RESPONSE.ok("history ready")

    monkeypatch.setattr(RateService, "get_live_conversion_rate", fake_live_conversion_rate)
    monkeypatch.setattr(RateService, "get_history", fake_history)

    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() + timedelta(days=1)).isoformat(),
                "source_currency": "CNY",
                "target_currency": "USD",
                "can_split_payment": True,
                "risk_preference": "opportunistic",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_level"] == "pay_now"
    assert payload["split_payment_plan"] is None
    assert payload["deadline_pressure"]
    assert payload["market_snapshot"]["requested_pair"] == "CNY/USD"
    assert payload["market_snapshot"]["reference_pair"] == "USD/CNY"


def test_student_payment_advice_can_watch_short_when_deadline_is_loose(monkeypatch):
    async def fake_live_conversion_rate(from_currency: str, to_currency: str) -> float:
        return 7.0

    async def fake_history(pair: str, days: int) -> tuple[dict, object]:
        points = _history_points([6.7 + (index * 0.02) for index in range(days)])
        return {"pair": pair, "days": days, "points": points}, RESPONSE.ok("history ready")

    monkeypatch.setattr(RateService, "get_live_conversion_rate", fake_live_conversion_rate)
    monkeypatch.setattr(RateService, "get_history", fake_history)

    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() + timedelta(days=14)).isoformat(),
                "source_currency": "USD",
                "target_currency": "CNY",
                "can_split_payment": False,
                "risk_preference": "balanced",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_level"] == "watch_short"
    assert payload["split_payment_plan"] is None
    assert payload["deadline_pressure"]


def test_student_payment_advice_rejects_same_currency():
    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() + timedelta(days=5)).isoformat(),
                "source_currency": "USD",
                "target_currency": "USD",
                "can_split_payment": True,
                "risk_preference": "balanced",
            },
        )

    assert response.status_code == 400
    assert "must be different" in response.json()["detail"]


def test_student_payment_advice_rejects_past_deadline():
    with TestClient(app) as client:
        headers = _auth_headers(client)
        response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json={
                "deadline_date": (date.today() - timedelta(days=1)).isoformat(),
                "source_currency": "USD",
                "target_currency": "CNY",
                "can_split_payment": True,
                "risk_preference": "balanced",
            },
        )

    assert response.status_code == 400
    assert "today or later" in response.json()["detail"]
