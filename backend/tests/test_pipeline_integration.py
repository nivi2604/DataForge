import pytest
import os
import json
import csv
from pathlib import Path

from app.services.execution_service import ExecutionService
from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.models.data_source import DataSource
from app.models.project import Project
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
from app.db.session import SessionLocal

@pytest.fixture
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_pipeline_integration(test_db, tmp_path):
    # Setup controlled messy dataset
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    
    with open(input_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "city"])
        writer.writerow(["1", "Alice", "Chennai"])
        writer.writerow(["2", "Bob", "Chenni"])
        writer.writerow(["2", "Bob", "Chenni"])
        writer.writerow(["3", "Charlie", ""])
        writer.writerow(["4", "David", "Chennnai"])
        
    # Setup DB records
    project = Project(id="proj_integration", name="Test Proj")
    test_db.add(project)
    test_db.commit()
    
    ds_in = DataSource(id="ds_in", project_id="proj_integration", name="DS In", type="CSV", connection_details=json.dumps({"path": str(input_file)}))
    ds_out = DataSource(id="ds_out", project_id="proj_integration", name="DS Out", type="CSV", connection_details=json.dumps({"path": str(output_file)}))
    test_db.add_all([ds_in, ds_out])
    
    pipe = Pipeline(id="pipe_integration", project_id="proj_integration", name="Integration Pipe")
    test_db.add(pipe)
    test_db.commit()
    
    # Create Pipeline Nodes
    nodes = [
        PipelineNode(
            id="node_extract", pipeline_id="pipe_integration", node_type="extract", sequence_index=1,
            configuration=json.dumps({"data_source_id": "ds_in"})
        ),
        PipelineNode(
            id="node_remove_dup", pipeline_id="pipe_integration", node_type="transform", sequence_index=2,
            configuration=json.dumps({"operation": "remove_duplicates"})
        ),
        PipelineNode(
            id="node_std_val", pipeline_id="pipe_integration", node_type="transform", sequence_index=3,
            configuration=json.dumps({"operation": "standardize_values", "column": "city", "mapping": {"Chenni": "Chennai", "Chennnai": "Chennai"}})
        ),
        PipelineNode(
            id="node_fill_miss", pipeline_id="pipe_integration", node_type="transform", sequence_index=4,
            configuration=json.dumps({"operation": "fill_missing", "column": "city", "value": "Unknown"})
        ),
        PipelineNode(
            id="node_dq", pipeline_id="pipe_integration", node_type="data_quality", sequence_index=5,
            configuration=json.dumps({"required_columns": "id,name,city"})
        ),
        PipelineNode(
            id="node_load", pipeline_id="pipe_integration", node_type="load", sequence_index=6,
            configuration=json.dumps({"data_source_id": "ds_out"})
        )
    ]
    test_db.add_all(nodes)
    test_db.commit()
    
    # Run the pipeline
    service = ExecutionService()
    
    # We must patch get_pipeline, list_pipeline_nodes to use the test db or the repositories used by ExecutionService
    # ExecutionService instantiates repositories. They create their own db sessions via get_db().
    # Because of `autouse=True` clear_repositories fixture, the database dataforge_test is clean. 
    # Since ExecutionService creates its own session, data committed here is visible to it.
    
    # Simulate execution via payload
    from app.schemas.execution import ExecutePipelineRequest
    payload = ExecutePipelineRequest(triggered_by="manual")
    
    execution = service.execute_pipeline(pipeline_id="pipe_integration", payload=payload)
    
    assert execution.status == "completed"
    
    # Check execution logs for data quality results
    logs = service.get_execution_logs("pipe_integration", execution.id)
    dq_log = next(
        (log for log in logs if "Processed" in log.message and "checks passed" in log.message),
        None
    )
    # Fall back to old format check if needed
    if dq_log is None:
        dq_log = next(
            (log for log in logs if "Data Quality:" in log.message),
            None
        )
    assert dq_log is not None, f"No DQ log found. Logs: {[l.message for l in logs]}"
    
    # Verify the processed output
    assert output_file.exists()
    
    with open(output_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        results = list(reader)
        
    assert len(results) == 4
    assert [r["id"] for r in results] == ["1", "2", "3", "4"]
    assert results[0]["city"] == "Chennai"
    assert results[1]["city"] == "Chennai"  # from Chenni
    assert results[2]["city"] == "Unknown"  # from ""
    assert results[3]["city"] == "Chennai"  # from Chennnai
    
    # Verify no duplicates
    seen = set()
    for row in results:
        key = tuple(row.items())
        assert key not in seen, f"Duplicate found: {row}"
        seen.add(key)
