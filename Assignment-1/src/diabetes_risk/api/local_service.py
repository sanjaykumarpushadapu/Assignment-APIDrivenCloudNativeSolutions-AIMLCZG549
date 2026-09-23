"""Service layer for the dataset-quality and model-results endpoints.

These are the pipeline's own generated artifacts (not Composer/Airflow
state), but per activity 3.1 ("Use Built-in APIs") they are still
retrieved through a GCP built-in API -- the Cloud Storage API -- reading
the same bucket objects the DAG itself writes
(`dags/diabetes_risk_pipeline.py` uses `DIABETES_GCS_BUCKET` /
`GCS_OUTPUT_PREFIX = "data/outputs"`), rather than the local filesystem.

`get_dataset_quality()`, `get_latest_run()`, and `get_model_comparison()`
read JSON/CSV artifacts from GCS using `google-cloud-storage` (install via
`pip install -e ".[gcp]"`; the library is not part of the default API
dependencies).
"""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime, timedelta, timezone


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
    return json.loads(_read_gcs_text(bucket_name, object_name))


def _list_gcs_text(
    bucket_name: str,
    prefix: str,
    limit: int,
    start_offset: str | None = None,
) -> list[tuple[str, str]]:
    from google.cloud import storage

    project_id = os.environ.get("GCP_PROJECT_ID")
    client = storage.Client(project=project_id) if project_id else storage.Client()
    blobs = sorted(
        client.bucket(bucket_name).list_blobs(
            prefix=prefix,
            start_offset=start_offset,
            page_size=max(100, limit * 10),
        ),
        key=lambda blob: blob.name,
        reverse=True,
    )[:limit]
    return [
        (blob.name, blob.download_as_text())
        for blob in blobs
    ]


def get_execution_history(limit: int = 10) -> list[dict[str, object]]:
    """Return recent pipeline run manifests stored by the scheduled DAG."""
    bucket = _bucket_name()
    if not bucket:
        raise NotImplementedError(
            "DIABETES_GCS_BUCKET is not set in .env (see .env.example) -- "
            "configure it before calling this endpoint."
        )

    prefix = "data/outputs/execution/run_"
    recent_start = datetime.now(timezone.utc) - timedelta(days=1)
    start_offset = f"{prefix}{recent_start.strftime('%Y%m%dT%H%M%S')}"
    entries = _list_gcs_text(bucket, prefix, max(1, limit), start_offset)
    runs = []
    for object_name, content in entries:
        if not object_name.endswith(".json"):
            continue
        run = json.loads(content)
        started_at = run.get("started_at")
        runs.append(
            {
                "dag_run_id": run.get("run_id") or object_name.rsplit("/", 1)[-1][4:-5],
                "state": str(run.get("status", "unknown")).lower(),
                "start_date": started_at,
                "end_date": run.get("ended_at"),
                "duration_seconds": run.get("duration_seconds"),
                "records_processed": run.get("records_processed", run.get("input_rows")),
                "errors": run.get("errors", []),
                "warnings": run.get("warnings", []),
            }
        )
    runs.sort(key=lambda run: str(run.get("start_date") or ""), reverse=True)
    return runs


def get_dataset_quality() -> dict[str, object]:
    """Report dataset and data-quality details ("processing/dataset/flow" detail).

    API: Cloud Storage JSON API -- objects.get
    Docs: https://cloud.google.com/storage/docs/json_api/v1/objects/get
    Required IAM role: roles/storage.objectViewer
    Objects: `gs://{bucket}/data/outputs/quality/data_quality.json` and
             `gs://{bucket}/data/processed/preprocessing_report.json`

    Returns a compact summary suitable for the dashboard, combining the
    quality report and preprocessing report written by the pipeline.
    """
    bucket = _bucket_name()
    if not bucket:
        raise NotImplementedError(
            "DIABETES_GCS_BUCKET is not set in .env (see .env.example) -- "
            "configure it before calling this endpoint."
        )

    quality = _read_gcs_json(bucket, "data/outputs/quality/data_quality.json")
    preprocessing = _read_gcs_json(bucket, "data/processed/preprocessing_report.json")
    missing_after = preprocessing.get("missing_values_after", {})
    missing_count = sum(
        int(value or 0) for value in missing_after.values()
    ) if isinstance(missing_after, dict) else 0
    schema = quality.get("schema", {})
    schema_ok = isinstance(schema, dict) and not schema.get("missing_columns")
    quality_status = quality.get("quality_status") or (
        "PASS" if schema_ok and missing_count == 0 else "REVIEW"
    )

    return {
        "input_rows": preprocessing.get("input_rows", quality.get("rows", 0)),
        "output_rows": preprocessing.get("output_rows", quality.get("rows", 0)),
        "input_columns": quality.get("columns", 0),
        "duplicate_records_removed": preprocessing.get(
            "duplicates_removed", preprocessing.get("duplicates_detected", 0)
        ),
        "missing_values_after": missing_count,
        "quality_status": quality_status,
        "target_column": preprocessing.get("target_column"),
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
    if not bucket:
        raise NotImplementedError(
            "DIABETES_GCS_BUCKET is not set in .env (see .env.example) -- "
            "configure it before calling this endpoint."
        )
    return _read_gcs_json(bucket, "data/outputs/execution/latest_run.json")
