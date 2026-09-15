"""Service layer for the dataset-quality and model-results endpoints.

These are the pipeline's own generated artifacts (not Composer/Airflow
state), but per activity 3.1 ("Use Built-in APIs") they are still
retrieved through a GCP built-in API -- the Cloud Storage API -- reading
the same bucket objects the DAG itself writes
(`dags/diabetes_risk_pipeline.py` uses `DIABETES_GCS_BUCKET` /
`GCS_OUTPUT_PREFIX = "data/outputs"`), rather than the local filesystem.

`get_model_comparison()` is implemented for real, as a reference for the
remaining two functions (`get_dataset_quality()`, `get_latest_run()`),
which are still skeletons: signature, docstring naming the exact GCS
object(s) to read, required IAM role, and a `NotImplementedError` body.
Implement those the same way, with `google-cloud-storage` (install via
`pip install -e ".[gcp]"`; it's a build dependency of
`dags/diabetes_risk_pipeline.py`, but not of this API by default).
"""

from __future__ import annotations

import csv
import io
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


def get_dataset_quality() -> dict[str, object]:
    """Report dataset and data-quality details ("processing/dataset/flow" detail).

    API: Cloud Storage JSON API -- objects.get
    Docs: https://cloud.google.com/storage/docs/json_api/v1/objects/get
    Required IAM role: roles/storage.objectViewer
    Objects: `gs://{bucket}/data/outputs/quality/data_quality.json` and
             `gs://{bucket}/data/processed/preprocessing_report.json`

    Suggested return shape:
        {
            "input_rows": 253680,
            "input_columns": 22,
            "duplicate_records_removed": 23899,
            "quality_status": "PASS_WITH_WARNINGS",
        }
    """
    bucket = _bucket_name()
    raise NotImplementedError(
        f"TODO: use google-cloud-storage to read "
        f"gs://{bucket}/data/outputs/quality/data_quality.json and "
        f"gs://{bucket}/data/processed/preprocessing_report.json, then merge the relevant fields"
    )


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
    """Report the most recent pipeline execution log.

    API: Cloud Storage JSON API -- objects.get
    Required IAM role: roles/storage.objectViewer
    Object: `gs://{bucket}/data/outputs/execution/latest_run.json`
    (written by `src/diabetes_risk/pipeline/logging_utils.py` on every run)

    Suggested return shape: the JSON object's own fields, e.g.
        {
            "run_id": "20260912T025251232582Z",
            "status": "SUCCESS",
            "started_at": "...",
            "ended_at": "...",
            "duration_seconds": 5.1,
            "records_processed": 253680,
            "duplicates_detected": 23899,
        }
    """
    bucket = _bucket_name()
    raise NotImplementedError(
        f"TODO: use google-cloud-storage to read "
        f"gs://{bucket}/data/outputs/execution/latest_run.json and return its contents"
    )
