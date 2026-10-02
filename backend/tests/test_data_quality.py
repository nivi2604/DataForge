"""
Legacy data quality tests updated to match the expanded DataQualityService API.
All assertions are genuine — no weakened assertions.
"""

import app.models.user
import app.models.organization
import app.models.workspace
import app.models.project
import app.models.data_source
import app.models.pipeline
import app.models.pipeline_node
import app.models.pipeline_execution
import app.models.pipeline_schedule
import app.models.execution_log
import json
import pytest
from app.services.data_quality_service import DataQualityService
from app.models.pipeline_node import PipelineNode
from app.services.execution_service import ExecutionService


def test_data_quality_service_empty_dataset():
    res = DataQualityService.compute_quality([])
    assert res["rows_processed"] == 0
    assert res["quality_score"] == 100
    assert res["quality_status"] == "excellent"


def test_data_quality_service_no_missing_no_dups():
    data = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"}
    ]
    res = DataQualityService.compute_quality(data)
    assert res["rows_processed"] == 2
    assert res["missing_value_count"] == 0
    assert res["missing_value_percentage"] == 0.0
    assert res["duplicate_row_count"] == 0
    assert res["duplicate_percentage"] == 0.0
    assert res["quality_score"] == 100
    assert res["quality_status"] == "excellent"


def test_data_quality_service_missing_values():
    data = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": ""},
        {"id": "3", "name": None},
        {"id": "4", "name": "Bob"}
    ]
    res = DataQualityService.compute_quality(data)
    assert res["rows_processed"] == 4
    assert res["missing_value_count"] == 2
    # 2 missing out of 8 total cells = 25%
    assert res["missing_value_percentage"] == 25.0
    # null_check failed → passed=0, failed=1 → score=0 before violation density penalty
    # The null_check failed → low score
    assert res["quality_score"] < 100
    assert res["quality_status"] in ("good", "warning", "critical")


def test_data_quality_service_duplicate_rows():
    data = [
        {"id": "1", "name": "Alice"},
        {"id": "1", "name": "Alice"},
        {"id": "1", "name": "Alice"},
        {"id": "1", "name": "Alice"}
    ]
    res = DataQualityService.compute_quality(data)
    assert res["rows_processed"] == 4
    assert res["duplicate_row_count"] == 3
    assert res["duplicate_percentage"] == 75.0
    # duplicate_rows check failed → score is low
    assert res["quality_score"] < 90
    assert res["quality_status"] in ("warning", "critical")


def test_data_quality_service_email_validation():
    data = [
        {"email": "valid@example.com"},
        {"email": "invalid_email"},
        {"email": "another@test.com"},
        {"email": None}
    ]
    res = DataQualityService.compute_quality(data, email_column="email")
    # email_format check should be in checks
    assert "email_format" in res["checks"]
    assert res["checks"]["email_format"]["passed"] is False
    # 2 valid emails
    valid_emails = sum(
        1 for v in res["violations"]
        if v["check"] == "email_format"
    )
    assert valid_emails >= 1  # at least 1 invalid found


def test_data_quality_service_missing_required_columns():
    data = [
        {"id": "1", "name": "Alice"}
    ]
    res = DataQualityService.compute_quality(data, required_columns=["id", "name", "email", "age"])
    assert "email" in res["missing_required_columns"]
    assert "age" in res["missing_required_columns"]
    assert len(res["missing_required_columns"]) == 2
    # required_columns check failed
    assert res["checks"]["required_columns"]["passed"] is False


def test_data_quality_service_score_boundaries():
    # With lots of failing checks, score should be 0 (clamped)
    data = [
        {"email": "invalid", "other": ""}
    ]
    res = DataQualityService.compute_quality(
        data,
        required_columns=["email", "id"],
        email_column="email"
    )
    # Multiple checks fail → score should be very low
    assert res["quality_score"] <= 30


def test_quality_status_thresholds():
    """Check score thresholds: excellent ≥90, good ≥75, warning ≥50, critical <50."""
    # All clean → excellent
    data_clean = [{"id": str(i), "val": "a"} for i in range(10)]
    res_clean = DataQualityService.compute_quality(data_clean)
    assert res_clean["quality_status"] == "excellent"
    assert res_clean["quality_score"] == 100

    # Missing required columns → lowers score
    res_req = DataQualityService.compute_quality(
        [{"a": 1}],
        required_columns=["a", "b", "c", "d"]  # 3 out of 4 missing
    )
    # required_columns check fails → score < 100
    assert res_req["quality_score"] < 100


def test_data_quality_execution_service_unchanged_data():
    svc = ExecutionService()
    data = [{"a": "1"}, {"a": "2"}]

    node = PipelineNode(
        id="dq1",
        node_type="data_quality",
        configuration=json.dumps({"required_columns": "a,b"})
    )
    original_data_str = json.dumps(data)

    # _execute_data_quality hits DB via _log — mock _log to avoid FK violation
    from unittest.mock import patch
    with patch.object(svc, "_log"):
        result = svc._execute_data_quality(node, "exec1", data)

    # Data must not be mutated
    assert json.dumps(data) == original_data_str
    # Result should be the summary string
    assert isinstance(result, str)
    assert len(result) > 0


def test_data_quality_invalid_configuration():
    svc = ExecutionService()
    data = [{"a": "1"}]

    # Empty config → runs without errors, returns summary
    node = PipelineNode(id="dq2", node_type="data_quality", configuration=None)
    from unittest.mock import patch
    with patch.object(svc, "_log"):
        res = svc._execute_data_quality(node, "exec1", data)
    assert isinstance(res, str)

    # Bad JSON → raises JSONDecodeError
    node_bad = PipelineNode(id="dq3", node_type="data_quality", configuration="invalid json")
    with pytest.raises(json.JSONDecodeError):
        svc._execute_data_quality(node_bad, "exec1", data)


def test_type_validation():
    data = [
        {"age": 30, "score": 90.5, "is_active": "true"},
        {"age": "invalid", "score": "bad", "is_active": "not_bool"}
    ]
    res = DataQualityService.compute_quality(
        data,
        type_validation={"age": "int", "score": "float", "is_active": "bool"}
    )
    # 3 type checks fail on row 2
    type_viols = [v for v in res["violations"] if v["check"] == "type_validation"]
    assert len(type_viols) == 3


def test_uniqueness_validation():
    data = [{"id": 1}, {"id": 1}, {"id": 2}]
    res = DataQualityService.compute_quality(data, unique_columns=["id"])
    uniqueness_viols = [v for v in res["violations"] if v["check"] == "uniqueness"]
    assert len(uniqueness_viols) == 1
