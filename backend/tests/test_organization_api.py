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


def _register_and_login(client: TestClient, email: str, first_name: str = "Owner") -> dict[str, str]:
    payload = {
        "first_name": first_name,
        "last_name": "Example",
        "email": email,
        "password": "StrongPassword123!",
    }
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_organization(client: TestClient) -> None:
    headers = _register_and_login(client, "alice@example.com", "Alice")

    response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Acme", "description": "Primary org"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Acme"
    assert response.json()["owner_id"] == auth_service.user_repository.get_by_email("alice@example.com").id


def test_list_organizations(client: TestClient) -> None:
    headers = _register_and_login(client, "list@example.com", "List")
    client.post(
        "/organizations",
        headers=headers,
        json={"name": "Visible Org", "description": "Visible"},
    )

    response = client.get("/organizations", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["name"] == "Visible Org"


def test_get_organization(client: TestClient) -> None:
    headers = _register_and_login(client, "get@example.com", "Get")
    created = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Lookup Org", "description": "Lookup"},
    )

    response = client.get(f"/organizations/{created.json()['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]
    assert response.json()["name"] == "Lookup Org"


def test_update_organization(client: TestClient) -> None:
    headers = _register_and_login(client, "update@example.com", "Update")
    created = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Original Org", "description": "Original"},
    )

    response = client.put(
        f"/organizations/{created.json()['id']}",
        headers=headers,
        json={"name": "Updated Org", "description": "Updated"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Org"
    assert response.json()["description"] == "Updated"


def test_delete_organization(client: TestClient) -> None:
    headers = _register_and_login(client, "delete@example.com", "Delete")
    created = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Delete Org", "description": "Delete"},
    )

    delete_response = client.delete(f"/organizations/{created.json()['id']}", headers=headers)
    get_response = client.get(f"/organizations/{created.json()['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_duplicate_organization_name_for_same_owner(client: TestClient) -> None:
    headers = _register_and_login(client, "duplicate@example.com", "Duplicate")
    client.post(
        "/organizations",
        headers=headers,
        json={"name": "Duplicate Org", "description": "First"},
    )

    response = client.post(
        "/organizations",
        headers=headers,
        json={"name": "Duplicate Org", "description": "Second"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Organization name already exists for this owner"


def test_organizations_require_authentication(client: TestClient) -> None:
    response = client.get("/organizations")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"


def test_non_owner_cannot_update_or_delete_organization(client: TestClient) -> None:
    owner_headers = _register_and_login(client, "owner@example.com", "Owner")
    other_headers = _register_and_login(client, "other@example.com", "Other")

    created = client.post(
        "/organizations",
        headers=owner_headers,
        json={"name": "Protected Org", "description": "Protected"},
    )

    update_response = client.put(
        f"/organizations/{created.json()['id']}",
        headers=other_headers,
        json={"name": "Tampered"},
    )
    delete_response = client.delete(f"/organizations/{created.json()['id']}", headers=other_headers)

    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "Only the organization owner can update this organization"
    assert delete_response.status_code == 403
    assert delete_response.json()["detail"] == "Only the organization owner can delete this organization"
