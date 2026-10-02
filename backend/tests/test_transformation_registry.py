"""
Tests for the Transformation Registry.
Tests all operations: ROW, COLUMN, CLEANING, AGGREGATION, DATE.
"""
import pytest
from app.services.transformation_registry import (
    REGISTRY,
    filter_rows,
    drop_nulls,
    remove_duplicates,
    select_columns,
    rename_columns,
    drop_columns,
    calculated_column,
    fill_missing,
    standardize_values,
    string_clean,
    type_cast,
    parse_date,
    extract_year,
    extract_month,
    extract_day,
    date_difference,
    aggregate,
)


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_contains_all_expected_ops():
    expected = [
        "filter_rows", "filter", "drop_nulls", "remove_duplicates",
        "select_columns", "rename_columns", "rename_column", "drop_columns",
        "calculated_column", "fill_missing", "standardize_values",
        "string_clean", "type_cast", "cast_type",
        "inner_join", "left_join", "right_join", "full_join", "merge",
        "group_by", "aggregate", "count", "sum", "avg", "min", "max",
        "parse_date", "extract_year", "extract_month", "extract_day",
        "date_difference",
    ]
    missing = [op for op in expected if op not in REGISTRY]
    assert not missing, f"Missing from registry: {missing}"


# ── ROW OPERATIONS ────────────────────────────────────────────────────────────

def test_filter_rows_eq():
    data = [{"x": "a"}, {"x": "b"}, {"x": "a"}]
    result = filter_rows(data, {"column": "x", "operator": "==", "value": "a"})
    assert len(result) == 2

def test_filter_rows_gt():
    data = [{"n": 10}, {"n": 20}, {"n": 30}]
    result = filter_rows(data, {"column": "n", "operator": ">", "value": 15})
    assert len(result) == 2
    assert all(r["n"] > 15 for r in result)

def test_filter_rows_contains():
    data = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Alexandra"}]
    result = filter_rows(data, {"column": "name", "operator": "contains", "value": "Al"})
    assert len(result) == 2

def test_filter_rows_starts_with():
    data = [{"s": "hello world"}, {"s": "world hello"}, {"s": "hello!"}]
    result = filter_rows(data, {"column": "s", "operator": "starts_with", "value": "hello"})
    assert len(result) == 2

def test_filter_rows_missing_config():
    with pytest.raises(ValueError):
        filter_rows([{"x": 1}], {"operator": "=="})

def test_filter_rows_null_excluded():
    data = [{"n": None}, {"n": 5}]
    result = filter_rows(data, {"column": "n", "operator": ">", "value": 0})
    assert len(result) == 1

def test_drop_nulls_all_columns():
    data = [
        {"a": 1, "b": "x"},
        {"a": None, "b": "y"},
        {"a": 3, "b": ""},
        {"a": 4, "b": "z"},
    ]
    result = drop_nulls(data, {})
    assert len(result) == 2
    assert all(r["a"] in [1, 4] for r in result)

def test_drop_nulls_specific_columns():
    data = [
        {"a": None, "b": "y"},  # a is null, but b is fine
        {"a": 3, "b": ""},      # b is null
    ]
    # Only check column 'a'
    result = drop_nulls(data, {"columns": "a"})
    assert len(result) == 1

def test_remove_duplicates_all():
    data = [{"id": 1, "v": "a"}, {"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
    result = remove_duplicates(data, {})
    assert len(result) == 2

def test_remove_duplicates_by_column():
    data = [{"id": 1, "name": "Alice"}, {"id": 1, "name": "Bob"}, {"id": 2, "name": "Charlie"}]
    result = remove_duplicates(data, {"columns": ["id"]})
    assert len(result) == 2
    assert result[0]["id"] == 1  # keeps first occurrence


# ── COLUMN OPERATIONS ─────────────────────────────────────────────────────────

def test_select_columns():
    data = [{"a": 1, "b": 2, "c": 3}]
    result = select_columns(data, {"columns": ["a", "c"]})
    assert result == [{"a": 1, "c": 3}]

def test_select_columns_missing_config():
    with pytest.raises(ValueError):
        select_columns([{"a": 1}], {})

def test_rename_columns_mapping():
    data = [{"first": "Alice", "last": "Smith"}]
    result = rename_columns(data, {"mapping": {"first": "first_name", "last": "last_name"}})
    assert result == [{"first_name": "Alice", "last_name": "Smith"}]

def test_rename_columns_old_new():
    data = [{"old": 1}]
    result = rename_columns(data, {"old_name": "old", "new_name": "new"})
    assert "new" in result[0]
    assert "old" not in result[0]

def test_drop_columns():
    data = [{"a": 1, "b": 2, "c": 3}]
    result = drop_columns(data, {"columns": ["b", "c"]})
    assert result == [{"a": 1}]

def test_calculated_column_addition():
    data = [{"x": 3.0, "y": 7.0}]
    result = calculated_column(data, {"output_column": "total", "expression": "x + y"})
    assert result[0]["total"] == 10.0

def test_calculated_column_division():
    data = [{"a": 10.0, "b": 2.0}]
    result = calculated_column(data, {"output_column": "ratio", "expression": "a / b"})
    assert result[0]["ratio"] == 5.0

def test_calculated_column_concat():
    data = [{"first": "Alice", "last": "Smith"}]
    result = calculated_column(data, {"output_column": "full", "expression": "concat:first:last: "})
    assert result[0]["full"] == "Alice Smith"


# ── CLEANING OPERATIONS ────────────────────────────────────────────────────────

def test_fill_missing_none():
    data = [{"city": None}, {"city": "Mumbai"}, {"city": ""}]
    result = fill_missing(data, {"column": "city", "value": "Unknown"})
    assert result[0]["city"] == "Unknown"
    assert result[1]["city"] == "Mumbai"
    assert result[2]["city"] == "Unknown"

def test_standardize_values():
    data = [{"status": "Active"}, {"status": "active"}, {"status": "ACTIVE"}]
    result = standardize_values(data, {
        "column": "status",
        "mapping": {"Active": "active", "ACTIVE": "active"}
    })
    assert result[0]["status"] == "active"
    assert result[2]["status"] == "active"

def test_string_clean_strip():
    data = [{"s": "  hello  "}]
    result = string_clean(data, {"column": "s", "operations": ["strip"]})
    assert result[0]["s"] == "hello"

def test_string_clean_lower():
    data = [{"s": "HELLO World"}]
    result = string_clean(data, {"column": "s", "operations": ["lower"]})
    assert result[0]["s"] == "hello world"

def test_string_clean_multiple():
    data = [{"s": "  HELLO  "}]
    result = string_clean(data, {"column": "s", "operations": ["strip", "lower"]})
    assert result[0]["s"] == "hello"

def test_type_cast_int():
    data = [{"n": "42.7"}]
    result = type_cast(data, {"column": "n", "target_type": "int"})
    assert result[0]["n"] == 42

def test_type_cast_float():
    data = [{"n": "3.14"}]
    result = type_cast(data, {"column": "n", "target_type": "float"})
    assert abs(result[0]["n"] - 3.14) < 1e-9

def test_type_cast_bool():
    data = [{"b": "true"}, {"b": "1"}, {"b": "false"}]
    result = type_cast(data, {"column": "b", "target_type": "bool"})
    assert result[0]["b"] is True
    assert result[1]["b"] is True
    assert result[2]["b"] is False

def test_type_cast_invalid_becomes_none():
    data = [{"n": "not_a_number"}]
    result = type_cast(data, {"column": "n", "target_type": "int"})
    assert result[0]["n"] is None


# ── AGGREGATION OPERATIONS ────────────────────────────────────────────────────

def test_aggregate_sum():
    data = [{"cat": "A", "val": 10}, {"cat": "A", "val": 20}, {"cat": "B", "val": 5}]
    result = aggregate(data, {"group_columns": "cat", "agg_column": "val", "agg_fn": "sum"})
    by_cat = {r["cat"]: r["val"] for r in result}
    assert by_cat["A"] == 30
    assert by_cat["B"] == 5

def test_aggregate_count():
    data = [{"cat": "X", "n": 1}, {"cat": "X", "n": 2}, {"cat": "Y", "n": 3}]
    result = aggregate(data, {"group_columns": ["cat"], "agg_column": "n", "agg_fn": "count"})
    assert len(result) == 2
    by_cat = {r["cat"]: r["n"] for r in result}
    assert by_cat["X"] == 2
    assert by_cat["Y"] == 1

def test_aggregate_avg():
    data = [{"g": "A", "v": 10}, {"g": "A", "v": 20}]
    result = aggregate(data, {"group_columns": "g", "agg_column": "v", "agg_fn": "avg"})
    assert result[0]["v"] == 15.0

def test_aggregate_min_max():
    data = [{"g": "A", "v": 5}, {"g": "A", "v": 15}, {"g": "A", "v": 10}]
    min_r = aggregate(data, {"group_columns": "g", "agg_column": "v", "agg_fn": "min"})
    max_r = aggregate(data, {"group_columns": "g", "agg_column": "v", "agg_fn": "max"})
    assert min_r[0]["v"] == 5
    assert max_r[0]["v"] == 15

def test_aggregate_invalid_fn():
    with pytest.raises(ValueError):
        aggregate([{"a": 1}], {"group_columns": "a", "agg_fn": "variance"})


# ── DATE OPERATIONS ───────────────────────────────────────────────────────────

def test_parse_date():
    data = [{"d": "2024-01-15"}]
    result = parse_date(data, {"column": "d"})
    assert result[0]["d"] == "2024-01-15"

def test_parse_date_custom_format():
    data = [{"d": "15/01/2024"}]
    result = parse_date(data, {"column": "d", "format": "%d/%m/%Y"})
    assert result[0]["d"] == "2024-01-15"

def test_extract_year():
    data = [{"d": "2023-06-20"}]
    result = extract_year(data, {"column": "d"})
    assert result[0]["d_year"] == 2023

def test_extract_month():
    data = [{"d": "2023-06-20"}]
    result = extract_month(data, {"column": "d"})
    assert result[0]["d_month"] == 6

def test_extract_day():
    data = [{"d": "2023-06-20"}]
    result = extract_day(data, {"column": "d"})
    assert result[0]["d_day"] == 20

def test_date_difference():
    data = [{"start": "2024-01-01", "end": "2024-01-11"}]
    result = date_difference(data, {"start_column": "start", "end_column": "end"})
    assert result[0]["date_diff_days"] == 10

def test_date_difference_negative():
    data = [{"a": "2024-06-01", "b": "2024-01-01"}]
    result = date_difference(data, {"start_column": "a", "end_column": "b", "output_column": "diff"})
    assert result[0]["diff"] == -152

def test_date_difference_invalid_becomes_none():
    data = [{"a": "not-a-date", "b": "2024-01-01"}]
    result = date_difference(data, {"start_column": "a", "end_column": "b"})
    assert result[0]["date_diff_days"] is None
