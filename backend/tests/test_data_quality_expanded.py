"""
Tests for the expanded DataQualityService.
Covers: required columns, nulls, duplicates, uniqueness,
        type validation, range validation, allowed values,
        regex/pattern validation, schema validation.
"""
import pytest
from app.services.data_quality_service import DataQualityService


def dq(data, **kwargs):
    """Shorthand to call compute_quality."""
    return DataQualityService.compute_quality(data, **kwargs)


# ── Empty data ────────────────────────────────────────────────────────────────

def test_empty_dataset_returns_100():
    result = dq([])
    assert result["rows_processed"] == 0
    assert result["score"] == 100
    assert result["quality_status"] == "excellent"
    assert result["violations"] == []


# ── Null / completeness ────────────────────────────────────────────────────────

def test_no_nulls_no_penalty():
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    result = dq(data)
    assert result["missing_value_count"] == 0
    assert result["score"] == 100

def test_nulls_detected():
    data = [{"id": None, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    result = dq(data)
    assert result["missing_value_count"] == 1
    assert result["missing_value_percentage"] == 25.0

def test_null_check_produces_violation():
    data = [{"a": None}]
    result = dq(data)
    assert any(v["check"] == "null_check" for v in result["violations"])


# ── Duplicate rows ─────────────────────────────────────────────────────────────

def test_no_duplicates():
    data = [{"id": 1}, {"id": 2}]
    result = dq(data)
    assert result["duplicate_row_count"] == 0

def test_duplicates_detected():
    data = [{"id": 1, "v": "x"}, {"id": 1, "v": "x"}, {"id": 2, "v": "y"}]
    result = dq(data)
    assert result["duplicate_row_count"] == 1
    assert any(v["check"] == "duplicate_rows" for v in result["violations"])


# ── Required columns ──────────────────────────────────────────────────────────

def test_required_columns_present():
    data = [{"id": 1, "email": "a@b.com"}]
    result = dq(data, required_columns=["id", "email"])
    assert result["checks"]["required_columns"]["passed"] is True

def test_required_columns_missing():
    data = [{"id": 1}]
    result = dq(data, required_columns=["id", "email"])
    assert result["checks"]["required_columns"]["passed"] is False
    assert "email" in result["missing_required_columns"]

def test_required_columns_comma_string():
    data = [{"id": 1, "name": "x"}]
    result = dq(data, required_columns="id,name")
    assert result["checks"]["required_columns"]["passed"] is True


# ── Uniqueness ────────────────────────────────────────────────────────────────

def test_unique_check_pass():
    data = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = dq(data, unique_columns=["id"])
    assert result["checks"]["unique_id"]["passed"] is True

def test_unique_check_fail():
    data = [{"id": 1}, {"id": 1}, {"id": 2}]
    result = dq(data, unique_columns=["id"])
    assert result["checks"]["unique_id"]["passed"] is False
    assert any(v["column"] == "id" for v in result["violations"])


# ── Type validation ────────────────────────────────────────────────────────────

def test_type_validation_int_pass():
    data = [{"age": 25}, {"age": 30}]
    result = dq(data, type_validation={"age": "int"})
    assert result["checks"]["type_age"]["passed"] is True

def test_type_validation_int_fail():
    data = [{"age": "not_a_number"}, {"age": 25}]
    result = dq(data, type_validation={"age": "int"})
    assert result["checks"]["type_age"]["passed"] is False

def test_type_validation_float():
    data = [{"score": "9.5"}, {"score": "8.0"}]
    result = dq(data, type_validation={"score": "float"})
    assert result["checks"]["type_score"]["passed"] is True

def test_type_validation_bool():
    data = [{"active": "true"}, {"active": "false"}, {"active": "yes"}]
    result = dq(data, type_validation={"active": "bool"})
    assert result["checks"]["type_active"]["passed"] is True

def test_type_validation_bool_fail():
    data = [{"active": "maybe"}]
    result = dq(data, type_validation={"active": "bool"})
    assert result["checks"]["type_active"]["passed"] is False


# ── Range validation ──────────────────────────────────────────────────────────

def test_range_validation_pass():
    data = [{"age": 25}, {"age": 30}, {"age": 18}]
    result = dq(data, range_validation={"age": {"min": 18, "max": 100}})
    assert result["checks"]["range_age"]["passed"] is True

def test_range_validation_below_min():
    data = [{"age": 10}]
    result = dq(data, range_validation={"age": {"min": 18, "max": 100}})
    assert result["checks"]["range_age"]["passed"] is False
    assert any("< min" in v["reason"] for v in result["violations"])

def test_range_validation_above_max():
    data = [{"score": 150.0}]
    result = dq(data, range_validation={"score": {"min": 0, "max": 100}})
    assert result["checks"]["range_score"]["passed"] is False
    assert any("> max" in v["reason"] for v in result["violations"])

def test_range_validation_non_numeric():
    data = [{"val": "abc"}]
    result = dq(data, range_validation={"val": {"min": 0, "max": 10}})
    assert result["checks"]["range_val"]["passed"] is False


# ── Allowed values ─────────────────────────────────────────────────────────────

def test_allowed_values_pass():
    data = [{"status": "active"}, {"status": "inactive"}]
    result = dq(data, allowed_values={"status": ["active", "inactive", "pending"]})
    assert result["checks"]["allowed_status"]["passed"] is True

def test_allowed_values_fail():
    data = [{"status": "deleted"}]
    result = dq(data, allowed_values={"status": ["active", "inactive"]})
    assert result["checks"]["allowed_status"]["passed"] is False
    assert any("not in allowed set" in v["reason"] for v in result["violations"])


# ── Pattern / regex validation ─────────────────────────────────────────────────

def test_pattern_validation_email_pass():
    data = [{"email": "user@example.com"}]
    result = dq(data, pattern_validation={"email": r"^[^@]+@[^@]+\.[^@]+$"})
    assert result["checks"]["pattern_email"]["passed"] is True

def test_pattern_validation_email_fail():
    data = [{"email": "not-an-email"}]
    result = dq(data, pattern_validation={"email": r"^[^@]+@[^@]+\.[^@]+$"})
    assert result["checks"]["pattern_email"]["passed"] is False
    assert any(v["column"] == "email" for v in result["violations"])

def test_pattern_validation_invalid_regex():
    data = [{"x": "abc"}]
    result = dq(data, pattern_validation={"x": "[invalid regex("})
    assert result["checks"]["pattern_x"]["passed"] is False


# ── Schema validation ─────────────────────────────────────────────────────────

def test_schema_required_column_present():
    data = [{"id": 1, "name": "Alice"}]
    result = dq(data, schema={"id": {"type": "int", "required": True}})
    assert result["checks"]["schema_id"]["passed"] is True

def test_schema_required_column_missing():
    data = [{"name": "Alice"}]
    result = dq(data, schema={"id": {"required": True}})
    assert result["checks"]["schema_id"]["passed"] is False
    assert any("schema" in v["check"] for v in result["violations"])

def test_schema_type_mismatch():
    data = [{"age": "not_int"}]
    result = dq(data, schema={"age": {"type": "int"}})
    assert result["checks"]["schema_age"]["passed"] is False

def test_schema_range():
    data = [{"age": 15}]
    result = dq(data, schema={"age": {"type": "int", "min": 18, "max": 100}})
    assert result["checks"]["schema_age"]["passed"] is False
    assert any("min" in v["reason"] for v in result["violations"])

def test_schema_allowed_values():
    data = [{"tier": "premium"}]
    result = dq(data, schema={"tier": {"allowed_values": ["free", "pro", "enterprise"]}})
    assert result["checks"]["schema_tier"]["passed"] is False


# ── Combined checks ────────────────────────────────────────────────────────────

def test_combined_checks_all_pass():
    data = [
        {"id": 1, "email": "alice@example.com", "age": 25, "status": "active"},
        {"id": 2, "email": "bob@example.com", "age": 30, "status": "inactive"},
    ]
    result = dq(
        data,
        required_columns=["id", "email"],
        unique_columns=["id"],
        type_validation={"age": "int"},
        range_validation={"age": {"min": 18, "max": 100}},
        allowed_values={"status": ["active", "inactive"]},
        pattern_validation={"email": r"^[^@]+@[^@]+\.[^@]+$"},
    )
    # All checks should pass → score should be high
    assert result["failed"] == 0
    assert result["score"] >= 90


# ── Result structure ──────────────────────────────────────────────────────────

def test_result_has_required_keys():
    result = dq([{"a": 1}])
    for key in ["rows_processed", "score", "quality_status", "passed", "failed",
                "checks", "violations", "summary"]:
        assert key in result, f"Missing key: {key}"

def test_quality_status_thresholds():
    # Manufacture a result by checking a dataset with only nulls
    data = [{"a": None, "b": None} for _ in range(100)]
    result = dq(data)
    # Should penalise heavily — status should be warning or critical
    assert result["quality_status"] in ("warning", "critical")


# ── format_quality_result ─────────────────────────────────────────────────────

def test_format_quality_result_returns_string():
    data = [{"id": 1, "name": "Alice"}]
    result = dq(data)
    formatted = DataQualityService.format_quality_result(result)
    assert isinstance(formatted, str)
    assert len(formatted) > 0
