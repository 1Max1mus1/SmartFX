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
        endpoints = [
            ("/api/health", None),
            ("/api/rates/live", None),
            ("/api/rates/history", {"pair": "USD/CNY", "days": 7}),
            ("/api/rates/stats", {"pair": "USD/HKD", "days": 30}),
        ]
        for path, params in endpoints:
            response = client.get(path, params=params)
            if response.status_code != 200:
                raise SystemExit(f"Smoke check failed for {path}: {response.status_code} {response.text}")
            print(f"[PASS] {path}")

        email = f"smoke-{uuid4().hex}@example.com"
        register_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "StrongPass123"},
        )
        if register_response.status_code != 200:
            raise SystemExit(f"Smoke register failed: {register_response.status_code} {register_response.text}")
        print("[PASS] /api/auth/register")

        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        create_response = client.post(
            "/api/records",
            headers=headers,
            json={
                "from_currency": "USD",
                "to_currency": "CNY",
                "from_amount": 500,
                "to_amount": 3590,
                "rate_used": 7.18,
                "exchange_date": "2026-04-19",
                "purpose": "smoke",
                "notes": "phase smoke",
            },
        )
        if create_response.status_code != 200:
            raise SystemExit(f"Smoke create record failed: {create_response.status_code} {create_response.text}")
        print("[PASS] /api/records POST")

        list_response = client.get("/api/records", headers=headers)
        if list_response.status_code != 200:
            raise SystemExit(f"Smoke list records failed: {list_response.status_code} {list_response.text}")
        print("[PASS] /api/records GET")

        report_response = client.get("/api/report/daily", headers=headers)
        if report_response.status_code != 200:
            raise SystemExit(f"Smoke daily report failed: {report_response.status_code} {report_response.text}")
        print("[PASS] /api/report/daily GET")

        chat_response = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": "现在美元高还是低？"},
        )
        if chat_response.status_code != 200:
            raise SystemExit(f"Smoke AI chat failed: {chat_response.status_code} {chat_response.text}")
        print("[PASS] /api/ai/chat POST")

        pro_email = f"pro-smoke-{uuid4().hex}@example.com"
        pro_register_response = client.post(
            "/api/auth/register",
            json={"email": pro_email, "password": "StrongPass123", "plan": "pro"},
        )
        if pro_register_response.status_code != 200:
            raise SystemExit(f"Smoke pro register failed: {pro_register_response.status_code} {pro_register_response.text}")
        pro_headers = {"Authorization": f"Bearer {pro_register_response.json()['access_token']}"}

        settlement_response = client.post(
            "/api/pro/settlement",
            headers=pro_headers,
            json={
                "amount": 50000,
                "source_currency": "USD",
                "target_currency": "CNY",
                "arrival_date": "2026-04-25",
                "optimization_goal": "maximize_income",
            },
        )
        if settlement_response.status_code != 200:
            raise SystemExit(f"Smoke pro settlement failed: {settlement_response.status_code} {settlement_response.text}")
        print("[PASS] /api/pro/settlement POST")

        report_create_response = client.post(
            "/api/pro/report/generate",
            headers=pro_headers,
            json={
                "settlement_data": {
                    "amount": 50000,
                    "source_currency": "USD",
                    "target_currency": "CNY",
                    "arrival_date": "2026-04-25",
                    "optimization_goal": "maximize_income",
                }
            },
        )
        if report_create_response.status_code != 200:
            raise SystemExit(f"Smoke report generate failed: {report_create_response.status_code} {report_create_response.text}")
        print("[PASS] /api/pro/report/generate POST")

        report_job_id = report_create_response.json()["job_id"]
        report_status_ok = False
        for _ in range(20):
            report_status_response = client.get(f"/api/pro/report/status/{report_job_id}", headers=pro_headers)
            if report_status_response.status_code != 200:
                raise SystemExit(f"Smoke report status failed: {report_status_response.status_code} {report_status_response.text}")
            if report_status_response.json()["job_status"] == "done":
                report_status_ok = True
                break
        if not report_status_ok:
            raise SystemExit("Smoke report status polling timed out before reaching done state.")
        print("[PASS] /api/pro/report/status/{job_id} GET")

        seed_records = [
            {
                "from_currency": "USD",
                "to_currency": "CNY",
                "from_amount": 10000,
                "to_amount": 71800,
                "rate_used": 7.18,
                "exchange_date": "2026-04-10",
                "purpose": "backtest",
                "notes": "seed 1",
            },
            {
                "from_currency": "USD",
                "to_currency": "CNY",
                "from_amount": 12000,
                "to_amount": 86160,
                "rate_used": 7.18,
                "exchange_date": "2026-04-15",
                "purpose": "backtest",
                "notes": "seed 2",
            },
        ]
        for payload in seed_records:
            seed_response = client.post("/api/records", headers=pro_headers, json=payload)
            if seed_response.status_code != 200:
                raise SystemExit(f"Smoke backtest seed record failed: {seed_response.status_code} {seed_response.text}")

        overview_response = client.get(
            "/api/pro/backtest/overview",
            headers=pro_headers,
            params={"pair": "USD/CNY", "days": 90},
        )
        if overview_response.status_code != 200:
            raise SystemExit(f"Smoke backtest overview failed: {overview_response.status_code} {overview_response.text}")
        print("[PASS] /api/pro/backtest/overview GET")

        personal_response = client.post(
            "/api/pro/backtest/personal",
            headers=pro_headers,
            json={
                "period_start": "2026-04-01",
                "period_end": "2026-04-19",
                "pair": "USD/CNY",
            },
        )
        if personal_response.status_code != 200:
            raise SystemExit(f"Smoke personal backtest failed: {personal_response.status_code} {personal_response.text}")
        print("[PASS] /api/pro/backtest/personal POST")

        backtest_job_id = personal_response.json()["job_id"]
        backtest_status_ok = False
        for _ in range(20):
            backtest_status_response = client.get(f"/api/pro/backtest/result/{backtest_job_id}", headers=pro_headers)
            if backtest_status_response.status_code != 200:
                raise SystemExit(f"Smoke backtest result failed: {backtest_status_response.status_code} {backtest_status_response.text}")
            if backtest_status_response.json()["job_status"] == "done":
                backtest_status_ok = True
                break
        if not backtest_status_ok:
            raise SystemExit("Smoke backtest result polling timed out before reaching done state.")
        print("[PASS] /api/pro/backtest/result/{job_id} GET")

        auto_rule_response = client.post(
            "/api/pro/auto-rules",
            headers=pro_headers,
            json={
                "pair": "USD/CNY",
                "trigger_mode": "rate",
                "rate_condition": "above",
                "target_rate": 7.0,
                "watch_amount": 50000,
                "cooldown_minutes": 120,
            },
        )
        if auto_rule_response.status_code != 200:
            raise SystemExit(f"Smoke auto rule create failed: {auto_rule_response.status_code} {auto_rule_response.text}")
        print("[PASS] /api/pro/auto-rules POST")

        auto_rule_list_response = client.get("/api/pro/auto-rules", headers=pro_headers)
        if auto_rule_list_response.status_code != 200:
            raise SystemExit(
                f"Smoke auto rule list failed: {auto_rule_list_response.status_code} {auto_rule_list_response.text}"
            )
        print("[PASS] /api/pro/auto-rules GET")

        auto_rule_history_response = client.get("/api/pro/auto-rules/history", headers=pro_headers)
        if auto_rule_history_response.status_code != 200:
            raise SystemExit(
                "Smoke auto rule history failed: "
                f"{auto_rule_history_response.status_code} {auto_rule_history_response.text}"
            )
        if len(auto_rule_history_response.json()["items"]) < 1:
            raise SystemExit("Smoke auto rule history returned no trigger items.")
        print("[PASS] /api/pro/auto-rules/history GET")

    print("Phase 0/1/2/3/4/5/6 smoke checks passed.")


if __name__ == "__main__":
    main()
