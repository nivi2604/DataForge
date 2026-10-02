"""
DataForge Transformation Registry
===================================
Each transformation is a standalone function that:
  - validates its own configuration
  - produces deterministic output
  - fails safely with descriptive errors

All functions have the signature:
    transform(data: list[dict], config: dict) -> list[dict]

The registry maps operation names to handler functions.
To add a new transformation: implement a function and register it.
"""

from __future__ import annotations

import re
from datetime import datetime, date
from typing import Callable

import pandas as pd

# ─── Type alias ──────────────────────────────────────────────────────────────

TransformFn = Callable[[list[dict], dict], list[dict]]
REGISTRY: dict[str, TransformFn] = {}


def register(name: str) -> Callable[[TransformFn], TransformFn]:
    """Decorator to register a transformation handler."""
    def decorator(fn: TransformFn) -> TransformFn:
        REGISTRY[name] = fn
        return fn
    return decorator


def get_transform(name: str) -> TransformFn | None:
    return REGISTRY.get(name)


def list_transforms() -> list[str]:
    return sorted(REGISTRY.keys())


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require(config: dict, *keys: str, operation: str) -> None:
    for k in keys:
        if k not in config or config[k] is None or config[k] == "":
            raise ValueError(f"[{operation}] Missing required config key: '{k}'")


def _split_columns(value) -> list[str]:
    if isinstance(value, list):
        return [str(c).strip() for c in value if str(c).strip()]
    if isinstance(value, str):
        return [c.strip() for c in value.split(",") if c.strip()]
    return []


def _to_df(data: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)


def _from_df(df: pd.DataFrame) -> list[dict]:
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")


# ─── ROW OPERATIONS ──────────────────────────────────────────────────────────

@register("filter_rows")
def filter_rows(data: list[dict], config: dict) -> list[dict]:
    """
    Filter rows where column satisfies operator comparison against value.
    Operators: ==, !=, >, <, >=, <=, contains, not_contains, starts_with, ends_with
    """
    _require(config, "column", "operator", operation="filter_rows")
    column = config["column"]
    operator = config["operator"]
    value = config.get("value")
    if value is None:
        raise ValueError("[filter_rows] 'value' is required")

    result = []
    for row in data:
        raw = row.get(column)
        if raw is None:
            continue
        match = False
        try:
            if operator == "==":
                match = str(raw) == str(value)
            elif operator == "!=":
                match = str(raw) != str(value)
            elif operator in (">", "<", ">=", "<="):
                fraw, fval = float(raw), float(value)
                if operator == ">":   match = fraw > fval
                elif operator == "<": match = fraw < fval
                elif operator == ">=": match = fraw >= fval
                elif operator == "<=": match = fraw <= fval
            elif operator == "contains":
                match = str(value) in str(raw)
            elif operator == "not_contains":
                match = str(value) not in str(raw)
            elif operator == "starts_with":
                match = str(raw).startswith(str(value))
            elif operator == "ends_with":
                match = str(raw).endswith(str(value))
            else:
                raise ValueError(f"[filter_rows] Unknown operator: {operator}")
        except (ValueError, TypeError):
            pass  # type mismatch → row excluded
        if match:
            result.append(row)
    return result


# Keep legacy alias
@register("filter")
def _filter_alias(data: list[dict], config: dict) -> list[dict]:
    return filter_rows(data, config)


@register("drop_nulls")
def drop_nulls(data: list[dict], config: dict) -> list[dict]:
    """
    Remove rows where any column (or specified columns) is null/empty.
    Config: columns (optional) — list or comma-separated string
    """
    columns = _split_columns(config.get("columns", []))
    if columns:
        return [
            row for row in data
            if all(row.get(c) is not None and str(row.get(c)).strip() != "" for c in columns)
        ]
    return [
        row for row in data
        if all(v is not None and str(v).strip() != "" for v in row.values())
    ]


@register("remove_duplicates")
def remove_duplicates(data: list[dict], config: dict) -> list[dict]:
    """
    Remove duplicate rows.
    Config: columns (optional) — deduplicate on these columns only
    """
    columns = _split_columns(config.get("columns", []))
    seen: set = set()
    result = []
    for row in data:
        if columns:
            key = tuple(row.get(c) for c in columns)
        else:
            try:
                key = tuple(sorted(
                    (k, v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
                    for k, v in row.items()
                ))
            except TypeError:
                key = str(row)
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


# ─── COLUMN OPERATIONS ────────────────────────────────────────────────────────

@register("select_columns")
def select_columns(data: list[dict], config: dict) -> list[dict]:
    """
    Keep only specified columns.
    Config: columns — list or comma-separated string (required)
    """
    columns = _split_columns(config.get("columns", []))
    if not columns:
        raise ValueError("[select_columns] 'columns' is required")
    return [{k: row[k] for k in columns if k in row} for row in data]


@register("rename_columns")
def rename_columns(data: list[dict], config: dict) -> list[dict]:
    """
    Rename one or more columns.
    Config: mapping — dict { old_name: new_name }
    """
    mapping: dict = config.get("mapping", {})
    if not mapping:
        # Legacy single-column form
        old = config.get("old_name")
        new = config.get("new_name")
        if old and new:
            mapping = {old: new}
        else:
            raise ValueError("[rename_columns] 'mapping' (dict) or 'old_name'+'new_name' required")

    result = []
    for row in data:
        new_row = {}
        for k, v in row.items():
            new_key = mapping.get(k, k)
            new_row[new_key] = v
        result.append(new_row)
    return result


# Legacy alias (single rename)
@register("rename_column")
def _rename_alias(data: list[dict], config: dict) -> list[dict]:
    return rename_columns(data, config)


@register("drop_columns")
def drop_columns(data: list[dict], config: dict) -> list[dict]:
    """
    Remove specified columns.
    Config: columns — list or comma-separated string (required)
    """
    columns = _split_columns(config.get("columns", []))
    if not columns:
        raise ValueError("[drop_columns] 'columns' is required")
    for row in data:
        for col in columns:
            row.pop(col, None)
    return data


@register("calculated_column")
def calculated_column(data: list[dict], config: dict) -> list[dict]:
    """
    Add a new column computed from an expression.
    Config:
        output_column (str) — name of new column
        expression (str) — one of:
            "col_a + col_b" (numeric addition)
            "col_a - col_b"
            "col_a * col_b"
            "col_a / col_b"
            "concat:col_a:col_b:separator" (string concatenation)
    """
    _require(config, "output_column", "expression", operation="calculated_column")
    out_col = config["output_column"]
    expr = config["expression"]

    # Parse expression: operator form "col_a OP col_b"
    ops = [("+", lambda a, b: a + b), ("-", lambda a, b: a - b),
           ("*", lambda a, b: a * b), ("/", lambda a, b: a / b if b != 0 else None)]

    parsed_op = None
    col_a, col_b, fn = None, None, None
    for sym, op_fn in ops:
        if sym in expr:
            parts = [p.strip() for p in expr.split(sym, 1)]
            if len(parts) == 2:
                col_a, col_b = parts[0], parts[1]
                fn = op_fn
                parsed_op = sym
                break

    if expr.startswith("concat:"):
        parts = expr.split(":")
        cols_to_concat = parts[1:-1]
        separator = parts[-1] if len(parts) > 2 else ""
        for row in data:
            vals = [str(row.get(c, "")) for c in cols_to_concat]
            row[out_col] = separator.join(vals)
        return data

    if not parsed_op:
        raise ValueError(
            f"[calculated_column] Cannot parse expression: '{expr}'. "
            "Use 'col_a OP col_b' (OP = +, -, *, /) or 'concat:col_a:col_b:sep'"
        )

    for row in data:
        try:
            a = float(row.get(col_a))
            b = float(row.get(col_b))
            row[out_col] = fn(a, b)
        except (TypeError, ValueError):
            row[out_col] = None
    return data


# ─── CLEANING OPERATIONS ──────────────────────────────────────────────────────

@register("fill_missing")
def fill_missing(data: list[dict], config: dict) -> list[dict]:
    """
    Fill null/empty values in a column.
    Config: column (str), value (any)
    """
    _require(config, "column", operation="fill_missing")
    column = config["column"]
    fill_value = config.get("value")
    for row in data:
        if row.get(column) is None or str(row.get(column)).strip() == "":
            row[column] = fill_value
    return data


@register("standardize_values")
def standardize_values(data: list[dict], config: dict) -> list[dict]:
    """
    Replace values in a column using a lookup mapping.
    Config: column (str), mapping (dict)
    """
    _require(config, "column", operation="standardize_values")
    column = config["column"]
    mapping: dict = config.get("mapping")
    if mapping is None:
        raise ValueError("[standardize_values] 'mapping' (dict) is required")

    for row in data:
        val = row.get(column)
        if val in mapping:
            row[column] = mapping[val]
        elif str(val) in mapping:
            row[column] = mapping[str(val)]
    return data


@register("string_clean")
def string_clean(data: list[dict], config: dict) -> list[dict]:
    """
    Clean string values in a column.
    Config:
        column (str)
        operations (list[str]) — any of:
            strip, lower, upper, title, remove_whitespace, remove_special_chars
    """
    _require(config, "column", operation="string_clean")
    column = config["column"]
    operations: list[str] = config.get("operations", ["strip"])
    if isinstance(operations, str):
        operations = [o.strip() for o in operations.split(",")]

    def apply_ops(val: str) -> str:
        for op in operations:
            if op == "strip":
                val = val.strip()
            elif op == "lower":
                val = val.lower()
            elif op == "upper":
                val = val.upper()
            elif op == "title":
                val = val.title()
            elif op == "remove_whitespace":
                val = re.sub(r"\s+", " ", val).strip()
            elif op == "remove_special_chars":
                val = re.sub(r"[^a-zA-Z0-9\s]", "", val)
        return val

    for row in data:
        val = row.get(column)
        if val is not None and str(val).strip() != "":
            row[column] = apply_ops(str(val))
    return data


@register("type_cast")
def type_cast(data: list[dict], config: dict) -> list[dict]:
    """
    Cast a column to a target type.
    Config: column (str), target_type (str: int|float|str|bool)
    """
    _require(config, "column", "target_type", operation="type_cast")
    column = config["column"]
    target_type = config["target_type"]
    for row in data:
        val = row.get(column)
        if val is not None:
            try:
                if target_type == "int":
                    row[column] = int(float(val))
                elif target_type == "float":
                    row[column] = float(val)
                elif target_type == "str":
                    row[column] = str(val)
                elif target_type == "bool":
                    row[column] = str(val).lower() in ("true", "1", "yes", "y", "t")
                else:
                    raise ValueError(f"Unknown target_type: {target_type}")
            except (ValueError, TypeError):
                row[column] = None
    return data


# Legacy alias
@register("cast_type")
def _cast_alias(data: list[dict], config: dict) -> list[dict]:
    return type_cast(data, config)


# ─── RELATIONAL OPERATIONS ───────────────────────────────────────────────────
# These are implemented in execution_service.py because they need to call
# _execute_extract. The registry stubs them so they appear in list_transforms().

@register("inner_join")
def _inner_join_stub(data: list[dict], config: dict) -> list[dict]:
    raise NotImplementedError("inner_join must be executed via ExecutionService")

@register("left_join")
def _left_join_stub(data: list[dict], config: dict) -> list[dict]:
    raise NotImplementedError("left_join must be executed via ExecutionService")

@register("right_join")
def _right_join_stub(data: list[dict], config: dict) -> list[dict]:
    raise NotImplementedError("right_join must be executed via ExecutionService")

@register("full_join")
def _full_join_stub(data: list[dict], config: dict) -> list[dict]:
    raise NotImplementedError("full_join must be executed via ExecutionService")

@register("merge")
def _merge_stub(data: list[dict], config: dict) -> list[dict]:
    raise NotImplementedError("merge must be executed via ExecutionService")


# ─── AGGREGATION OPERATIONS ───────────────────────────────────────────────────

def _aggregate(data: list[dict], config: dict, agg_fn: str) -> list[dict]:
    group_columns = _split_columns(config.get("group_columns", []))
    if not group_columns:
        raise ValueError(f"[{agg_fn}] 'group_columns' is required")

    agg_column = config.get("agg_column")
    df = _to_df(data)

    for col in group_columns:
        if col not in df.columns:
            raise ValueError(f"[{agg_fn}] group column '{col}' not found in data")

    if agg_fn == "group_by":
        df["__count"] = 1
        result_df = df.groupby(group_columns, as_index=False)["__count"].sum()
        result_df = result_df.rename(columns={"__count": "count"})
    else:
        if not agg_column:
            raise ValueError(f"[{agg_fn}] 'agg_column' is required")
        if agg_column not in df.columns:
            raise ValueError(f"[{agg_fn}] agg column '{agg_column}' not found in data")
        df[agg_column] = pd.to_numeric(df[agg_column], errors="coerce")
        agg_map = {"count": "count", "sum": "sum", "avg": "mean", "min": "min", "max": "max"}
        result_df = df.groupby(group_columns, as_index=False)[agg_column].agg(agg_map[agg_fn])

    return _from_df(result_df)


@register("group_by")
def _group_by(data: list[dict], config: dict) -> list[dict]:
    return _aggregate(data, config, "group_by")

@register("aggregate")
def aggregate(data: list[dict], config: dict) -> list[dict]:
    """
    Aggregate data by group columns using a specified function.
    Config: group_columns, agg_column, agg_fn (count|sum|avg|min|max)
    """
    _require(config, "agg_fn", operation="aggregate")
    agg_fn = config["agg_fn"]
    if agg_fn not in ("count", "sum", "avg", "min", "max"):
        raise ValueError(f"[aggregate] Unknown agg_fn '{agg_fn}'. Use: count, sum, avg, min, max")
    return _aggregate(data, config, agg_fn)

@register("count")
def _count(data: list[dict], config: dict) -> list[dict]:
    return _aggregate(data, config, "count")

@register("sum")
def _sum(data: list[dict], config: dict) -> list[dict]:
    return _aggregate(data, config, "sum")

@register("avg")
def _avg(data: list[dict], config: dict) -> list[dict]:
    return _aggregate(data, config, "avg")

@register("min")
def _min(data: list[dict], config: dict) -> list[dict]:
    return _aggregate(data, config, "min")

@register("max")
def _max(data: list[dict], config: dict) -> list[dict]:
    return _aggregate(data, config, "max")


# ─── DATE OPERATIONS ──────────────────────────────────────────────────────────

def _parse_dt(val, fmt: str | None) -> datetime | None:
    if val is None:
        return None
    val_str = str(val).strip()
    if fmt:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            return None
    # Try common formats
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(val_str, f)
        except ValueError:
            continue
    return None


@register("parse_date")
def parse_date(data: list[dict], config: dict) -> list[dict]:
    """
    Parse a string column into ISO date format YYYY-MM-DD.
    Config: column (str), format (optional strptime format string), output_column (optional)
    """
    _require(config, "column", operation="parse_date")
    column = config["column"]
    fmt = config.get("format")
    out_col = config.get("output_column", column)
    for row in data:
        dt = _parse_dt(row.get(column), fmt)
        row[out_col] = dt.strftime("%Y-%m-%d") if dt else None
    return data


@register("extract_year")
def extract_year(data: list[dict], config: dict) -> list[dict]:
    _require(config, "column", operation="extract_year")
    column = config["column"]
    out_col = config.get("output_column", f"{column}_year")
    fmt = config.get("format")
    for row in data:
        dt = _parse_dt(row.get(column), fmt)
        row[out_col] = dt.year if dt else None
    return data


@register("extract_month")
def extract_month(data: list[dict], config: dict) -> list[dict]:
    _require(config, "column", operation="extract_month")
    column = config["column"]
    out_col = config.get("output_column", f"{column}_month")
    fmt = config.get("format")
    for row in data:
        dt = _parse_dt(row.get(column), fmt)
        row[out_col] = dt.month if dt else None
    return data


@register("extract_day")
def extract_day(data: list[dict], config: dict) -> list[dict]:
    _require(config, "column", operation="extract_day")
    column = config["column"]
    out_col = config.get("output_column", f"{column}_day")
    fmt = config.get("format")
    for row in data:
        dt = _parse_dt(row.get(column), fmt)
        row[out_col] = dt.day if dt else None
    return data


@register("date_difference")
def date_difference(data: list[dict], config: dict) -> list[dict]:
    """
    Compute the difference in days between two date columns.
    Config: start_column, end_column, output_column, format (optional)
    Positive result = end is after start.
    """
    _require(config, "start_column", "end_column", operation="date_difference")
    start_col = config["start_column"]
    end_col = config["end_column"]
    out_col = config.get("output_column", "date_diff_days")
    fmt = config.get("format")
    for row in data:
        dt_start = _parse_dt(row.get(start_col), fmt)
        dt_end = _parse_dt(row.get(end_col), fmt)
        if dt_start and dt_end:
            row[out_col] = (dt_end - dt_start).days
        else:
            row[out_col] = None
    return data
