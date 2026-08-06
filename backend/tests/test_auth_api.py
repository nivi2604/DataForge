import pytest
from fastapi.testclient import TestClient

from app.api.routes.auth import auth_service
from app.db.session import SessionLocal
from app.main import app
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace


@pytest.fixture(autouse=True)
def clear_user_repository() -> None:
    with SessionLocal() as session:
        session.query(Project).delete()
        session.query(Workspace).delete()
        session.query(Organization).delete()
        session.query(User).delete()
        session.commit()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_register_login_and_me_flow(client: TestClient) -> None:
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "password": "StrongPassword123!",
    }

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201
    assert register_response.json()["email"] == payload["email"]

    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    unauthorized_response = client.get("/auth/me")
    assert unauthorized_response.status_code == 401

    token = login_response.json()["access_token"]
    authorized_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert authorized_response.status_code == 200
    assert authorized_response.json()["email"] == payload["email"]


def test_me_returns_authenticated_user_with_valid_jwt(client: TestClient) -> None:
    payload = {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.com",
        "password": "StrongPassword123!",
    }

    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": response.json()["id"],
        "first_name": payload["first_name"],
        "last_name": payload["last_name"],
        "email": payload["email"],
        "created_at": response.json()["created_at"],
    }
    assert "password_hash" not in response.json()


def test_me_returns_401_when_jwt_is_missing(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"


def test_me_returns_401_when_jwt_is_invalid(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
