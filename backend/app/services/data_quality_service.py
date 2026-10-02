"""
DataForge Data Quality Service
================================
Validates datasets against a structured set of quality rules.

Configuration schema (all fields optional):
{
  "required_columns": ["id", "email"],      # or "id,email"
  "email_column": "email",                  # email format validation
  "unique_columns": ["id", "email"],        # or "id,email"
  "type_validation": {
      "age": "int",
      "score": "float",
      "active": "bool"
  },
  "range_validation": {
      "age":   {"min": 0, "max": 120},
      "score": {"min": 0.0, "max": 100.0}
  },
  "allowed_values": {
      "status": ["active", "inactive", "pending"],
      "tier":   ["free", "pro", "enterprise"]
  },
  "pattern_validation": {
      "email": "^[^@]+@[^@]+\\.[^@]+$",
      "phone": "^\\+?[0-9\\s\\-]{7,15}$"
  },
  "schema": {
      "id":     {"type": "int", "required": true},
      "email":  {"type": "str", "required": true},
      "age":    {"type": "int", "min": 18, "max": 100}
  }
}

Returns:
{
  "rows_processed": int,
  "score": int (0-100),
  "quality_status": "excellent|good|warning|critical",
  "passed": int,
  "failed": int,
  "checks": { "<check_name>": { "passed": bool, "detail": str } },
  "violations": [ { "check": str, "row_index": int, "column": str, "value": any, "reason": str } ],
  "summary": str
}
"""

from __future__ import annotations

import re
from typing import Any


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _is_empty(val) -> bool:
    return val is None or str(val).strip() == ""


def _coerce_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [c.strip() for c in value.split(",") if c.strip()]
    return []


class _CheckResult:
    def __init__(self):
        self.checks: dict[str, dict] = {}
        self.violations: list[dict] = []

    def add_check(self, name: str, passed: bool, detail: str = ""):
        self.checks[name] = {"passed": passed, "detail": detail}

    def add_violation(self, check: str, row_index: int, column: str, value: Any, reason: str):
        self.violations.append({
            "check": check,
            "row_index": row_index,
            "column": column,
            "value": value,
            "reason": reason,
        })


# ─── DataQualityService ───────────────────────────────────────────────────────

class DataQualityService:
    """
    Extensible data quality validation service.
    Supports: required columns, nulls, duplicates, uniqueness,
              type validation, range validation, allowed values,
              regex/pattern validation, and schema validation.
    """

    # ── Public entry point ────────────────────────────────────────────────────

    @staticmethod
    def compute_quality(
        data: list[dict],
        required_columns: list[str] | None = None,
        email_column: str | None = None,
        type_validation: dict | None = None,
        unique_columns: list[str] | None = None,
        range_validation: dict | None = None,
        allowed_values: dict | None = None,
        pattern_validation: dict | None = None,
        schema: dict | None = None,
    ) -> dict:
        """
        Run all configured quality checks and return a structured result dict.
        """
        if not data:
            return DataQualityService._empty_result()

        cr = _CheckResult()
        rows_processed = len(data)
        column_keys = set(data[0].keys()) if data else set()

        # ── 1. Required columns ────────────────────────────────────────────────
        if required_columns:
            required_columns = _coerce_list(required_columns)
            missing_cols = [c for c in required_columns if c not in column_keys]
            cr.add_check(
                "required_columns",
                passed=len(missing_cols) == 0,
                detail=f"Missing: {missing_cols}" if missing_cols else "All required columns present",
            )
            for col in missing_cols:
                cr.add_violation("required_columns", -1, col, None, f"Column '{col}' is missing from dataset")

        # ── 2. Null / completeness check ──────────────────────────────────────
        total_cells = rows_processed * len(column_keys) if column_keys else 0
        missing_count = 0
        for i, row in enumerate(data):
            for k, v in row.items():
                if _is_empty(v):
                    missing_count += 1
                    cr.add_violation("null_check", i, k, v, f"Null or empty value in column '{k}'")

        missing_pct = round(missing_count / total_cells * 100, 2) if total_cells > 0 else 0.0
        cr.add_check(
            "null_check",
            passed=missing_count == 0,
            detail=f"{missing_count} missing values ({missing_pct}%)",
        )

        # ── 3. Duplicate rows ─────────────────────────────────────────────────
        seen_rows: set = set()
        dup_count = 0
        for i, row in enumerate(data):
            key = tuple(sorted((k, str(v)) for k, v in row.items()))
            if key in seen_rows:
                dup_count += 1
                cr.add_violation("duplicate_rows", i, "*", None, "Duplicate row")
            else:
                seen_rows.add(key)
        dup_pct = round(dup_count / rows_processed * 100, 2)
        cr.add_check(
            "duplicate_rows",
            passed=dup_count == 0,
            detail=f"{dup_count} duplicate rows ({dup_pct}%)",
        )

        # ── 4. Uniqueness check ────────────────────────────────────────────────
        if unique_columns:
            unique_columns = _coerce_list(unique_columns)
            for col in unique_columns:
                col_seen: set = set()
                col_viol = 0
                for i, row in enumerate(data):
                    v = row.get(col)
                    if v is not None:
                        if v in col_seen:
                            col_viol += 1
                            cr.add_violation("uniqueness", i, col, v,
                                             f"Duplicate value '{v}' in column '{col}'")
                        else:
                            col_seen.add(v)
                cr.add_check(
                    f"unique_{col}",
                    passed=col_viol == 0,
                    detail=f"{col_viol} duplicate values in '{col}'",
                )

        # ── 5. Email column validation ─────────────────────────────────────────
        if email_column and email_column in column_keys:
            email_regex = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
            invalid_emails = 0
            for i, row in enumerate(data):
                v = row.get(email_column)
                if not _is_empty(v) and not email_regex.match(str(v).strip()):
                    invalid_emails += 1
                    cr.add_violation("email_format", i, email_column, v,
                                     f"Invalid email format: '{v}'")
            cr.add_check(
                "email_format",
                passed=invalid_emails == 0,
                detail=f"{invalid_emails} invalid email values in '{email_column}'",
            )

        # ── 6. Type validation ─────────────────────────────────────────────────
        if type_validation:
            for col, expected_type in type_validation.items():
                mismatches = 0
                for i, row in enumerate(data):
                    v = row.get(col)
                    if _is_empty(v):
                        continue
                    ok = DataQualityService._check_type(v, expected_type)
                    if not ok:
                        mismatches += 1
                        cr.add_violation("type_validation", i, col, v,
                                         f"Cannot cast '{v}' to {expected_type}")
                cr.add_check(
                    f"type_{col}",
                    passed=mismatches == 0,
                    detail=f"{mismatches} type mismatches in '{col}' (expected {expected_type})",
                )

        # ── 7. Range validation ────────────────────────────────────────────────
        if range_validation:
            for col, bounds in range_validation.items():
                col_min = bounds.get("min")
                col_max = bounds.get("max")
                range_viols = 0
                for i, row in enumerate(data):
                    v = row.get(col)
                    if _is_empty(v):
                        continue
                    try:
                        fv = float(v)
                        if col_min is not None and fv < float(col_min):
                            range_viols += 1
                            cr.add_violation("range_validation", i, col, v,
                                             f"Value {fv} < min {col_min}")
                        elif col_max is not None and fv > float(col_max):
                            range_viols += 1
                            cr.add_violation("range_validation", i, col, v,
                                             f"Value {fv} > max {col_max}")
                    except (TypeError, ValueError):
                        range_viols += 1
                        cr.add_violation("range_validation", i, col, v,
                                         f"Cannot compare non-numeric value '{v}'")
                cr.add_check(
                    f"range_{col}",
                    passed=range_viols == 0,
                    detail=f"{range_viols} range violations in '{col}' [{col_min}, {col_max}]",
                )

        # ── 8. Allowed values ──────────────────────────────────────────────────
        if allowed_values:
            for col, allowed in allowed_values.items():
                allowed_set = {str(v) for v in allowed}
                av_viols = 0
                for i, row in enumerate(data):
                    v = row.get(col)
                    if _is_empty(v):
                        continue
                    if str(v) not in allowed_set:
                        av_viols += 1
                        cr.add_violation("allowed_values", i, col, v,
                                         f"Value '{v}' not in allowed set {sorted(allowed_set)}")
                cr.add_check(
                    f"allowed_{col}",
                    passed=av_viols == 0,
                    detail=f"{av_viols} disallowed values in '{col}'",
                )

        # ── 9. Pattern / regex validation ─────────────────────────────────────
        if pattern_validation:
            for col, pattern in pattern_validation.items():
                try:
                    compiled = re.compile(pattern)
                except re.error as e:
                    cr.add_check(f"pattern_{col}", passed=False,
                                 detail=f"Invalid regex pattern: {e}")
                    continue
                pv_viols = 0
                for i, row in enumerate(data):
                    v = row.get(col)
                    if _is_empty(v):
                        continue
                    if not compiled.match(str(v).strip()):
                        pv_viols += 1
                        cr.add_violation("pattern_validation", i, col, v,
                                         f"Value '{v}' does not match pattern '{pattern}'")
                cr.add_check(
                    f"pattern_{col}",
                    passed=pv_viols == 0,
                    detail=f"{pv_viols} pattern mismatches in '{col}'",
                )

        # ── 10. Schema validation ──────────────────────────────────────────────
        if schema:
            for col, rules in schema.items():
                col_required = rules.get("required", False)
                col_type = rules.get("type")
                col_min = rules.get("min")
                col_max = rules.get("max")
                col_allowed = rules.get("allowed_values")

                if col_required and col not in column_keys:
                    cr.add_check(f"schema_{col}", passed=False,
                                 detail=f"Required column '{col}' missing from schema")
                    cr.add_violation("schema", -1, col, None,
                                     f"Schema requires column '{col}' to be present")
                    continue

                schema_viols = 0
                for i, row in enumerate(data):
                    v = row.get(col)
                    if col_required and _is_empty(v):
                        schema_viols += 1
                        cr.add_violation("schema", i, col, v, f"Required column '{col}' is null")
                        continue
                    if _is_empty(v):
                        continue
                    if col_type and not DataQualityService._check_type(v, col_type):
                        schema_viols += 1
                        cr.add_violation("schema", i, col, v,
                                         f"Expected type '{col_type}' for '{col}'")
                    if col_min is not None or col_max is not None:
                        try:
                            fv = float(v)
                            if col_min is not None and fv < float(col_min):
                                schema_viols += 1
                                cr.add_violation("schema", i, col, v,
                                                 f"{col}: {fv} < min {col_min}")
                            if col_max is not None and fv > float(col_max):
                                schema_viols += 1
                                cr.add_violation("schema", i, col, v,
                                                 f"{col}: {fv} > max {col_max}")
                        except (TypeError, ValueError):
                            pass
                    if col_allowed:
                        allowed_set = {str(a) for a in col_allowed}
                        if str(v) not in allowed_set:
                            schema_viols += 1
                            cr.add_violation("schema", i, col, v,
                                             f"'{v}' not in allowed values for '{col}'")

                cr.add_check(
                    f"schema_{col}",
                    passed=schema_viols == 0,
                    detail=f"{schema_viols} schema violations in '{col}'",
                )

        # ── Compute score ──────────────────────────────────────────────────────
        passed = sum(1 for c in cr.checks.values() if c["passed"])
        failed = sum(1 for c in cr.checks.values() if not c["passed"])
        total_checks = passed + failed

        if total_checks == 0:
            score = 100
        else:
            score = round(passed / total_checks * 100)

        # Also penalise for violation density
        if len(cr.violations) > 0 and rows_processed > 0:
            violation_density = min(len(cr.violations) / (rows_processed * max(1, len(column_keys))), 1.0)
            score = max(0, score - round(violation_density * 30))

        if score >= 90:
            status = "excellent"
        elif score >= 75:
            status = "good"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"

        summary = (
            f"Processed {rows_processed} rows. "
            f"{passed}/{total_checks} checks passed. "
            f"{len(cr.violations)} violations. "
            f"Score: {score}/100 ({status})."
        )

        return {
            "rows_processed": rows_processed,
            "score": score,
            "quality_score": score,          # legacy alias
            "quality_status": status,
            "passed": passed,
            "failed": failed,
            "checks": cr.checks,
            "violations": cr.violations[:100],  # cap to avoid huge payloads
            "summary": summary,
            # Legacy scalar fields for backward compatibility
            "missing_value_count": missing_count,
            "missing_value_percentage": missing_pct,
            "duplicate_row_count": dup_count,
            "duplicate_percentage": dup_pct,
            "missing_required_columns": (
                [c for c in (_coerce_list(required_columns) if required_columns else [])
                 if c not in column_keys]
            ),
        }

    @staticmethod
    def _check_type(val, expected_type: str) -> bool:
        """Return True if val can be interpreted as expected_type."""
        try:
            if expected_type == "int":
                int(float(str(val)))
                return True
            elif expected_type == "float":
                float(str(val))
                return True
            elif expected_type == "bool":
                return str(val).lower() in ("true", "false", "1", "0", "yes", "no")
            elif expected_type == "str":
                return True  # anything is a string
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _empty_result() -> dict:
        return {
            "rows_processed": 0,
            "score": 100,
            "quality_score": 100,
            "quality_status": "excellent",
            "passed": 0,
            "failed": 0,
            "checks": {},
            "violations": [],
            "summary": "No data to evaluate.",
            "missing_value_count": 0,
            "missing_value_percentage": 0.0,
            "duplicate_row_count": 0,
            "duplicate_percentage": 0.0,
            "missing_required_columns": [],
        }

    @staticmethod
    def format_quality_result(res: dict) -> str:
        """Format a quality result dict into a human-readable log message expected by frontend parser."""
        return (
            f"Data Quality: {res.get('rows_processed', '?')} rows, "
            f"{res.get('missing_value_count', '?')} missing values, "
            f"{res.get('duplicate_row_count', '?')} duplicate, "
            f"score {res.get('quality_score', res.get('score', '?'))}/100 "
            f"({res.get('quality_status', '?')})"
        )
