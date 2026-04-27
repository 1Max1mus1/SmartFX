from datetime import date, timedelta
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.application import app


def main() -> None:
    with TestClient(app) as client:
        email = f"student-advice-smoke-{uuid4().hex}@example.com"
        register_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "StrongPass123"},
        )
        if register_response.status_code != 200:
            raise SystemExit(
                "Smoke register failed: "
                f"{register_response.status_code} {register_response.text}"
            )
        print("[PASS] /api/auth/register")

        headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}
        payload = {
            "deadline_date": (date.today() + timedelta(days=4)).isoformat(),
            "amount": 18000,
            "source_currency": "CNY",
            "target_currency": "USD",
            "can_split_payment": True,
            "risk_preference": "balanced",
            "notes": "学费这周内要交",
        }
        advice_response = client.post(
            "/api/ai/student-payment-advice",
            headers=headers,
            json=payload,
        )
        if advice_response.status_code != 200:
            raise SystemExit(
                "Smoke student payment advice failed: "
                f"{advice_response.status_code} {advice_response.text}"
            )

        advice = advice_response.json()
        required_fields = {
            "decision",
            "decision_level",
            "decision_reason",
            "rate_assessment",
            "deadline_pressure",
            "suggested_action",
            "market_snapshot",
            "analysis_markdown",
            "disclaimer",
        }
        missing_fields = sorted(required_fields - set(advice))
        if missing_fields:
            raise SystemExit(f"Smoke student payment advice missing fields: {missing_fields}")
        if "仅供信息参考" not in advice["disclaimer"]:
            raise SystemExit("Smoke student payment advice missing disclaimer text.")
        if advice["market_snapshot"]["requested_pair"] != "CNY/USD":
            raise SystemExit("Smoke student payment advice returned unexpected requested_pair.")
        print("[PASS] /api/ai/student-payment-advice")

    print("Student payment advice smoke checks passed.")


if __name__ == "__main__":
    main()
