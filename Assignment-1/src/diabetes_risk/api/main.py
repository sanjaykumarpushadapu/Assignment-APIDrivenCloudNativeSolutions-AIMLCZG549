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

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import gcp_service, local_service

app = FastAPI(
    title="Diabetes Risk Screening API",
    version="0.1.0",
    description="Non-diagnostic risk-screening pipeline endpoints.",
)

# The dashboard (src/diabetes_risk/dashboard/app.py) runs on a different
# port and calls this API from browser-side JS, so it needs CORS enabled.
# DASHBOARD_ORIGIN defaults to the dashboard's documented local port
# (see README.md "Run the dashboard"); override in .env if you serve it
# elsewhere. "*" is fine for local development/demo, not for production.
_DASHBOARD_ORIGIN = os.environ.get("DASHBOARD_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_DASHBOARD_ORIGIN] if _DASHBOARD_ORIGIN != "*" else ["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(NotImplementedError)
def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    """Turn a skeleton function's NotImplementedError into a clean 501.

    Without this, FastAPI would return a generic 500 for every endpoint
    that still delegates to an unimplemented gcp_service/local_service
    function. A 501 is the honest, correct status code for "this route
    exists but isn't implemented yet" -- useful to show during API testing
    (activity 3.3) even before gcp_service.py is filled in for real.
    """
    return JSONResponse(
        status_code=501,
        content={"error": "not_implemented", "detail": str(exc)},
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
