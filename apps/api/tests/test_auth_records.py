from uuid import uuid4

from fastapi.testclient import TestClient

from src.application import app


def _register_and_login(client: TestClient) -> tuple[str, str]:
    email = f"tester-{uuid4().hex}@example.com"
    password = "StrongPass123"

    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    token = register_payload["access_token"]
    return email, token


def test_register_rejects_duplicate_email():
    with TestClient(app) as client:
        email = "duplicate@example.com"
        password = "StrongPass123"

        first = client.post("/api/auth/register", json={"email": email, "password": password})
        second = client.post("/api/auth/register", json={"email": email, "password": password})

    assert first.status_code == 200
    assert second.status_code == 409


def test_login_returns_token_for_existing_user():
    with TestClient(app) as client:
        email, _ = _register_and_login(client)
        response = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_records_crud_is_user_scoped():
    with TestClient(app) as client:
        _, token = _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post(
            "/api/records",
            headers=headers,
            json={
                "from_currency": "USD",
                "to_currency": "CNY",
                "from_amount": 1000,
                "to_amount": 7180,
                "rate_used": 7.18,
                "exchange_date": "2026-04-19",
                "purpose": "tuition",
                "notes": "phase2 test"
            },
        )
        assert create_response.status_code == 200
        record = create_response.json()

        list_response = client.get("/api/records", headers=headers)
        assert list_response.status_code == 200
        items = list_response.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == record["id"]

        update_response = client.patch(
            f"/api/records/{record['id']}",
            headers=headers,
            json={"notes": "updated note"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["notes"] == "updated note"

        delete_response = client.delete(f"/api/records/{record['id']}", headers=headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] is True

        final_list_response = client.get("/api/records", headers=headers)
        assert final_list_response.status_code == 200
        assert final_list_response.json()["items"] == []


def test_records_require_authentication():
    with TestClient(app) as client:
        response = client.get("/api/records")

    assert response.status_code == 401

