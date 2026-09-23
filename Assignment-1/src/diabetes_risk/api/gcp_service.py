"""Service layer: calls Google Cloud's *built-in* APIs as a client.

This is what activity 3.1 ("Use Built-in APIs to access important
application information (e.g., flow, deployment etc.)") refers to --
Cloud Composer's own Environments API, the Airflow REST API hosted by
Composer, and Cloud Monitoring. `main.py`'s FastAPI endpoints call the
functions in this module and re-expose the results as the application's
own tested API (satisfying Objective 2, "Access the application's details
using APIs").

The service functions use the optional `gcp` dependencies. Functions
accept an optional `config` so they can be unit tested without calling
real GCP services.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote
import requests
import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

from .gcp_config import GCPConfig, load_gcp_config

def _get_composer_web_server_url(config: GCPConfig) -> str:
    """Retrieves the Airflow Web UI URL from the Composer Environment details."""
    from google.cloud.orchestration.airflow.service_v1 import EnvironmentsClient
    credentials = _load_credentials(config)
    client = EnvironmentsClient(credentials=credentials) if credentials else EnvironmentsClient()
    name = client.environment_path(config.project_id, config.location, config.composer_environment)
    environment = client.get_environment(name=name)
    return environment.config.airflow_uri.rstrip("/")

def _get_iap_headers(web_server_url: str) -> dict[str, str]:
    """Obtains an IAP Bearer ID token for Airflow REST API authentication."""
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, web_server_url)
    return {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

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


def _airflow_api_get(
    config: GCPConfig,
    path: str,
    params: dict[str, object] | None = None,
) -> dict[str, object]:
    """Make an authenticated GET request to the Composer Airflow API."""
    web_url = _get_composer_web_server_url(config)
    response = requests.get(
        f"{web_url}/api/v1/{path.lstrip('/')}",
        headers=_get_iap_headers(web_url),
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


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
    limit: int = 10,
    config: GCPConfig | None = None,
) -> list[dict[str, object]]:
    """Report recent DAG runs -- the pipeline's execution "flow"."""
    config = config or load_gcp_config()
    if not config.is_configured():
        raise NotImplementedError("GCP is not configured: set GCP_PROJECT_ID, GCP_LOCATION and GCP_COMPOSER_ENVIRONMENT in .env")

    try:
        data = _airflow_api_get(
            config,
            f"dags/{quote(dag_id, safe='')}/dagRuns",
            params={"limit": limit, "order_by": "-execution_date"},
        )
        runs = []
        for run in data.get("dag_runs", []):
            runs.append({
                "dag_run_id": run.get("dag_run_id"),
                "state": run.get("state"),
                "start_date": run.get("start_date"),
                "end_date": run.get("end_date"),
            })
        return runs
    except Exception as e:
        raise RuntimeError(f"Failed to fetch DAG run history from Airflow REST API: {e}") from e


def get_task_instance_status(
    dag_id: str,
    dag_run_id: str,
    config: GCPConfig | None = None,
) -> list[dict[str, object]]:
    """Report per-task status within one DAG run (schedule/execution detail)."""
    config = config or load_gcp_config()
    if not config.is_configured():
        raise NotImplementedError("GCP is not configured: set GCP_PROJECT_ID, GCP_LOCATION and GCP_COMPOSER_ENVIRONMENT in .env")

    try:
        data = _airflow_api_get(
            config,
            f"dags/{quote(dag_id, safe='')}/dagRuns/{quote(dag_run_id, safe='')}/taskInstances",
        )

        tasks = []
        for task in data.get("task_instances", []):
            tasks.append({
                "task_id": task.get("task_id"),
                "state": task.get("state"),
                "duration": task.get("duration"),
                "start_date": task.get("start_date"),
                "end_date": task.get("end_date"),
            })
        return tasks
    except Exception as e:
        raise RuntimeError(f"Failed to fetch task instance status from Airflow REST API: {e}") from e


def get_environment_health(config: GCPConfig | None = None) -> dict[str, object]:
    """Report Composer environment health from Cloud Monitoring."""
    config = config or load_gcp_config()
    if not config.is_configured():
        raise NotImplementedError("GCP is not configured: set GCP_PROJECT_ID, GCP_LOCATION and GCP_COMPOSER_ENVIRONMENT in .env")

    from google.cloud import monitoring_v3
    import time

    credentials = _load_credentials(config)
    client = monitoring_v3.MetricServiceClient(credentials=credentials) if credentials else monitoring_v3.MetricServiceClient()
    
    project_name = f"projects/{config.project_id}"
    now = time.time()
    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(now)},
        "start_time": {"seconds": int(now - 300)}  # Past 5 minutes
    })

    metric_type = "composer.googleapis.com/environment/healthy"
    try:
        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": f'metric.type = "{metric_type}" AND resource.labels.environment_name = "{config.composer_environment}"',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )

        is_healthy = False
        latest_time = None

        for result in results:
            for point in result.points:
                is_healthy = point.value.bool_value
                latest_time = point.interval.start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                break

        return {
            "environment_healthy": is_healthy,
            "checked_at": latest_time or datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Cloud Monitoring health metrics: {e}") from e
