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
def clear_repositories() -> None:
    with SessionLocal() as session:
        session.query(Project).delete()
        session.query(Workspace).delete()
        session.query(Organization).delete()
        session.query(User).delete()
        session.commit()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "password": "StrongPassword123!",
    }
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace(client: TestClient) -> None:
    headers = _auth_headers(client)
    create_org_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Acme", "description": "Primary org"},
    )

    response = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": create_org_response.json()["id"], "name": "Engineering", "description": "Primary workspace"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Engineering"
    assert response.json()["organization_id"] == create_org_response.json()["id"]


def test_get_workspace(client: TestClient) -> None:
    headers = _auth_headers(client)
    create_org_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Beta", "description": "Secondary org"},
    )
    created = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": create_org_response.json()["id"], "name": "Research", "description": "Research workspace"},
    )

    response = client.get(f"/workspaces/{created.json()['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]
    assert response.json()["name"] == "Research"


def test_update_workspace(client: TestClient) -> None:
    headers = _auth_headers(client)
    create_org_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Gamma", "description": "Third org"},
    )
    created = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": create_org_response.json()["id"], "name": "Ops", "description": "Ops workspace"},
    )

    response = client.put(
        f"/workspaces/{created.json()['id']}",
        headers=headers,
        json={"name": "Operations", "description": "Updated"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Operations"
    assert response.json()["description"] == "Updated"


def test_delete_workspace(client: TestClient) -> None:
    headers = _auth_headers(client)
    create_org_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Delta", "description": "Fourth org"},
    )
    created = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": create_org_response.json()["id"], "name": "Archive", "description": "Archive workspace"},
    )

    delete_response = client.delete(f"/workspaces/{created.json()['id']}", headers=headers)
    get_response = client.get(f"/workspaces/{created.json()['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_workspaces_require_authentication(client: TestClient) -> None:
    response = client.get("/workspaces")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"
