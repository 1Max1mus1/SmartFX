import asyncio
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app
from src.clients.kimi_client import DISCLAIMER, KimiClient
from src.services.pro_report_service import ProReportService


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


def _analysis_payload() -> dict:
    return {
        "pair": "USD/CNY",
        "current_rate": 7.18,
        "current_percentile_30d": 42.5,
        "current_percentile_90d": 61.2,
        "immediate_value": 359000.0,
        "projected_best_case_value": 362500.0,
        "estimated_delta": 3500.0,
        "recommended_window_days": 5,
        "recommended_window_end_date": "2026-04-30",
        "recommended_window_reason": "当前处于中位区间，先观察 5 天更适合等待更清晰的回款窗口。",
        "zone_label": "中位",
        "narrative": "建议在未来 5 天关注更优窗口，并结合到账时间分批执行。",
        "disclaimer": DISCLAIMER,
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
    assert payload["recommended_window_reason"]
    assert payload["recommended_window_end_date"]
    assert DISCLAIMER in payload["disclaimer"]


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
    assert DISCLAIMER in " ".join(status_payload["result"]["sections"])


def test_report_status_recovers_when_background_task_was_not_scheduled(monkeypatch):
    async def fake_generate_settlement_report(self, analysis: dict, request: dict) -> dict:
        return {
            "title": "SmartFX AI 结算分析报告",
            "summary": "恢复执行成功。",
            "sections": ["商业影响：已生成。", DISCLAIMER],
            "markdown_report": f"# SmartFX AI 结算分析报告\n\n恢复执行成功。\n\n{DISCLAIMER}",
        }

    monkeypatch.setattr(ProReportService, "_schedule_report_job", staticmethod(lambda job_id, is_demo: None))
    monkeypatch.setattr(KimiClient, "generate_settlement_report", fake_generate_settlement_report)

    with TestClient(app) as client:
        headers = _auth_headers(client, plan="pro")
        create_response = client.post(
            "/api/pro/report/generate",
            headers=headers,
            json={"settlement_data": _settlement_payload()},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        status_response = client.get(f"/api/pro/report/status/{job_id}", headers=headers)

    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["job_status"] == "done"
    assert payload["result"]["summary"] == "恢复执行成功。"


def test_settlement_report_fallback_emphasizes_business_impact():
    client = KimiClient()
    result = client._build_settlement_report_fallback(_analysis_payload(), _settlement_payload(), ai_unavailable=False)

    assert "出口收汇" in result["summary"]
    assert "利润" in result["summary"]
    assert any("商业影响" in item for item in result["sections"])
    assert DISCLAIMER in result["markdown_report"]


def test_settlement_report_falls_back_when_ai_output_is_incomplete(monkeypatch):
    client = KimiClient()
    client.provider = "moonshot"
    client.api_key = "test-key"

    async def fake_chat_completion(messages: list[dict], *, max_tokens: int = 1200) -> str:
        return "# 只有标题"

    monkeypatch.setattr(client, "_chat_completion", fake_chat_completion)

    result = asyncio.run(client.generate_settlement_report(_analysis_payload(), _settlement_payload()))

    assert result["title"] == "SmartFX AI 结算分析报告"
    assert "商业影响" in " ".join(result["sections"])
    assert DISCLAIMER in result["markdown_report"]
