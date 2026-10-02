"""
DataForge Data Profiling Service
=================================
Computes real statistical profiles of datasets.
No fake metrics — all figures come from the actual data.
"""

from __future__ import annotations
import statistics
from typing import Any


def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _infer_type(values: list) -> str:
    """
    Infer the most likely data type from a sample of non-null values.
    Returns one of: integer, float, boolean, string.
    """
    if not values:
        return "string"

    # Try boolean first
    bool_vals = {"true", "false", "1", "0", "yes", "no"}
    if all(str(v).strip().lower() in bool_vals for v in values):
        return "boolean"

    # Try integer
    try:
        all(int(str(v).strip()) == float(str(v).strip()) for v in values)
        all(float(str(v).strip()) for v in values)
        int_ok = all(str(v).strip() == str(int(float(str(v).strip()))) or "." not in str(v) for v in values)
        float_ok = True
        for v in values:
            float(str(v).strip())
        if int_ok:
            return "integer"
        if float_ok:
            return "float"
    except (ValueError, TypeError):
        pass

    try:
        for v in values:
            float(str(v).strip())
        return "float"
    except (ValueError, TypeError):
        pass

    return "string"


class DataProfilingService:
    """
    Compute a structured profile of a list-of-dict dataset.

    Returns:
        {
            "row_count": int,
            "column_count": int,
            "duplicate_row_count": int,
            "duplicate_percentage": float,
            "columns": {
                "<col_name>": {
                    "inferred_type": str,
                    "missing_count": int,
                    "missing_percentage": float,
                    "unique_count": int,
                    "uniqueness_percentage": float,
                    "min": ...,          # numeric/string
                    "max": ...,
                    "mean": float|None,  # numeric only
                    "median": float|None,
                    "sample_values": list  # up to 5 values
                },
                ...
            }
        }
    """

    @staticmethod
    def profile(data: list[dict]) -> dict:
        row_count = len(data)
        if row_count == 0:
            return {
                "row_count": 0,
                "column_count": 0,
                "duplicate_row_count": 0,
                "duplicate_percentage": 0.0,
                "columns": {},
            }

        # Gather all column names (union across all rows)
        all_columns: list[str] = []
        seen_cols: set[str] = set()
        for row in data:
            for k in row.keys():
                if k not in seen_cols:
                    all_columns.append(k)
                    seen_cols.add(k)

        column_count = len(all_columns)

        # Duplicate row detection
        seen_rows: set = set()
        duplicate_row_count = 0
        for row in data:
            key = tuple(sorted((k, str(v)) for k, v in row.items()))
            if key in seen_rows:
                duplicate_row_count += 1
            else:
                seen_rows.add(key)
        duplicate_percentage = round(duplicate_row_count / row_count * 100, 2)

        # Per-column statistics
        columns: dict[str, dict[str, Any]] = {}
        for col in all_columns:
            col_values = [row.get(col) for row in data]
            missing_count = sum(
                1 for v in col_values
                if v is None or str(v).strip() == ""
            )
            present_values = [v for v in col_values if v is not None and str(v).strip() != ""]
            unique_values = list({str(v) for v in present_values})
            unique_count = len(unique_values)
            missing_percentage = round(missing_count / row_count * 100, 2)
            uniqueness_percentage = round(unique_count / row_count * 100, 2)

            inferred_type = _infer_type(present_values[:200])  # sample for large datasets

            # Numeric statistics
            numeric_values: list[float] = []
            if inferred_type in ("integer", "float"):
                numeric_values = [
                    fv for fv in (_safe_float(v) for v in present_values)
                    if fv is not None
                ]

            col_min: Any = None
            col_max: Any = None
            mean: float | None = None
            median: float | None = None

            if numeric_values:
                col_min = min(numeric_values)
                col_max = max(numeric_values)
                mean = round(sum(numeric_values) / len(numeric_values), 4)
                try:
                    median = round(statistics.median(numeric_values), 4)
                except statistics.StatisticsError:
                    median = None
            elif present_values:
                try:
                    str_vals = sorted(str(v) for v in present_values)
                    col_min = str_vals[0]
                    col_max = str_vals[-1]
                except Exception:
                    pass

            sample_values = [v for v in col_values if v is not None][:5]

            columns[col] = {
                "inferred_type": inferred_type,
                "missing_count": missing_count,
                "missing_percentage": missing_percentage,
                "unique_count": unique_count,
                "uniqueness_percentage": uniqueness_percentage,
                "min": col_min,
                "max": col_max,
                "mean": mean,
                "median": median,
                "sample_values": sample_values,
            }

        return {
            "row_count": row_count,
            "column_count": column_count,
            "duplicate_row_count": duplicate_row_count,
            "duplicate_percentage": duplicate_percentage,
            "columns": columns,
        }
