"""FastAPI application exposing details about the diabetes-risk pipeline.

This satisfies Assessment Sub-Objective 2 (API Access):
  - Objective 2 ("Access the application's details using APIs") -- this
    app IS that API layer, tested with an API client (Swagger/OpenAPI or
    Postman/curl) and documented with request/response screenshots and
    HTTP status codes (activities 3.1-3.3).
  - Activity 3.1 ("Use Built-in APIs to access important application
    information, e.g. flow, deployment etc.") -- the data behind these
    endpoints comes from GCP's built-in APIs (Cloud Composer, Airflow, and
    Cloud Storage). Dataset-quality, execution-log, and model results are
    the pipeline's own generated artifacts, retrieved from GCS via
    `local_service.py`.

Endpoints cover the four required "application detail" categories from
Assignment_1_Workload_Plan.md Section 8, Step 4:
  1. Workflow or pipeline information       -> /api/v1/workflow       (GCP)
    2. Latest execution status                -> /api/v1/runs/latest    (GCS)
  3. Processing, dataset, or flow info       -> /api/v1/dataset        (local)
  4. Schedule/deployment/model/history info  -> /api/v1/schedule       (GCP)
Plus an optional fifth (model results)       -> /api/v1/model          (local)

Each endpoint is a thin wrapper: it calls one service-layer function and
returns the result. Service functions are implemented in `gcp_service.py`
and `local_service.py`; they remain straightforward to test with mocked
GCP and GCS responses.
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import gcp_service, local_service

# Load .env once at startup so GCP_PROJECT_ID / DIABETES_GCS_BUCKET / etc.
# (see .env.example) are available to gcp_service.py and local_service.py
# without having to export them manually before running uvicorn.
load_dotenv()

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


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Turn any other uncaught exception into a clean, CORS-safe 500.

    Without a registered handler, an uncaught exception (e.g. a missing
    dependency raising ModuleNotFoundError, or a real GCP/auth error) is
    handled by Starlette's outermost error middleware, which sits OUTSIDE
    CORSMiddleware -- so the resulting response has no CORS headers, and
    the browser reports it to the dashboard's JS as "API unreachable"
    (a network-level failure) instead of a normal error response. This
    handler runs inside the app's own exception-handling layer (same as
    the NotImplementedError handler above), so CORSMiddleware still
    applies and the dashboard can show a real "Error" instead.
    """
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
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
# Application detail #2: Latest execution status (GCS-backed)
# ============================================================

@app.get("/api/v1/runs/latest", tags=["pipeline"])
def latest_run() -> dict[str, object]:
    """Most recent pipeline execution log, including warnings and errors."""
    return local_service.get_latest_run()


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
