# Person 2 — Airflow Orchestration

`dags/diabetes_risk_pipeline.py` is intentionally cloud agnostic.

It uses only Airflow's Python operator and invokes the same platform-neutral `diabetes_risk.pipeline.runner.run()` used by local execution.

There are no GCP SDK imports, GCS operators, Vertex AI operators, or GCP-specific credentials in the DAG.

The same DAG is intended to run in:

- local/self-hosted Airflow for development and testing
- Google Cloud Composer for the planned production deployment

## Schedule

```text
*/2 * * * *
```

This triggers the complete Person-2 data-quality, preprocessing and EDA pipeline every two minutes.

## Reliability

`max_active_runs=1` prevents overlapping DAG runs. One retry is configured with a one-minute retry delay for transient task failures.

## Cloud deployment boundary

Cloud Composer and Cloud Storage configuration belong under `infra/gcp/`. The processing code and DAG remain unchanged; environment variables can supply runtime input/output locations.
