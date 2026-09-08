from __future__ import annotations

import pandas as pd


def normalize_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, and snake_case every column name."""
    result = frame.copy()
    result.columns = [column.strip().lower().replace(" ", "_") for column in result.columns]
    return result


def summary_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Descriptive statistics for every column (rubric 1.3: 'summary statistics')."""
    return frame.describe(include="all").transpose()


def dtype_report(frame: pd.DataFrame) -> dict[str, str]:
    """Each column's pandas dtype as a string (rubric 1.3: 'displaying data types')."""
    return {column: str(dtype) for column, dtype in frame.dtypes.items()}


def missing_value_report(frame: pd.DataFrame) -> dict[str, int]:
    """Count of missing values per column, omitting columns with none
    (rubric 1.3: 'checking for missing values')."""
    counts = frame.isna().sum()
    return {column: int(count) for column, count in counts.items() if count > 0}


def impute_missing(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill missing numeric values with the column median, categoricals with 'unknown'
    (rubric 1.3: 'imputing missing data for numeric columns')."""
    result = frame.copy()
    numeric_columns = result.select_dtypes(include="number").columns
    for column in numeric_columns:
        result[column] = result[column].fillna(result[column].median())
    categorical_columns = result.select_dtypes(exclude="number").columns
    for column in categorical_columns:
        result[column] = result[column].fillna("unknown")
    return result


def normalize_numeric(frame: pd.DataFrame, exclude: list[str] | None = None) -> pd.DataFrame:
    """Min-max scale numeric columns to the [0, 1] range (rubric 1.3: 'normalizing data').

    ``exclude`` should list columns that must stay in their original scale,
    such as the prediction target or identifier columns.
    """
    result = frame.copy()
    excluded = set(exclude or [])
    numeric_columns = [c for c in result.select_dtypes(include="number").columns if c not in excluded]
    for column in numeric_columns:
        min_value = result[column].min()
        max_value = result[column].max()
        value_range = max_value - min_value
        result[column] = 0.0 if value_range == 0 else (result[column] - min_value) / value_range
    return result


def preprocess(
    frame: pd.DataFrame, target_column: str | None = None
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Run the full 1.3 preprocessing contract.

    Order: normalize column names -> capture dtypes / missing counts / summary
    statistics on the raw data -> impute missing values -> min-max normalize
    numeric columns (excluding ``target_column`` if given, so the label keeps
    its original scale).

    Returns the cleaned frame plus a JSON-serializable report describing what
    happened, for logging and for the API/dashboard to display later.
    """
    named = normalize_column_names(frame)
    target = target_column.strip().lower().replace(" ", "_") if target_column else None

    report: dict[str, object] = {
        "rows": len(named),
        "dtypes": dtype_report(named),
        "missing_values_before": missing_value_report(named),
        "summary_statistics": summary_statistics(named).to_dict(orient="index"),
    }

    imputed = impute_missing(named)
    normalized = normalize_numeric(imputed, exclude=[target] if target else None)

    report["missing_values_after"] = missing_value_report(normalized)
    report["columns"] = list(normalized.columns)

    return normalized, report
