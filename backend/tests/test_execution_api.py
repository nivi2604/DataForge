import json
import csv
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.organization import Organization
from app.models.project import Project
from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.models.pipeline_execution import PipelineExecution
from app.models.execution_log import ExecutionLog
from app.models.user import User
from app.models.workspace import Workspace
from app.models.data_source import DataSource

@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture()
def temp_csv_files() -> tuple[Path, Path]:
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "source.csv"
        target = Path(tmpdir) / "target.csv"
        source.write_text("name,value\nAlice,10\nBob,\nCharlie,20\n")
        target.write_text("name,value\n")
        yield source, target

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

def _create_project(client: TestClient, headers: dict[str, str]) -> str:
    org_res = client.post("/organizations", headers=headers, json={"name": "Org"})
    ws_res = client.post("/workspaces", headers=headers, json={"organization_id": org_res.json()["id"], "name": "WS"})
    proj_res = client.post("/projects", headers=headers, json={"workspace_id": ws_res.json()["id"], "name": "Proj"})
    return proj_res.json()["id"]

def _create_pipeline(client: TestClient, headers: dict[str, str], project_id: str) -> str:
    res = client.post("/pipelines", headers=headers, json={"project_id": project_id, "name": "Pipe"})
    return res.json()["id"]

def _create_csv_data_source(client: TestClient, headers: dict[str, str], project_id: str, path: str, name: str) -> str:
    res = client.post("/data-sources", headers=headers, json={
        "project_id": project_id,
        "name": name,
        "type": "CSV",
        "connection_details": json.dumps({"path": path})
    })
    return res.json()["id"]

def test_execute_valid_pipeline(client: TestClient, temp_csv_files: tuple[Path, Path]) -> None:
    headers = _auth_headers(client)
    project_id = _create_project(client, headers)
    pipeline_id = _create_pipeline(client, headers, project_id)
    
    source_path, target_path = temp_csv_files
    source_id = _create_csv_data_source(client, headers, project_id, str(source_path), "Source")
    target_id = _create_csv_data_source(client, headers, project_id, str(target_path), "Target")
    
    # 1. Extract Node
    client.post(f"/pipelines/{pipeline_id}/nodes", headers=headers, json={
        "node_type": "extract",
        "configuration": json.dumps({"data_source_id": source_id}),
        "sequence_index": 1
    })

    # 2. Transform Node (drop nulls)
    client.post(f"/pipelines/{pipeline_id}/nodes", headers=headers, json={
        "node_type": "transform",
        "configuration": json.dumps({"operation": "drop_nulls"}),
        "sequence_index": 2
    })
    
    # 3. Load Node
    client.post(f"/pipelines/{pipeline_id}/nodes", headers=headers, json={
        "node_type": "load",
        "configuration": json.dumps({"data_source_id": target_id}),
        "sequence_index": 3
    })

    # Execute
    res = client.post(
        f"/pipelines/{pipeline_id}/executions", 
        headers=headers,
        json={"triggered_by": "test_user"}
    )
    assert res.status_code == 201
    execution = res.json()
    assert execution["status"] == "completed"
    assert execution["pipeline_id"] == pipeline_id
    assert execution["triggered_by"] == "test_user"
    execution_id = execution["id"]

    # Verify target file contents
    with open(target_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2  # Alice and Charlie. Bob was dropped because value=""
        assert rows[0]["name"] == "Alice"
        assert rows[1]["name"] == "Charlie"

    # Retrieve execution logs
    res = client.get(f"/pipelines/{pipeline_id}/executions/{execution_id}/logs", headers=headers)
    assert res.status_code == 200
    logs = res.json()
    
    assert any("Extracted 3 rows" in log["message"] for log in logs)
    assert any("Transformed 2 rows" in log["message"] for log in logs)
    assert any("Loaded 2 rows" in log["message"] for log in logs)


def test_execute_invalid_pipeline(client: TestClient) -> None:
    headers = _auth_headers(client)
    res = client.post(
        "/pipelines/invalid-id/executions", 
        headers=headers,
        json={"triggered_by": "test_user"}
    )
    assert res.status_code == 404

def test_execute_unsupported_node(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _create_project(client, headers)
    pipeline_id = _create_pipeline(client, headers, project_id)
    
    # Add an unsupported node
    client.post(f"/pipelines/{pipeline_id}/nodes", headers=headers, json={
        "node_type": "magical_unsupported_node",
        "configuration": "{}",
        "position_x": 0,
        "position_y": 0
    })

    # Execute
    res = client.post(
        f"/pipelines/{pipeline_id}/executions", 
        headers=headers,
        json={"triggered_by": "test_user"}
    )
    assert res.status_code == 201
    execution = res.json()
    assert execution["status"] == "failed"

    # Check logs
    res = client.get(f"/pipelines/{pipeline_id}/executions/{execution['id']}/logs", headers=headers)
    assert res.status_code == 200
    logs = res.json()
    assert any(log["level"] == "ERROR" and "Unsupported node type" in log["message"] for log in logs)


def test_execution_logs(client: TestClient, temp_csv_files: tuple[Path, Path]) -> None:
    headers = _auth_headers(client)
    project_id = _create_project(client, headers)
    pipeline_id = _create_pipeline(client, headers, project_id)
    
    source_path, _ = temp_csv_files
    source_id = _create_csv_data_source(client, headers, project_id, str(source_path), "Source")
    
    # Add a valid extract node
    client.post(f"/pipelines/{pipeline_id}/nodes", headers=headers, json={
        "node_type": "extract",
        "configuration": json.dumps({"data_source_id": source_id}),
        "sequence_index": 1
    })

    # Execute
    res = client.post(
        f"/pipelines/{pipeline_id}/executions", 
        headers=headers,
        json={"triggered_by": "test_user"}
    )
    execution_id = res.json()["id"]

    # Retrieve logs
    res = client.get(f"/pipelines/{pipeline_id}/executions/{execution_id}/logs", headers=headers)
    assert res.status_code == 200
    logs = res.json()

    # Total logs:
    # 1. Execution started
    # 2. Node started: extract
    # 3. Extracted 3 rows
    # 4. Node completed: extract
    # 5. Execution completed
    assert len(logs) == 5
    assert logs[0]["message"] == "Execution started"
    assert logs[1]["message"] == "Node started: extract"
    assert "Extracted" in logs[2]["message"]
    assert logs[3]["message"] == "Node completed: extract"
    assert logs[4]["message"] == "Execution completed"

    # Test invalid pipeline
    res = client.get(f"/pipelines/invalid-pipeline-id/executions/{execution_id}/logs", headers=headers)
    assert res.status_code == 404

    # Test invalid execution
    res = client.get(f"/pipelines/{pipeline_id}/executions/invalid-execution-id/logs", headers=headers)
    assert res.status_code == 404

    # Test execution mismatch
    other_pipeline_id = _create_pipeline(client, headers, project_id)
    res = client.get(f"/pipelines/{other_pipeline_id}/executions/{execution_id}/logs", headers=headers)
    assert res.status_code == 403

def test_execute_missing_source_fails(client: TestClient) -> None:
    headers = _auth_headers(client)
    project_id = _create_project(client, headers)
    pipeline_id = _create_pipeline(client, headers, project_id)
    
    # Extract node pointing to non-existent source
    client.post(f"/pipelines/{pipeline_id}/nodes", headers=headers, json={
        "node_type": "extract",
        "configuration": json.dumps({"data_source_id": "fake_id"}),
    })
    
    res = client.post(f"/pipelines/{pipeline_id}/executions", headers=headers, json={"triggered_by": "test"})
    execution = res.json()
    assert execution["status"] == "failed"
    assert "Data source fake_id not found" in execution["error_message"]
    
    logs = client.get(f"/pipelines/{pipeline_id}/executions/{execution['id']}/logs", headers=headers).json()
    assert any(log["level"] == "ERROR" and "Data source fake_id not found" in log["message"] for log in logs)
