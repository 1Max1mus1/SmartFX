from fastapi.testclient import TestClient

from src.application import app


def test_live_rates_returns_three_supported_pairs():
    with TestClient(app) as client:
        response = client.get("/api/rates/live")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["pairs"]) == 3
    assert {item["pair"] for item in payload["pairs"]} == {"USD/CNY", "HKD/CNY", "USD/HKD"}


def test_rate_history_returns_requested_window():
    with TestClient(app) as client:
        response = client.get("/api/rates/history", params={"pair": "USD/CNY", "days": 30})

    assert response.status_code == 200
    payload = response.json()
    assert payload["pair"] == "USD/CNY"
    assert payload["days"] == 30
    assert len(payload["points"]) == 30


def test_rate_stats_returns_aggregates():
    with TestClient(app) as client:
        response = client.get("/api/rates/stats", params={"pair": "HKD/CNY", "days": 90})

    assert response.status_code == 200
    payload = response.json()
    assert payload["pair"] == "HKD/CNY"
    assert payload["days"] == 90
    assert payload["high"] >= payload["low"]
    assert 0 <= payload["percentile"] <= 100


def test_rate_history_rejects_unsupported_pair():
    with TestClient(app) as client:
        response = client.get("/api/rates/history", params={"pair": "EUR/CNY", "days": 30})

    assert response.status_code == 400

