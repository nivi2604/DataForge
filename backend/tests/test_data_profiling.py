"""
Tests for DataProfilingService.
All tests use real in-memory data — no fake metrics.
"""
import pytest
from app.services.data_profiling_service import DataProfilingService


def profile(data):
    return DataProfilingService.profile(data)


def test_empty_dataset():
    result = profile([])
    assert result["row_count"] == 0
    assert result["column_count"] == 0
    assert result["columns"] == {}


def test_row_count():
    data = [{"a": 1}, {"a": 2}, {"a": 3}]
    result = profile(data)
    assert result["row_count"] == 3


def test_column_count():
    data = [{"a": 1, "b": 2, "c": 3}]
    result = profile(data)
    assert result["column_count"] == 3


def test_duplicate_detection():
    data = [{"id": 1, "v": "x"}, {"id": 1, "v": "x"}, {"id": 2, "v": "y"}]
    result = profile(data)
    assert result["duplicate_row_count"] == 1
    assert result["duplicate_percentage"] == pytest.approx(33.33, abs=0.1)


def test_no_duplicates():
    data = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = profile(data)
    assert result["duplicate_row_count"] == 0


def test_missing_count():
    data = [{"a": None, "b": "x"}, {"a": 2, "b": "y"}]
    result = profile(data)
    col_a = result["columns"]["a"]
    assert col_a["missing_count"] == 1
    assert col_a["missing_percentage"] == 50.0


def test_unique_count():
    data = [{"x": "a"}, {"x": "b"}, {"x": "a"}]
    result = profile(data)
    assert result["columns"]["x"]["unique_count"] == 2


def test_inferred_type_integer():
    data = [{"n": "1"}, {"n": "2"}, {"n": "3"}]
    result = profile(data)
    assert result["columns"]["n"]["inferred_type"] == "integer"


def test_inferred_type_float():
    data = [{"n": "1.5"}, {"n": "2.3"}]
    result = profile(data)
    assert result["columns"]["n"]["inferred_type"] == "float"


def test_inferred_type_string():
    data = [{"s": "hello"}, {"s": "world"}]
    result = profile(data)
    assert result["columns"]["s"]["inferred_type"] == "string"


def test_numeric_min_max():
    data = [{"v": 10}, {"v": 5}, {"v": 20}]
    result = profile(data)
    col = result["columns"]["v"]
    assert col["min"] == 5.0
    assert col["max"] == 20.0


def test_numeric_mean():
    data = [{"v": 10}, {"v": 20}, {"v": 30}]
    result = profile(data)
    assert result["columns"]["v"]["mean"] == pytest.approx(20.0)


def test_numeric_median():
    data = [{"v": 10}, {"v": 20}, {"v": 30}]
    result = profile(data)
    assert result["columns"]["v"]["median"] == pytest.approx(20.0)


def test_string_min_max():
    data = [{"s": "banana"}, {"s": "apple"}, {"s": "cherry"}]
    result = profile(data)
    col = result["columns"]["s"]
    assert col["min"] == "apple"  # alphabetically first
    assert col["max"] == "cherry"


def test_sample_values_limited_to_5():
    data = [{"n": i} for i in range(20)]
    result = profile(data)
    assert len(result["columns"]["n"]["sample_values"]) <= 5


def test_result_structure():
    data = [{"id": 1, "name": "Alice"}]
    result = profile(data)
    assert "row_count" in result
    assert "column_count" in result
    assert "duplicate_row_count" in result
    assert "duplicate_percentage" in result
    assert "columns" in result
    for col_name, col_data in result["columns"].items():
        for key in ["inferred_type", "missing_count", "missing_percentage",
                    "unique_count", "uniqueness_percentage",
                    "min", "max", "mean", "median", "sample_values"]:
            assert key in col_data, f"Column '{col_name}' missing key '{key}'"


def test_multiple_column_types():
    data = [
        {"id": 1, "score": 95.5, "name": "Alice", "active": "true"},
        {"id": 2, "score": 88.0, "name": "Bob", "active": "false"},
    ]
    result = profile(data)
    assert result["columns"]["id"]["inferred_type"] == "integer"
    assert result["columns"]["score"]["inferred_type"] == "float"
    assert result["columns"]["name"]["inferred_type"] == "string"
