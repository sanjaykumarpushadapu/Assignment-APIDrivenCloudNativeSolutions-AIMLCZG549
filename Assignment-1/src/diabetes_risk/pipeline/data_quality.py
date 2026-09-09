"""Data-quality validation for the diabetes health indicators dataset.

This module is intentionally platform neutral. It accepts a pandas DataFrame and
returns JSON-serializable quality results; storage and orchestration are handled
outside this module.
"""
from __future__ import annotations

from typing import Any
import math

import pandas as pd

from .ingestion import EXPECTED_COLUMNS, TARGET_COLUMN

EXPECTED_TARGET_VALUES = {0.0, 1.0, 2.0}
BINARY_COLUMNS = {
    "HighBP", "HighChol", "CholCheck", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "DiffWalk", "Sex",
}
EXPECTED_BINARY_VALUES = {0.0, 1.0}
EXPECTED_RANGES = {
    "BMI": (1.0, 100.0),
    "MentHlth": (0.0, 30.0),
    "PhysHlth": (0.0, 30.0),
    "GenHlth": (1.0, 5.0),
    "Age": (1.0, 13.0),
    "Education": (1.0, 6.0),
    "Income": (1.0, 8.0),
}


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy scalar values to standard JSON types."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if value is pd.NA or value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


class DataQualityError(ValueError):
    """Raised when a critical data-quality rule fails."""


def _missing_report(frame: pd.DataFrame) -> pd.DataFrame:
    counts = frame.isna().sum()
    return pd.DataFrame(
        {
            "column": counts.index,
            "missing_count": counts.values,
            "missing_percentage": (counts.values / max(len(frame), 1)) * 100,
        }
    )


def _unique_values(frame: pd.DataFrame, column: str) -> list[Any]:
    if column not in frame.columns:
        return []
    values = frame[column].dropna().unique().tolist()
    return sorted(values, key=lambda value: str(value))


def validate_schema(frame: pd.DataFrame, target_column: str = TARGET_COLUMN, *, strict: bool = False) -> dict[str, Any]:
    """Validate expected columns and target presence."""
    missing_columns = [column for column in EXPECTED_COLUMNS if column not in frame.columns]
    unexpected_columns = [column for column in frame.columns if column not in EXPECTED_COLUMNS]
    target_present = target_column in frame.columns
    if not target_present or (strict and missing_columns):
        raise DataQualityError(
            f"Schema validation failed. missing_columns={missing_columns}, target_present={target_present}"
        )
    return {
        "expected_column_count": len(EXPECTED_COLUMNS),
        "actual_column_count": len(frame.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "target_column": target_column,
        "target_present": target_present,
        "column_order_matches": list(frame.columns) == EXPECTED_COLUMNS,
    }


def validate_target(frame: pd.DataFrame, target_column: str = TARGET_COLUMN) -> dict[str, Any]:
    """Check target values against the approved 0/1/2 classes."""
    if target_column not in frame.columns:
        raise DataQualityError(f"Target column '{target_column}' is missing")
    values = set(frame[target_column].dropna().unique().tolist())
    invalid = sorted(values - EXPECTED_TARGET_VALUES)
    return {
        "valid_values": sorted(EXPECTED_TARGET_VALUES),
        "observed_values": sorted(values),
        "invalid_values": invalid,
        "invalid_count": int(frame[target_column].isin(invalid).sum()) if invalid else 0,
        "missing_count": int(frame[target_column].isna().sum()),
        "valid": not invalid and frame[target_column].notna().all(),
    }


def validate_numeric_ranges(frame: pd.DataFrame) -> dict[str, Any]:
    """Check known dataset fields against their documented value ranges."""
    results: dict[str, Any] = {}
    for column, (minimum, maximum) in EXPECTED_RANGES.items():
        if column not in frame.columns:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        invalid_mask = numeric.notna() & ((numeric < minimum) | (numeric > maximum))
        results[column] = {
            "expected_min": minimum,
            "expected_max": maximum,
            "observed_min": float(numeric.min()) if numeric.notna().any() else None,
            "observed_max": float(numeric.max()) if numeric.notna().any() else None,
            "invalid_count": int(invalid_mask.sum()),
            "valid": not bool(invalid_mask.any()),
        }
    return results


def validate_binary_values(frame: pd.DataFrame) -> dict[str, Any]:
    """Check binary indicator columns for values outside 0/1."""
    results: dict[str, Any] = {}
    for column in sorted(BINARY_COLUMNS):
        if column not in frame.columns:
            continue
        observed = set(frame[column].dropna().unique().tolist())
        invalid = sorted(observed - EXPECTED_BINARY_VALUES)
        results[column] = {
            "expected_values": [0.0, 1.0],
            "observed_values": sorted(observed),
            "invalid_values": invalid,
            "invalid_count": int(frame[column].isin(invalid).sum()) if invalid else 0,
            "valid": not invalid,
        }
    return results


def run_data_quality(frame: pd.DataFrame, target_column: str = TARGET_COLUMN, *, strict_schema: bool = False) -> dict[str, Any]:
    """Run all Person-2 quality checks and return a JSON-serializable report."""
    schema = validate_schema(frame, target_column, strict=strict_schema)
    missing = _missing_report(frame)
    duplicate_count = int(frame.duplicated(keep="first").sum())
    target = validate_target(frame, target_column)
    numeric_ranges = validate_numeric_ranges(frame)
    binary_values = validate_binary_values(frame)

    invalid_numeric_total = sum(item["invalid_count"] for item in numeric_ranges.values())
    invalid_binary_total = sum(item["invalid_count"] for item in binary_values.values())

    report = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "schema": schema,
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "summary_statistics": frame.describe(include="all").transpose().fillna(pd.NA).to_dict(orient="index"),
        "missing_values": missing.to_dict(orient="records"),
        "missing_value_total": int(frame.isna().sum().sum()),
        "duplicate_count": duplicate_count,
        "duplicate_percentage": float(duplicate_count / max(len(frame), 1) * 100),
        "target_validation": target,
        "numeric_range_validation": numeric_ranges,
        "binary_value_validation": binary_values,
        "invalid_numeric_value_count": int(invalid_numeric_total),
        "invalid_binary_value_count": int(invalid_binary_total),
        "quality_status": "PASS" if target["valid"] and invalid_numeric_total == 0 and invalid_binary_total == 0 and duplicate_count == 0 else ("PASS_WITH_WARNINGS" if target["valid"] and invalid_numeric_total == 0 and invalid_binary_total == 0 else "WARN"),
    }
    return _json_safe(report)
