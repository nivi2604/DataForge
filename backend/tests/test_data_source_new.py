import pytest
import os
import json
import pandas as pd
from pathlib import Path
from app.services.data_source_service import DataSourceService
from app.services.execution_service import ExecutionService
from app.models.pipeline_node import PipelineNode
from app.models.data_source import DataSource

class MockDataSourceRepo:
    def __init__(self):
        self.sources = {}
        
    def get_data_source_by_id(self, ds_id):
        return self.sources.get(ds_id)
        
    def update_data_source(self, ds_id, data):
        self.sources[ds_id] = data
        return data

class MockExecutionService(ExecutionService):
    def __init__(self, repo):
        self.data_source_repository = repo

@pytest.fixture
def tmp_files(tmp_path):
    # CSV
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name\n1,Alice\n2,Bob")
    
    # JSON
    json_file = tmp_path / "test.json"
    json_file.write_text('[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]')
    
    # Invalid JSON
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text('{"id": 1, "name": "Alice"}') # Not a list
    
    # Parquet
    parquet_file = tmp_path / "test.parquet"
    df = pd.DataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
    df.to_parquet(parquet_file)
    
    return {
        "csv": str(csv_file),
        "json": str(json_file),
        "invalid_json": str(invalid_json_file),
        "parquet": str(parquet_file)
    }

def test_extract_and_load_json(tmp_files):
    repo = MockDataSourceRepo()
    repo.sources["json_src"] = DataSource(id="json_src", type="JSON", connection_details=json.dumps({"path": tmp_files["json"]}))
    
    svc = MockExecutionService(repo)
    node = PipelineNode(configuration=json.dumps({"data_source_id": "json_src"}))
    
    data = svc._execute_extract(node, "exec1")
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
    
    out_path = str(Path(tmp_files["json"]).parent / "out.json")
    repo.sources["json_out"] = DataSource(id="json_out", type="JSON", connection_details=json.dumps({"path": out_path}))
    load_node = PipelineNode(configuration=json.dumps({"data_source_id": "json_out"}))
    
    svc._execute_load(load_node, "exec1", data)
    assert Path(out_path).exists()
    assert len(json.loads(Path(out_path).read_text())) == 2

def test_extract_and_load_parquet(tmp_files):
    repo = MockDataSourceRepo()
    repo.sources["pq_src"] = DataSource(id="pq_src", type="Parquet", connection_details=json.dumps({"path": tmp_files["parquet"]}))
    
    svc = MockExecutionService(repo)
    node = PipelineNode(configuration=json.dumps({"data_source_id": "pq_src"}))
    
    data = svc._execute_extract(node, "exec1")
    assert len(data) == 2
    assert data[1]["name"] == "Bob"
    
    out_path = str(Path(tmp_files["parquet"]).parent / "out.parquet")
    repo.sources["pq_out"] = DataSource(id="pq_out", type="Parquet", connection_details=json.dumps({"path": out_path}))
    load_node = PipelineNode(configuration=json.dumps({"data_source_id": "pq_out"}))
    
    svc._execute_load(load_node, "exec1", data)
    assert Path(out_path).exists()
    df = pd.read_parquet(out_path)
    assert len(df) == 2

def test_invalid_json(tmp_files):
    repo = MockDataSourceRepo()
    repo.sources["invalid_json"] = DataSource(id="invalid_json", type="JSON", connection_details=json.dumps({"path": tmp_files["invalid_json"]}))
    svc = MockExecutionService(repo)
    node = PipelineNode(configuration=json.dumps({"data_source_id": "invalid_json"}))
    
    with pytest.raises(ValueError, match="must be a list"):
        svc._execute_extract(node, "exec1")

def test_missing_file_extraction():
    repo = MockDataSourceRepo()
    repo.sources["missing"] = DataSource(id="missing", type="CSV", connection_details=json.dumps({"path": "/does/not/exist.csv"}))
    svc = MockExecutionService(repo)
    node = PipelineNode(configuration=json.dumps({"data_source_id": "missing"}))
    
    with pytest.raises(ValueError, match="Invalid or missing CSV path"):
        svc._execute_extract(node, "exec1")

def test_probe_connection_json(tmp_files):
    svc = DataSourceService()
    # Valid
    svc._probe_connection("JSON", {"path": tmp_files["json"]})
    
    # Invalid json structure
    with pytest.raises(ValueError, match="JSON array"):
        svc._probe_connection("JSON", {"path": tmp_files["invalid_json"]})
        
    # Missing
    with pytest.raises(ValueError, match="does not exist"):
        svc._probe_connection("JSON", {"path": "/no/path.json"})

def test_probe_connection_parquet(tmp_files):
    svc = DataSourceService()
    # Valid
    svc._probe_connection("Parquet", {"path": tmp_files["parquet"]})
    
    # Invalid (use json file as parquet)
    with pytest.raises(ValueError, match="not valid Parquet"):
        svc._probe_connection("Parquet", {"path": tmp_files["json"]})
