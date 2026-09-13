"""FastAPI application exposing details about the diabetes-risk pipeline.

This satisfies Assessment Sub-Objective 2 (API Access):
  - Objective 2 ("Access the application's details using APIs") -- this
    app IS that API layer, tested with an API client (Swagger/OpenAPI or
    Postman/curl) and documented with request/response screenshots and
    HTTP status codes (activities 3.1-3.3).
  - Activity 3.1 ("Use Built-in APIs to access important application
    information, e.g. flow, deployment etc.") -- the data behind these
    endpoints should come from GCP's own built-in APIs (Cloud Composer,
    the Airflow REST API, Cloud Monitoring), via `gcp_service.py`, for the
    workflow/schedule/deployment details. Dataset-quality and model
    results are the pipeline's own generated artifacts, so those two
    endpoints read local files via `local_service.py` instead.

Endpoints cover the four required "application detail" categories from
Assignment_1_Workload_Plan.md Section 8, Step 4:
  1. Workflow or pipeline information       -> /api/v1/workflow       (GCP)
  2. Latest execution status                -> /api/v1/runs/latest    (GCP)
  3. Processing, dataset, or flow info       -> /api/v1/dataset        (local)
  4. Schedule/deployment/model/history info  -> /api/v1/schedule       (GCP)
Plus an optional fifth (model results)       -> /api/v1/model          (local)

Each endpoint is a thin wrapper: it calls one service-layer function and
returns the result. The service-layer functions are the actual skeletons
(signature + docstring + `NotImplementedError`) -- see `gcp_service.py`
and `local_service.py`. Nothing below needs to change once those are
implemented.
"""

from datetime import datetime, timezone

from fastapi import FastAPI

from . import gcp_service, local_service

app = FastAPI(
    title="Diabetes Risk Screening API",
    version="0.1.0",
    description="Non-diagnostic risk-screening pipeline endpoints.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/metadata", tags=["pipeline"])
def metadata() -> dict[str, str]:
    return {
        "project": "Diabetes Risk Prediction Using Health and Lifestyle Indicators",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "For risk screening only; not a medical diagnosis.",
    }


# ============================================================
# Application detail #1: Workflow / pipeline information (GCP-backed)
# ============================================================

@app.get("/api/v1/workflow", tags=["pipeline"])
def workflow_info() -> list[dict[str, object]]:
    """Recent DAG run history -- the pipeline's execution "flow".

    Delegates to `gcp_service.get_dag_run_history()` (Airflow REST API).
    """
    return gcp_service.get_dag_run_history()


# ============================================================
# Application detail #2: Latest execution status (GCP-backed)
# ============================================================

@app.get("/api/v1/runs/latest", tags=["pipeline"])
def latest_run() -> list[dict[str, object]]:
    """Most recent DAG run's task-level status.

    Resolves the latest `dag_run_id` from `get_dag_run_history()` first
    (Airflow orders dagRuns by execution date descending by default), then
    fetches that run's task instances. Both calls go through
    `gcp_service.py` (Airflow REST API) -- TODO (Person 4): implement
    `get_dag_run_history()` and `get_task_instance_status()` there; this
    function should not need to change once they are.
    """
    runs = gcp_service.get_dag_run_history(dag_id="diabetes_risk_pipeline", limit=1)
    if not runs:
        return []
    latest_dag_run_id = runs[0]["dag_run_id"]
    return gcp_service.get_task_instance_status(
        dag_id="diabetes_risk_pipeline",
        dag_run_id=latest_dag_run_id,
    )


# ============================================================
# Application detail #3: Processing / dataset / flow information (local)
# ============================================================

@app.get("/api/v1/dataset", tags=["pipeline"])
def dataset_info() -> dict[str, object]:
    """Dataset and data-quality details, from the pipeline's own output files.

    Delegates to `local_service.get_dataset_quality()`.
    """
    return local_service.get_dataset_quality()


# ============================================================
# Application detail #4: Schedule / deployment information (GCP-backed)
# ============================================================

@app.get("/api/v1/schedule", tags=["pipeline"])
def schedule_info() -> dict[str, object]:
    """Composer environment deployment details (schedule lives in the DAG
    file itself; deployment/version/health comes from GCP).

    Delegates to `gcp_service.get_composer_environment_details()`.
    """
    return gcp_service.get_composer_environment_details()


# ============================================================
# Optional fifth detail: optional model comparison results (local)
# ============================================================

@app.get("/api/v1/model", tags=["pipeline"])
def model_info() -> dict[str, object]:
    """Optional Random Forest vs. Logistic Regression comparison results.

    Delegates to `local_service.get_model_comparison()`.
    """
    return local_service.get_model_comparison()
