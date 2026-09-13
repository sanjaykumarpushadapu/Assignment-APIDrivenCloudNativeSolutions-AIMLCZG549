"""Service layer for the dataset-quality and model-results endpoints.

These are the pipeline's own generated artifacts (not Composer/Airflow
state), but per activity 3.1 ("Use Built-in APIs") they are still
retrieved through a GCP built-in API -- the Cloud Storage API -- reading
the same bucket objects the DAG itself writes
(`dags/diabetes_risk_pipeline.py` uses `DIABETES_GCS_BUCKET` /
`GCS_OUTPUT_PREFIX = "data/outputs"`), rather than the local filesystem.

Every function is a skeleton only: signature, docstring naming the exact
GCS object(s) to read, required IAM role, and a `NotImplementedError`
body. Implement with `google-cloud-storage` (already a runtime dependency
of `dags/diabetes_risk_pipeline.py`, so no new package is needed here).
"""

from __future__ import annotations

import os


def _bucket_name() -> str:
    """Read the target bucket name.

    Reuses `DIABETES_GCS_BUCKET`, the same environment variable
    `dags/diabetes_risk_pipeline.py` uses, so both the DAG and this API
    point at one bucket.
    """
    return os.environ.get("DIABETES_GCS_BUCKET", "")


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
    raise NotImplementedError(
        f"TODO: use google-cloud-storage to read "
        f"gs://{bucket}/data/outputs/model_evaluation.csv and "
        f"gs://{bucket}/data/outputs/feature_importance.csv, then return as a JSON-friendly dict"
    )


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
