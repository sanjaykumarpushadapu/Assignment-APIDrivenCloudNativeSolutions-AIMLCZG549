"""Automated EDA artifact generation for the Person-2 workflow.

The module generates reusable tables and charts; interpretation remains with
Person 3 as required by the workload split.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .data_quality import BINARY_COLUMNS

EDA_BIVARIATE_COLUMNS = ["bmi", "age", "highbp", "highchol", "physactivity", "genhlth"]
EDA_DISTRIBUTION_COLUMNS = ["bmi", "age", "genhlth", "highbp", "highchol", "physactivity", "cholcheck", "smoker"]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _save_bar(series: pd.Series, path: Path, title: str, xlabel: str) -> None:
    ax = series.plot(kind="bar")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def _save_hist(series: pd.Series, path: Path, title: str) -> None:
    series.dropna().plot(kind="hist", bins=20)
    plt.title(title)
    plt.xlabel(series.name)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def _save_box(frame: pd.DataFrame, path: Path, title: str) -> None:
    frame.boxplot(column="value", by="target")
    plt.suptitle("")
    plt.title(title)
    plt.xlabel("Diabetes_012")
    plt.ylabel(frame.attrs.get("feature", "Value"))
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def generate_eda(frame: pd.DataFrame, output_dir: Path, target_column: str = "Diabetes_012") -> dict[str, Any]:
    """Generate the required EDA tables/charts and return artifact metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = frame.copy()
    frame.columns = [column.strip().lower().replace(" ", "_") for column in frame.columns]
    target_column = target_column.strip().lower().replace(" ", "_")
    distributions_dir = output_dir / "feature_distributions"
    bivariate_dir = output_dir / "bivariate"
    distributions_dir.mkdir(exist_ok=True)
    bivariate_dir.mkdir(exist_ok=True)

    summary = frame.describe(include="all").transpose()
    summary.to_csv(output_dir / "summary_statistics.csv")

    missing = frame.isna().sum().rename("missing_count").to_frame()
    missing["missing_percentage"] = missing["missing_count"] / max(len(frame), 1) * 100
    missing.to_csv(output_dir / "missing_value_summary.csv")

    target_counts = frame[target_column].value_counts(dropna=False).sort_index()
    target_distribution = target_counts.rename("count").to_frame()
    target_distribution["percentage"] = target_distribution["count"] / max(len(frame), 1) * 100
    target_distribution.to_csv(output_dir / "target_distribution.csv")
    _save_bar(target_counts, output_dir / "target_distribution.png", "Diabetes Risk Target Distribution", target_column)

    generated_distributions: list[str] = []
    for column in EDA_DISTRIBUTION_COLUMNS:
        if column not in frame.columns:
            continue
        path = distributions_dir / f"{column.lower()}_distribution.png"
        if column in BINARY_COLUMNS or frame[column].nunique(dropna=True) <= 10:
            _save_bar(frame[column].value_counts().sort_index(), path, f"{column} Distribution", column)
        else:
            _save_hist(frame[column], path, f"{column} Distribution")
        generated_distributions.append(str(path))

    numeric = frame.select_dtypes(include="number")
    correlation = numeric.corr(numeric_only=True)
    correlation.to_csv(output_dir / "correlation_matrix.csv")

    generated_bivariate: list[str] = []
    for feature in EDA_BIVARIATE_COLUMNS:
        if feature not in frame.columns or target_column not in frame.columns:
            continue
        grouped = frame.groupby(target_column)[feature].agg(["count", "mean", "median"])
        grouped.to_csv(bivariate_dir / f"{feature.lower()}_vs_target.csv")
        if pd.api.types.is_numeric_dtype(frame[feature]):
            temp = frame[[target_column, feature]].rename(columns={feature: "value", target_column: "target"}).dropna()
            temp.attrs["feature"] = feature
            path = bivariate_dir / f"{feature.lower()}_vs_target.png"
            _save_box(temp, path, f"{feature} vs {target_column}")
            generated_bivariate.append(str(path))

    # Meaningful bins are generated without replacing the original columns.
    bin_frame = pd.DataFrame(index=frame.index)
    if "age" in frame.columns:
        bin_frame["AgeGroup"] = pd.cut(
            frame["age"], bins=[0, 4, 7, 10, 13], labels=["1-4", "5-7", "8-10", "11-13"], include_lowest=True
        )
    if "bmi" in frame.columns:
        bin_frame["BMIGroup"] = pd.cut(
            frame["bmi"], bins=[0, 18.5, 25, 30, float("inf")], labels=["Underweight", "Normal", "Overweight", "Obese"], include_lowest=True
        )
    bin_frame.to_csv(output_dir / "binned_features.csv", index=False)

    metadata = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "target_column": target_column,
        "summary_statistics": str(output_dir / "summary_statistics.csv"),
        "missing_value_summary": str(output_dir / "missing_value_summary.csv"),
        "target_distribution": str(output_dir / "target_distribution.csv"),
        "target_distribution_chart": str(output_dir / "target_distribution.png"),
        "feature_distribution_charts": generated_distributions,
        "correlation_matrix": str(output_dir / "correlation_matrix.csv"),
        "bivariate_outputs": generated_bivariate,
        "binned_features": str(output_dir / "binned_features.csv"),
    }
    (output_dir / "eda_metadata.json").write_text(json.dumps(_json_safe(metadata), indent=2), encoding="utf-8")
    return metadata
