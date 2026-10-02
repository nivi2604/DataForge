import pytest
import json
import os
from unittest.mock import MagicMock
from app.services.execution_service import ExecutionService
from app.models.pipeline_node import PipelineNode
from app.models.data_source import DataSource
import app.models.project
import app.models.workspace
import app.models.organization
import app.models.user
import app.models.pipeline
import app.models.pipeline_execution
import app.models.execution_log
import app.models.pipeline_schedule
import app.models.pipeline_version
import app.models.github_connection
import app.models.github_pr_validation

@pytest.fixture
def exec_service():
    service = ExecutionService()
    # Mock _execute_extract so join/merge tests don't need real DB data sources.
    service._execute_extract = MagicMock()
    # Mock _log so transform unit tests don't require real pipeline_executions rows.
    service._log = MagicMock()
    return service

def test_drop_nulls(exec_service):
    data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": None},
        {"id": 3, "name": "Bob"},
        {"id": 4, "name": ""}
    ]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({"operation": "drop_nulls"})
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 3

def test_remove_duplicates(exec_service):
    data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
        {"id": 2, "name": "Bob", "age": 30} # Not a full duplicate unless columns specified
    ]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({"operation": "remove_duplicates"})
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert len(result) == 4
    
    # With columns specified
    node.configuration = json.dumps({"operation": "remove_duplicates", "columns": ["id"]})
    result = exec_service._execute_transform(node, "exec1", data)
    assert len(result) == 3
    assert [r["id"] for r in result] == [1, 2, 3]

def test_fill_missing(exec_service):
    data = [
        {"name": "Alice", "city": "Chennai"},
        {"name": "Bob", "city": None},
        {"name": "Charlie", "city": ""}
    ]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({"operation": "fill_missing", "column": "city", "value": "Unknown"})
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert len(result) == 3
    assert result[0]["city"] == "Chennai"
    assert result[1]["city"] == "Unknown"
    assert result[2]["city"] == "Unknown"

def test_standardize_values(exec_service):
    data = [
        {"name": "Alice", "city": "Chennai"},
        {"name": "Bob", "city": "Chenni"},
        {"name": "Charlie", "city": "Chennnai"}
    ]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({
            "operation": "standardize_values", 
            "column": "city", 
            "mapping": {
                "Chenni": "Chennai",
                "Chennnai": "Chennai"
            }
        })
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert len(result) == 3
    assert all(r["city"] == "Chennai" for r in result)

def test_merge(exec_service):
    left_data = [
        {"customer_id": 101, "name": "Alice"},
        {"customer_id": 102, "name": "Bob"}
    ]
    right_data = [
        {"customer_id": 101, "order": 500},
        {"customer_id": 102, "order": 700}
    ]
    
    exec_service._execute_extract.return_value = right_data
    
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({
            "operation": "merge",
            "right_source": "ds_1",
            "left_key": "customer_id",
            "right_key": "customer_id",
            "how": "left"
        })
    )
    
    result = exec_service._execute_transform(node, "exec1", left_data)
    assert len(result) == 2
    assert result[0]["order"] == 500
    assert result[1]["order"] == 700


def test_filter(exec_service):
    data = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": 30}
    ]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({"operation": "filter", "column": "value", "operator": ">=", "value": 20})
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert len(result) == 2
    assert result[0]["id"] == 2
    assert result[1]["id"] == 3

def test_rename_column(exec_service):
    data = [{"old_name": "Alice"}]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({"operation": "rename_column", "old_name": "old_name", "new_name": "name"})
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert "name" in result[0]
    assert "old_name" not in result[0]
    assert result[0]["name"] == "Alice"

def test_drop_columns(exec_service):
    data = [{"id": 1, "name": "Alice", "age": 30}]
    node = PipelineNode(
        id="node1",
        pipeline_id="pipe1",
        node_type="transform",
        configuration=json.dumps({"operation": "drop_columns", "columns": ["age", "id"]})
    )
    result = exec_service._execute_transform(node, "exec1", data)
    assert "age" not in result[0]
    assert "id" not in result[0]
    assert "name" in result[0]

def test_cast_type(exec_service):
    data = [{"id": "1", "valid": "True", "score": "10.5"}]
    node1 = PipelineNode(id="n1", pipeline_id="p1", node_type="transform", configuration=json.dumps({"operation": "cast_type", "column": "id", "target_type": "int"}))
    node2 = PipelineNode(id="n2", pipeline_id="p1", node_type="transform", configuration=json.dumps({"operation": "cast_type", "column": "valid", "target_type": "bool"}))
    node3 = PipelineNode(id="n3", pipeline_id="p1", node_type="transform", configuration=json.dumps({"operation": "cast_type", "column": "score", "target_type": "float"}))
    
    data = exec_service._execute_transform(node1, "e1", data)
    data = exec_service._execute_transform(node2, "e1", data)
    data = exec_service._execute_transform(node3, "e1", data)
    
    assert data[0]["id"] == 1
    assert data[0]["valid"] is True
    assert data[0]["score"] == 10.5

def test_joins(exec_service):
    left_data = [{"id": 1, "val": "A"}, {"id": 2, "val": "B"}]
    right_data = [{"id": 1, "extra": "X"}]
    exec_service._execute_extract.return_value = right_data
    
    node = PipelineNode(
        id="n1", pipeline_id="p1", node_type="transform",
        configuration=json.dumps({"operation": "inner_join", "right_source": "ds", "left_key": "id", "right_key": "id"})
    )
    res = exec_service._execute_transform(node, "e1", left_data)
    assert len(res) == 1
    assert res[0]["val"] == "A"
    assert res[0]["extra"] == "X"

def test_aggregations(exec_service):
    data = [
        {"cat": "A", "val": 10},
        {"cat": "A", "val": 20},
        {"cat": "B", "val": 15}
    ]
    node = PipelineNode(
        id="n1", pipeline_id="p1", node_type="transform",
        configuration=json.dumps({"operation": "sum", "group_columns": "cat", "agg_column": "val"})
    )
    res = exec_service._execute_transform(node, "e1", data)
    assert len(res) == 2
    for r in res:
        if r["cat"] == "A":
            assert r["val"] == 30
        else:
            assert r["val"] == 15
