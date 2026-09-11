"""
Cloud Composer deployment DAG for the complete diabetes risk pipeline.

Pipeline:
1. Data quality + preprocessing + EDA
2. Random Forest + feature importance
3. Logistic Regression + model evaluation

Cloud Storage is used as the persistent hand-off between Airflow tasks.
The core pipeline code remains storage/orchestration neutral.
"""

from __future__ import annotations

import os
import shutil
from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from pendulum import datetime
from google.cloud import storage

from diabetes_risk.pipeline.runner import run


# ============================================================
# GCP / GCS CONFIGURATION
# ============================================================

GCS_BUCKET = os.getenv(
    "DIABETES_GCS_BUCKET",
    "apicloudsolutions49-diabetes-pipeline",
)

GCS_RAW_PREFIX = "data/raw"
GCS_PROCESSED_PREFIX = "data/processed"
GCS_OUTPUT_PREFIX = "data/outputs"


# ============================================================
# LOCAL WORKSPACE
# ============================================================

LOCAL_BASE_DIR = Path("/tmp/diabetes_risk_pipeline")
LOCAL_RAW_DIR = LOCAL_BASE_DIR / "data" / "raw"
LOCAL_PROCESSED_DIR = LOCAL_BASE_DIR / "data" / "processed"
LOCAL_OUTPUT_DIR = LOCAL_BASE_DIR / "data" / "outputs"

LOCAL_RAW_DATASET = (
    LOCAL_RAW_DIR
    / "diabetes_012_health_indicators_BRFSS2015.csv"
)


# ============================================================
# GCS HELPERS
# ============================================================

def get_gcs_client() -> storage.Client:
    """Create a GCS client using the Composer service account."""
    return storage.Client()


def upload_directory_to_gcs(
    local_dir: Path,
    gcs_prefix: str,
) -> None:
    """Upload all files under a local directory to GCS."""
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)

    if not local_dir.exists():
        raise FileNotFoundError(
            f"Local directory does not exist: {local_dir}"
        )

    for local_file in local_dir.rglob("*"):
        if not local_file.is_file():
            continue

        relative_path = local_file.relative_to(local_dir)
        blob_name = f"{gcs_prefix}/{relative_path}"

        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_file))

        print(
            f"Uploaded {local_file} "
            f"to gs://{GCS_BUCKET}/{blob_name}"
        )


def download_gcs_object(
    gcs_object: str,
    local_path: Path,
) -> None:
    """Download one GCS object to a local file."""
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(gcs_object)

    local_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    blob.download_to_filename(str(local_path))

    print(
        f"Downloaded gs://{GCS_BUCKET}/{gcs_object} "
        f"to {local_path}"
    )


def download_gcs_prefix(
    gcs_prefix: str,
    local_dir: Path,
) -> None:
    """Download all objects under a GCS prefix."""
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)

    local_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    blobs = client.list_blobs(
        GCS_BUCKET,
        prefix=gcs_prefix,
    )

    found = False

    for blob in blobs:
        if blob.name.endswith("/"):
            continue

        found = True

        relative_path = Path(
            blob.name[len(gcs_prefix):].lstrip("/")
        )

        local_path = local_dir / relative_path
        local_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        blob.download_to_filename(str(local_path))

        print(
            f"Downloaded gs://{GCS_BUCKET}/{blob.name} "
            f"to {local_path}"
        )

    if not found:
        raise FileNotFoundError(
            f"No GCS objects found under gs://"
            f"{GCS_BUCKET}/{gcs_prefix}"
        )


# ============================================================
# WORKSPACE SETUP
# ============================================================

def reset_workspace() -> None:
    """Create a clean local workspace for the task."""
    if LOCAL_BASE_DIR.exists():
        shutil.rmtree(LOCAL_BASE_DIR)

    LOCAL_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    LOCAL_PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    LOCAL_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# TASK 1
# PERSON 2 - DATA QUALITY + PREPROCESSING + EDA
# ============================================================

def run_diabetes_pipeline() -> dict[str, object]:
    """
    Download raw data from GCS, execute the existing Person-2
    pipeline, and upload generated artifacts back to GCS.
    """

    reset_workspace()

    download_gcs_object(
        f"{GCS_RAW_PREFIX}/"
        "diabetes_012_health_indicators_BRFSS2015.csv",
        LOCAL_RAW_DATASET,
    )

    target_column = os.getenv(
        "DIABETES_TARGET_COLUMN",
        "Diabetes_012",
    )

    summary = run(
        input_path=LOCAL_RAW_DATASET,
        output_dir=LOCAL_PROCESSED_DIR,
        target_column=target_column,
        report_dir=LOCAL_OUTPUT_DIR,
    )

    upload_directory_to_gcs(
        LOCAL_PROCESSED_DIR,
        GCS_PROCESSED_PREFIX,
    )

    upload_directory_to_gcs(
        LOCAL_OUTPUT_DIR,
        GCS_OUTPUT_PREFIX,
    )

    return summary


# ============================================================
# TASK 2
# PERSON 3 - RANDOM FOREST
# ============================================================

def run_random_forest() -> dict[str, str]:
    """
    Download the model-ready dataset from GCS, train Random Forest,
    and upload the model and feature-importance artifacts.
    """

    reset_workspace()

    download_gcs_object(
        f"{GCS_PROCESSED_PREFIX}/diabetes_model_ready.csv",
        LOCAL_PROCESSED_DIR / "diabetes_model_ready.csv",
    )

    from diabetes_risk.pipeline.randomforestclassifier import (
        train_random_forest,
    )

    result = train_random_forest(
        input_path=LOCAL_PROCESSED_DIR
        / "diabetes_model_ready.csv",
        report_dir=LOCAL_OUTPUT_DIR,
    )

    upload_directory_to_gcs(
        LOCAL_OUTPUT_DIR,
        GCS_OUTPUT_PREFIX,
    )

    return result


# ============================================================
# TASK 3
# PERSON 3 - MODEL EVALUATION
# ============================================================

def run_model_evaluation() -> dict[str, str]:
    """
    Download the model-ready dataset and Random Forest model,
    evaluate the models, and upload evaluation artifacts.
    """

    reset_workspace()

    download_gcs_object(
        f"{GCS_PROCESSED_PREFIX}/diabetes_model_ready.csv",
        LOCAL_PROCESSED_DIR / "diabetes_model_ready.csv",
    )

    # Random Forest model generated by Task 2.
    download_gcs_object(
        f"{GCS_OUTPUT_PREFIX}/random_forest_model.joblib",
        LOCAL_OUTPUT_DIR / "random_forest_model.joblib",
    )

    from diabetes_risk.pipeline.model_evaluation import (
        evaluate_models,
    )

    result = evaluate_models(
        input_path=LOCAL_PROCESSED_DIR
        / "diabetes_model_ready.csv",
        report_dir=LOCAL_OUTPUT_DIR,
    )

    upload_directory_to_gcs(
        LOCAL_OUTPUT_DIR,
        GCS_OUTPUT_PREFIX,
    )

    return result


# ============================================================
# AIRFLOW DAG
# ============================================================

with DAG(
    dag_id="diabetes_risk_pipeline",

    start_date=datetime(
        2026,
        1,
        1,
        tz="UTC",
    ),

    # Assignment requirement:
    # run every 2 minutes.
    schedule="*/2 * * * *",

    catchup=False,

    # Prevent overlapping complete pipeline executions.
    max_active_runs=1,

    default_args={
        "owner": "group-49-person-3",
        "retries": 1,
        "retry_delay": timedelta(
            minutes=1,
        ),
    },

    tags=[
        "diabetes",
        "assignment-1",
        "dataops",
        "person-2",
        "person-3",
        "gcp",
        "composer",
    ],

    description=(
        "Complete diabetes risk data and ML pipeline "
        "running every two minutes on Cloud Composer."
    ),
) as dag:

    data_quality_preprocessing_and_eda = PythonOperator(
        task_id="data_quality_preprocessing_and_eda",
        python_callable=run_diabetes_pipeline,
    )

    random_forest = PythonOperator(
        task_id="random_forest",
        python_callable=run_random_forest,
    )

    model_evaluation = PythonOperator(
        task_id="model_evaluation",
        python_callable=run_model_evaluation,
    )

    data_quality_preprocessing_and_eda >> random_forest
    random_forest >> model_evaluation
