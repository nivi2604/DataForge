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
        "first_name": "Linus",
        "last_name": "Torvalds",
        "email": "linus@example.com",
        "password": "StrongPassword123!",
    }
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_project(client: TestClient) -> None:
    headers = _auth_headers(client)
    organization_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Workspace Org", "description": "Org for workspace tests"},
    )
    workspace_response = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": organization_response.json()["id"], "name": "Workspace 1", "description": "Workspace for project"},
    )

    response = client.post(
        "/projects",
        headers=headers,
        json={"workspace_id": workspace_response.json()["id"], "name": "Alpha Project", "description": "First project"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Alpha Project"
    assert response.json()["workspace_id"] == workspace_response.json()["id"]


def test_get_project(client: TestClient) -> None:
    headers = _auth_headers(client)
    organization_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Workspace Org 2", "description": "Org for workspace tests"},
    )
    workspace_response = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": organization_response.json()["id"], "name": "Workspace 2", "description": "Workspace for project"},
    )
    created = client.post(
        "/projects",
        headers=headers,
        json={"workspace_id": workspace_response.json()["id"], "name": "Beta Project"},
    )

    response = client.get(f"/projects/{created.json()['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]
    assert response.json()["name"] == "Beta Project"


def test_update_project(client: TestClient) -> None:
    headers = _auth_headers(client)
    organization_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Workspace Org 3", "description": "Org for workspace tests"},
    )
    workspace_response = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": organization_response.json()["id"], "name": "Workspace 3", "description": "Workspace for project"},
    )
    created = client.post(
        "/projects",
        headers=headers,
        json={"workspace_id": workspace_response.json()["id"], "name": "Gamma Project"},
    )

    response = client.put(
        f"/projects/{created.json()['id']}",
        headers=headers,
        json={"name": "Updated Gamma Project", "status": "active"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Gamma Project"
    assert response.json()["status"] == "active"


def test_delete_project(client: TestClient) -> None:
    headers = _auth_headers(client)
    organization_response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Workspace Org 4", "description": "Org for workspace tests"},
    )
    workspace_response = client.post(
        "/workspaces",
        headers=headers,
        json={"organization_id": organization_response.json()["id"], "name": "Workspace 4", "description": "Workspace for project"},
    )
    created = client.post(
        "/projects",
        headers=headers,
        json={"workspace_id": workspace_response.json()["id"], "name": "Delta Project"},
    )

    delete_response = client.delete(f"/projects/{created.json()['id']}", headers=headers)
    get_response = client.get(f"/projects/{created.json()['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_projects_require_authentication(client: TestClient) -> None:
    response = client.get("/projects")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"
