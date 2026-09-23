"""Service layer for the dataset-quality and model-results endpoints.

These are the pipeline's own generated artifacts (not Composer/Airflow
state), but per activity 3.1 ("Use Built-in APIs") they are still
retrieved through a GCP built-in API -- the Cloud Storage API -- reading
the same bucket objects the DAG itself writes
(`dags/diabetes_risk_pipeline.py` uses `DIABETES_GCS_BUCKET` /
`GCS_OUTPUT_PREFIX = "data/outputs"`), rather than the local filesystem.

The functions in this module read the pipeline's JSON and CSV artifacts
from Cloud Storage. Install the optional `gcp` dependencies to use them.
"""

from __future__ import annotations

import csv
import io
import json
import os


def _bucket_name() -> str:
    """Read the target bucket name.

    Reuses `DIABETES_GCS_BUCKET`, the same environment variable
    `dags/diabetes_risk_pipeline.py` uses, so both the DAG and this API
    point at one bucket.
    """
    return os.environ.get("DIABETES_GCS_BUCKET", "")


def _read_gcs_text(bucket_name: str, object_name: str) -> str:
    """Download one GCS object's contents as text.

    Uses `google-cloud-storage` (Cloud Storage JSON API under the hood),
    the same client library the DAG itself uses. Requires
    `roles/storage.objectViewer` and picks up credentials the same way
    as `gcp_service.py`: `GOOGLE_APPLICATION_CREDENTIALS` if set,
    otherwise Application Default Credentials.
    """
    from google.cloud import storage

    project_id = os.environ.get("GCP_PROJECT_ID")
    client = storage.Client(project=project_id) if project_id else storage.Client()
    blob = client.bucket(bucket_name).blob(object_name)
    return blob.download_as_text()


def _read_gcs_json(bucket_name: str, object_name: str) -> dict[str, object]:
    """Download and decode one JSON artifact from GCS."""
    return json.loads(_read_gcs_text(bucket_name, object_name))


def get_dataset_quality() -> dict[str, object]:
    """Report dataset and data-quality details ("processing/dataset/flow" detail)."""
    bucket = _bucket_name()
    if not bucket:
        raise NotImplementedError("DIABETES_GCS_BUCKET is not set in .env (see .env.example)")

    quality_data = _read_gcs_json(bucket, "data/outputs/quality/data_quality.json")
    report_data = _read_gcs_json(bucket, "data/processed/preprocessing_report.json")

    missing_after = report_data.get("missing_values_after", {})
    if isinstance(missing_after, dict):
        missing_count = sum(value for value in missing_after.values() if isinstance(value, (int, float)))
    else:
        missing_count = missing_after if isinstance(missing_after, (int, float)) else 0

    quality_status = quality_data.get("quality_status")
    if quality_status is None:
        schema = quality_data.get("schema", {})
        missing_columns = schema.get("missing_columns", []) if isinstance(schema, dict) else []
        quality_status = "PASS" if not missing_columns and missing_count == 0 else "WARN"

    return {
        "input_rows": report_data.get("input_rows", quality_data.get("input_rows", quality_data.get("rows", 0))),
        "output_rows": report_data.get("output_rows", 0),
        "input_columns": report_data.get("input_columns", quality_data.get("input_columns", quality_data.get("columns", 0))),
        "duplicate_records_removed": report_data.get("duplicates_removed", report_data.get("duplicate_records_removed", quality_data.get("duplicate_count", 0))),
        "missing_values_after": missing_count,
        "quality_status": quality_status,
        "target_column": report_data.get("target_column", quality_data.get("schema", {}).get("target_column", "")),
    }


def get_model_comparison() -> dict[str, object]:
    """Report the optional model comparison results.

    API: Cloud Storage JSON API -- objects.get
    Required IAM role: roles/storage.objectViewer
    Objects: `gs://{bucket}/data/outputs/model_evaluation.csv` and
             `gs://{bucket}/data/outputs/feature_importance.csv`

    Suggested return shape:
        {
            "logistic_regression": {"accuracy": 0.6292, "balanced_accuracy": 0.5135},
            "random_forest": {"accuracy": 0.8247, "balanced_accuracy": 0.3839},
            "top_feature": "BMI",
        }
    """
    bucket = _bucket_name()
    if not bucket:
        raise NotImplementedError(
            "DIABETES_GCS_BUCKET is not set in .env (see .env.example) -- "
            "configure it before calling this endpoint."
        )

    evaluation_csv = _read_gcs_text(bucket, "data/outputs/model_evaluation.csv")
    metrics_by_model: dict[str, dict[str, float]] = {}
    for row in csv.DictReader(io.StringIO(evaluation_csv)):
        key = row["Model"].strip().lower().replace(" ", "_")
        metrics_by_model[key] = {
            "accuracy": float(row["Accuracy"]),
            "balanced_accuracy": float(row["Balanced Accuracy"]),
            "precision": float(row["Precision"]),
            "recall": float(row["Recall"]),
            "f1_score": float(row["F1 Score"]),
        }

    importance_csv = _read_gcs_text(bucket, "data/outputs/feature_importance.csv")
    top_row = next(csv.DictReader(io.StringIO(importance_csv)), {})

    return {
        "logistic_regression": metrics_by_model.get("logistic_regression", {}),
        "random_forest": metrics_by_model.get("random_forest", {}),
        "top_feature": top_row.get("Feature", ""),
    }


def get_latest_run() -> dict[str, object]:
    """Report the most recent pipeline execution log."""
    bucket = _bucket_name()
    if not bucket:
        raise NotImplementedError("DIABETES_GCS_BUCKET is not set in .env (see .env.example)")

    try:
        return _read_gcs_json(bucket, "data/outputs/execution/latest_run.json")
    except Exception as e:
        raise RuntimeError(f"Failed to read latest_run.json from GCS bucket {bucket}: {e}") from e
