"""Platform-neutral preprocessing for the diabetes health indicators dataset."""
from __future__ import annotations

from typing import Any

import pandas as pd



def normalize_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, and snake_case every column name."""
    result = frame.copy()
    result.columns = [column.strip().lower().replace(" ", "_") for column in result.columns]
    return result


def summary_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Descriptive statistics for every column."""
    return frame.describe(include="all").transpose()


def dtype_report(frame: pd.DataFrame) -> dict[str, str]:
    """Return pandas data types by column."""
    return {column: str(dtype) for column, dtype in frame.dtypes.items()}


def missing_value_report(frame: pd.DataFrame) -> dict[str, int]:
    """Return missing counts for all columns, including zero counts."""
    return {column: int(count) for column, count in frame.isna().sum().items()}


def impute_missing(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Median-impute numeric fields and mode-impute categorical fields."""
    result = frame.copy()
    numeric_imputations: dict[str, float] = {}
    categorical_imputations: dict[str, Any] = {}
    for column in result.select_dtypes(include="number").columns:
        if result[column].isna().any():
            median = float(result[column].median())
            result[column] = result[column].fillna(median)
            numeric_imputations[column] = median
    for column in result.select_dtypes(exclude="number").columns:
        if result[column].isna().any():
            mode = result[column].mode(dropna=True)
            value = mode.iloc[0] if not mode.empty else "unknown"
            result[column] = result[column].fillna(value)
            categorical_imputations[column] = value
    return result, {
        "numeric_medians": numeric_imputations,
        "categorical_values": categorical_imputations,
    }


def remove_exact_duplicates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate records while preserving the first occurrence."""
    duplicate_count = int(frame.duplicated(keep="first").sum())
    return frame.drop_duplicates(keep="first").reset_index(drop=True), duplicate_count


def encode_features(frame: pd.DataFrame, target_column: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Encode non-numeric categories while leaving existing binary indicators unchanged."""
    result = frame.copy()
    target = target_column
    categorical = [c for c in result.select_dtypes(exclude="number").columns if c != target]
    if not categorical:
        return result, {"encoded_columns": [], "method": "No non-numeric columns required encoding"}
    encoded = pd.get_dummies(result, columns=categorical, drop_first=False, dtype=float)
    return encoded, {"encoded_columns": categorical, "method": "pandas one-hot encoding"}


def standardize_numeric(
    frame: pd.DataFrame,
    *,
    exclude: list[str] | None = None,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Standardize selected continuous/count fields using z-score scaling.

    Binary, ordinal, and target fields are deliberately not scaled by default.
    """
    result = frame.copy()
    excluded = set(exclude or [])
    selected = columns or ["bmi", "menthlth", "physhlth"]
    scaled: list[str] = []
    parameters: dict[str, dict[str, float]] = {}
    for column in selected:
        if column not in result.columns or column in excluded:
            continue
        if not pd.api.types.is_numeric_dtype(result[column]):
            continue
        mean = float(result[column].mean())
        std = float(result[column].std(ddof=0))
        parameters[column] = {"mean": mean, "std": std}
        result[column] = 0.0 if std == 0 else (result[column] - mean) / std
        scaled.append(column)
    return result, {"method": "z-score standardization", "columns": scaled, "parameters": parameters}


def normalize_numeric(frame: pd.DataFrame, exclude: list[str] | None = None) -> pd.DataFrame:
    """Backward-compatible helper: min-max normalize numeric columns."""
    result = frame.copy()
    excluded = set(exclude or [])
    numeric_columns = [c for c in result.select_dtypes(include="number").columns if c not in excluded]
    for column in numeric_columns:
        minimum = result[column].min()
        maximum = result[column].max()
        value_range = maximum - minimum
        result[column] = 0.0 if value_range == 0 else (result[column] - minimum) / value_range
    return result


def preprocess(
    frame: pd.DataFrame,
    target_column: str | None = None,
    *,
    drop_duplicates: bool = True,
    standardize: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute the complete preprocessing contract.

    The output retains interpretable binary/ordinal features and the target.
    Continuous/count features are standardized by default. Exact duplicates are
    removed after schema normalization and before transformations.
    """
    named = normalize_column_names(frame)
    target = target_column.strip().lower().replace(" ", "_") if target_column else None
    original_rows = len(named)

    if target and target not in named.columns:
        raise ValueError(f"Target column '{target}' not found after column normalization")

    duplicate_count = int(named.duplicated(keep="first").sum())
    deduplicated = named.drop_duplicates(keep="first").reset_index(drop=True) if drop_duplicates else named

    imputed, imputation_report = impute_missing(deduplicated)
    encoded, encoding_report = encode_features(imputed, target)

    # For the approved dataset, these fields are continuous/count-like and are
    # appropriate for standardization. Existing binary and ordinal indicators
    # remain interpretable and are not unnecessarily transformed.
    standardized, standardization_report = standardize_numeric(
        encoded,
        exclude=[target] if target else [],
        columns=[c for c in ["BMI", "MentHlth", "PhysHlth"] if c in encoded.columns],
    ) if standardize else (encoded, {"method": "disabled", "columns": [], "parameters": {}})

    report: dict[str, Any] = {
        "input_rows": int(original_rows),
        "output_rows": int(len(standardized)),
        "duplicates_detected": duplicate_count,
        "duplicates_removed": duplicate_count if drop_duplicates else 0,
        "missing_values_before": missing_value_report(named),
        "missing_values_after": missing_value_report(standardized),
        "dtypes_before": dtype_report(named),
        "dtypes_after": dtype_report(standardized),
        "imputation": imputation_report,
        "encoding": encoding_report,
        "standardization": standardization_report,
        "target_column": target,
        "feature_columns": [c for c in standardized.columns if c != target],
        "target_values": sorted(standardized[target].dropna().unique().tolist()) if target else [],
        "transformations": [
            "column-name normalization",
            "exact duplicate removal" if drop_duplicates else "duplicate removal disabled",
            "numeric median imputation where required",
            "categorical mode imputation where required",
            "categorical one-hot encoding where required",
            "z-score standardization of continuous/count features" if standardize else "standardization disabled",
        ],
    }
    return standardized, report
