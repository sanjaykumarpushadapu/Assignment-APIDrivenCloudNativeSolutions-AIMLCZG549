"""Service layer: calls Google Cloud's *built-in* APIs as a client.

This is what activity 3.1 ("Use Built-in APIs to access important
application information (e.g., flow, deployment etc.)") refers to --
Cloud Composer's own Environments API, the Airflow REST API hosted by
Composer, and Cloud Monitoring. `main.py`'s FastAPI endpoints call the
functions in this module and re-expose the results as the application's
own tested API (satisfying Objective 2, "Access the application's details
using APIs").

`get_composer_environment_details()` is implemented for real, as a
reference for the remaining three functions (`get_dag_run_history()`,
`get_task_instance_status()`, `get_environment_health()`), which are
still skeletons: signature, docstring (exact GCP API/method, required
IAM role, and a suggested return shape), and a `NotImplementedError`
body. Implement those with either:
  - `google-cloud-orchestration-airflow` (Composer Environments API), or
  - direct authenticated HTTP requests (`google-auth` + `requests`) to the
    Composer-hosted Airflow REST API and the Cloud Monitoring REST API.
These are NOT in `pyproject.toml`'s default dependencies -- see the
`gcp` optional dependency group added there, and install with
`pip install -e ".[gcp]"` once you start implementing.

All functions accept an optional `config` so they're easy to unit test
with a fake `GCPConfig` instead of hitting real GCP.
"""

from __future__ import annotations

from .gcp_config import GCPConfig, load_gcp_config


def _load_credentials(config: GCPConfig):
    """Build explicit credentials from GOOGLE_APPLICATION_CREDENTIALS.

    Loading the key file explicitly (rather than relying only on ambient
    Application Default Credentials) keeps every function here easy to
    unit test with a fake `GCPConfig`, per this module's own docstring.
    Falls back to `None` (Application Default Credentials) if no path is
    configured, so this also works with `gcloud auth application-default
    login` for teammates who were granted IAM roles directly instead of a
    shared key file.
    """
    if not config.credentials_path:
        return None
    from google.oauth2 import service_account

    return service_account.Credentials.from_service_account_file(config.credentials_path)


def get_composer_environment_details(config: GCPConfig | None = None) -> dict[str, object]:
    """Report the Composer environment's own deployment details ("deployment").

    API: Cloud Composer API v1 -- projects.locations.environments.get
    Docs: https://cloud.google.com/composer/docs/reference/rest/v1/projects.locations.environments/get
    Required IAM role: roles/composer.viewer (or higher)
    Auth: Application Default Credentials, or a service-account key file
          referenced by GOOGLE_APPLICATION_CREDENTIALS.

    Suggested return shape:
        {
            "name": "diabetes-risk-env",
            "state": "RUNNING",
            "airflow_version": "2.11.1",
            "gcs_bucket": "us-central1-diabetes-risk-e-xxxxx-bucket",
        }
    """
    config = config or load_gcp_config()
    if not config.is_configured():
        raise NotImplementedError(
            "GCP is not configured: set GCP_PROJECT_ID, GCP_LOCATION and "
            "GCP_COMPOSER_ENVIRONMENT in .env (see .env.example) before "
            "calling this endpoint."
        )

    from google.cloud.orchestration.airflow.service_v1 import EnvironmentsClient

    credentials = _load_credentials(config)
    client = EnvironmentsClient(credentials=credentials) if credentials else EnvironmentsClient()
    name = client.environment_path(config.project_id, config.location, config.composer_environment)
    environment = client.get_environment(name=name)

    dag_gcs_prefix = environment.config.dag_gcs_prefix or ""
    gcs_bucket = dag_gcs_prefix[len("gs://"):].split("/", 1)[0] if dag_gcs_prefix else ""

    return {
        "name": environment.name.rsplit("/", 1)[-1],
        "state": environment.state.name,
        "airflow_version": environment.config.software_config.image_version,
        "gcs_bucket": gcs_bucket,
    }


def get_dag_run_history(
    dag_id: str = "diabetes_risk_pipeline",
    limit: int = 5,
    config: GCPConfig | None = None,
) -> list[dict[str, object]]:
    """Report recent DAG runs -- the pipeline's execution "flow".

    API: Airflow REST API -- GET /dags/{dag_id}/dagRuns
    Docs: https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/DAGRun/paths/~1dags~1%7Bdag_id%7D~1dagRuns/get
    Access: the Composer environment's Airflow web server, via an
            IAP-authenticated request -- see Google's "Accessing the
            Airflow REST API" guide for Cloud Composer 2.

    Suggested return shape:
        [
            {
                "dag_run_id": "scheduled__2026-09-12T12:10:00+00:00",
                "state": "success",
                "start_date": "2026-09-12T12:12:00Z",
                "end_date": "2026-09-12T12:15:00Z",
            },
            ...
        ]
    """
    config = config or load_gcp_config()
    raise NotImplementedError(
        "TODO: call the Airflow REST API dagRuns endpoint and map the response"
    )


def get_task_instance_status(
    dag_id: str,
    dag_run_id: str,
    config: GCPConfig | None = None,
) -> list[dict[str, object]]:
    """Report per-task status within one DAG run (schedule/execution detail).

    API: Airflow REST API -- GET /dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances
    Docs: https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#tag/TaskInstance

    Suggested return shape:
        [
            {"task_id": "data_quality_preprocessing_and_eda", "state": "success", "duration": 17.88},
            {"task_id": "random_forest", "state": "success", "duration": 79.59},
            {"task_id": "model_evaluation", "state": "success", "duration": 85.61},
        ]
    """
    config = config or load_gcp_config()
    raise NotImplementedError(
        "TODO: call the Airflow REST API taskInstances endpoint and map the response"
    )


def get_environment_health(config: GCPConfig | None = None) -> dict[str, object]:
    """Report Composer environment health from Cloud Monitoring.

    API: Cloud Monitoring API v3 -- projects.timeSeries.list
    Docs: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.timeSeries/list
    Required IAM role: roles/monitoring.viewer
    Suggested metric type: "composer.googleapis.com/environment/healthy"

    Suggested return shape:
        {
            "environment_healthy": True,
            "checked_at": "2026-09-12T12:21:00Z",
        }
    """
    config = config or load_gcp_config()
    raise NotImplementedError(
        "TODO: call Cloud Monitoring projects.timeSeries.list and map the response"
    )
