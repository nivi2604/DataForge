import json
import socket
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.data_source import DataSource
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace


@pytest.fixture(autouse=True)
def clear_repositories() -> None:
    with SessionLocal() as session:
        session.query(DataSource).delete()
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
        "first_name": "Data",
        "last_name": "Source",
        "email": "datasource@example.com",
        "password": "StrongPassword123!",
    }
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_project() -> str:
    with SessionLocal() as session:
        workspace = Workspace(id="workspace-data", name="Workspace Data")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        project = Project(id="project-data", workspace_id=workspace.id, name="Project Data", description="Seed project", status="active")
        session.add(project)
        session.commit()
        session.refresh(project)
        return project.id


def test_create_data_source(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()

    response = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Postgres Source",
            "type": "PostgreSQL",
            "connection_details": json.dumps(
                {
                    "host": "localhost",
                    "port": 5432,
                    "database": "app",
                    "username": "postgres",
                    "password": "secret",
                }
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Postgres Source"
    assert response.json()["type"] == "PostgreSQL"


def test_list_data_sources(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()
    client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "List Source",
            "type": "CSV",
            "connection_details": json.dumps({"path": "data.csv"}),
        },
    )

    response = client.get("/data-sources", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["name"] == "List Source"


def test_get_data_source(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()
    created = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Read Source",
            "type": "Excel",
            "connection_details": json.dumps({"path": "data.xlsx"}),
        },
    )

    response = client.get(f"/data-sources/{created.json()['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]
    assert response.json()["name"] == "Read Source"


def test_update_data_source(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()
    created = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Original Source",
            "type": "CSV",
            "connection_details": json.dumps({"path": "original.csv"}),
        },
    )

    response = client.put(
        f"/data-sources/{created.json()['id']}",
        headers=headers,
        json={"name": "Updated Source", "type": "Excel"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Source"
    assert response.json()["type"] == "Excel"


def test_delete_data_source(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()
    created = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Delete Source",
            "type": "MySQL",
            "connection_details": json.dumps(
                {
                    "host": "localhost",
                    "port": 3306,
                    "database": "app",
                    "username": "mysql",
                    "password": "secret",
                }
            ),
        },
    )

    delete_response = client.delete(f"/data-sources/{created.json()['id']}", headers=headers)
    get_response = client.get(f"/data-sources/{created.json()['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_test_connection_postgresql(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        created = client.post(
            "/data-sources",
            headers=headers,
            json={
                "project_id": project_id,
                "name": "PG Test",
                "type": "PostgreSQL",
                "connection_details": json.dumps(
                    {
                        "host": "127.0.0.1",
                        "port": port,
                        "database": "app",
                        "username": "postgres",
                        "password": "secret",
                    }
                ),
            },
        )

        response = client.post(
            f"/data-sources/{created.json()['id']}/test-connection",
            headers=headers,
            json={},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_test_connection_mysql(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        created = client.post(
            "/data-sources",
            headers=headers,
            json={
                "project_id": project_id,
                "name": "MySQL Test",
                "type": "MySQL",
                "connection_details": json.dumps(
                    {
                        "host": "127.0.0.1",
                        "port": port,
                        "database": "app",
                        "username": "mysql",
                        "password": "secret",
                    }
                ),
            },
        )

        response = client.post(
            f"/data-sources/{created.json()['id']}/test-connection",
            headers=headers,
            json={},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_test_connection_csv_file_exists(client: TestClient, tmp_path) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n")

    created = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "CSV Test",
            "type": "CSV",
            "connection_details": json.dumps({"path": str(csv_path)}),
        },
    )

    response = client.post(
        f"/data-sources/{created.json()['id']}/test-connection",
        headers=headers,
        json={},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_test_connection_excel_file_exists(client: TestClient, tmp_path) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()
    excel_path = tmp_path / "sample.xlsx"
    with zipfile.ZipFile(excel_path, "w") as workbook:
        workbook.writestr("xl/workbook.xml", "<workbook />")

    created = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Excel Test",
            "type": "Excel",
            "connection_details": json.dumps({"path": str(excel_path)}),
        },
    )

    response = client.post(
        f"/data-sources/{created.json()['id']}/test-connection",
        headers=headers,
        json={},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_test_connection_rest_api_reachable(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _seed_project()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format: str, *args) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    created = client.post(
        "/data-sources",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "REST Test",
            "type": "REST API",
            "connection_details": json.dumps({"url": f"http://127.0.0.1:{port}/health"}),
        },
    )

    response = client.post(
        f"/data-sources/{created.json()['id']}/test-connection",
        headers=headers,
        json={},
    )

    server.shutdown()
    server.server_close()
    thread.join()

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_data_sources_require_authentication(client: TestClient) -> None:
    response = client.get("/data-sources")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"
