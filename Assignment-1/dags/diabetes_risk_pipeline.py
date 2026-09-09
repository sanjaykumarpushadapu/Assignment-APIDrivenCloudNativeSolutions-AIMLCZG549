"""Cloud-agnostic Airflow DAG for the diabetes risk pipeline.

The DAG intentionally uses only Airflow's PythonOperator and invokes the same
platform-neutral runner used by local execution. Cloud Composer can deploy this
DAG unchanged; cloud storage/authentication can be introduced through the
runtime environment without embedding GCP SDK calls in the DAG.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from pendulum import datetime

from diabetes_risk.pipeline.runner import run


def run_diabetes_pipeline() -> dict[str, object]:
    input_path = Path(os.getenv("DIABETES_DATASET_PATH", "data/raw/diabetes_012_health_indicators_BRFSS2015.csv"))
    processed_dir = Path(os.getenv("DIABETES_OUTPUT_DIR", "data/processed"))
    report_dir = Path(os.getenv("DIABETES_REPORT_DIR", "data/outputs"))
    target_column = os.getenv("DIABETES_TARGET_COLUMN", "Diabetes_012")
    return run(input_path, processed_dir, target_column=target_column, report_dir=report_dir)


with DAG(
    dag_id="diabetes_risk_pipeline",
    start_date=datetime(2026, 1, 1, tz="UTC"),
    schedule="*/2 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "group-49-person-2",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["diabetes", "assignment-1", "dataops"],
    description="Every-two-minute data-quality, preprocessing and EDA pipeline.",
) as dag:
    pipeline = PythonOperator(
        task_id="data_quality_preprocessing_and_eda",
        python_callable=run_diabetes_pipeline,
    )
