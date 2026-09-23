"""Service layer: calls Google Cloud's *built-in* APIs as a client.

This is what activity 3.1 ("Use Built-in APIs to access important
application information (e.g., flow, deployment etc.)") refers to --
Cloud Composer's own Environments API, the Airflow REST API hosted by
Composer, and Cloud Monitoring. `main.py`'s FastAPI endpoints call the
functions in this module and re-expose the results as the application's
own tested API (satisfying Objective 2, "Access the application's details
using APIs").

`get_composer_environment_details()`, `get_dag_run_history()`, and
`get_task_instance_status()` are implemented with the Composer Environments
API and the Composer-hosted Airflow REST API. `get_environment_health()`
remains an optional, unwired Cloud Monitoring extension. GCP libraries are
in the optional dependency group; install with `pip install -e ".[gcp]"`.

All functions accept an optional `config` so they're easy to unit test
with a fake `GCPConfig` instead of hitting real GCP.
"""

from __future__ import annotations

import subprocess
import os
from urllib.parse import quote

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


def _get_composer_environment(config: GCPConfig):
    from google.cloud.orchestration.airflow.service_v1 import EnvironmentsClient

    credentials = _load_credentials(config)
    client = EnvironmentsClient(credentials=credentials) if credentials else EnvironmentsClient()
    name = client.environment_path(config.project_id, config.location, config.composer_environment)
    return client.get_environment(name=name)


def _airflow_api_get(config: GCPConfig, path: str, params: dict[str, object] | None = None) -> dict[str, object]:
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass

    from google.auth.transport.requests import Request
    from google.oauth2 import id_token
    import requests

    environment = _get_composer_environment(config)
    airflow_uri = environment.config.airflow_uri.rstrip("/")
    if not airflow_uri:
        raise RuntimeError("The configured Cloud Composer environment has no Airflow web-server URL.")
    try:
        token = id_token.fetch_id_token(Request(), airflow_uri)
    except Exception as adc_error:
        service_account = os.environ.get("GCP_IAP_SERVICE_ACCOUNT")
        if not service_account and config.project_id:
            service_account = f"diabetes-risk-runtime@{config.project_id}.iam.gserviceaccount.com"
        if not service_account:
            raise RuntimeError(
                "Local Airflow access requires GCP_IAP_SERVICE_ACCOUNT to name "
                "a service account that can access the Composer web server."
            ) from adc_error
        try:
            token_result = subprocess.run(
                subprocess.list2cmdline(
                    [
                        "gcloud",
                        "auth",
                        "print-identity-token",
                        f"--audiences={airflow_uri}",
                        f"--impersonate-service-account={service_account}",
                        "--include-email",
                    ]
                ),
                check=True,
                capture_output=True,
                text=True,
                shell=True,
                timeout=30,
            )
            token = token_result.stdout.strip()
            if not token:
                raise RuntimeError("gcloud returned an empty identity token.")
        except Exception as cli_error:
            raise RuntimeError(
                "Could not obtain an audience-bound Composer identity token. "
                "Grant the active user roles/iam.serviceAccountTokenCreator on "
                f"{service_account}, and ensure that service account has "
                "roles/composer.viewer and roles/composer.user."
            ) from cli_error
    response = requests.get(
        f"{airflow_uri}/api/v1/{path.lstrip('/')}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Airflow API returned an unexpected response shape.")
    return payload


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

    environment = _get_composer_environment(config)

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
    if not config.is_configured():
        raise NotImplementedError(
            "GCP is not configured: set GCP_PROJECT_ID, GCP_LOCATION and "
            "GCP_COMPOSER_ENVIRONMENT in .env (see .env.example) before "
            "calling this endpoint."
        )
    payload = _airflow_api_get(
        config,
        f"dags/{quote(dag_id, safe='')}/dagRuns",
        params={"limit": max(1, limit), "order_by": "-start_date"},
    )
    return [
        {
            "dag_run_id": run.get("dag_run_id"),
            "state": run.get("state"),
            "start_date": run.get("start_date"),
            "end_date": run.get("end_date"),
        }
        for run in payload.get("dag_runs", [])
    ]


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
    if not config.is_configured():
        raise NotImplementedError(
            "GCP is not configured: set GCP_PROJECT_ID, GCP_LOCATION and "
            "GCP_COMPOSER_ENVIRONMENT in .env (see .env.example) before "
            "calling this endpoint."
        )
    payload = _airflow_api_get(
        config,
        f"dags/{quote(dag_id, safe='')}/dagRuns/{quote(dag_run_id, safe='')}/taskInstances",
    )
    return [
        {
            "task_id": task.get("task_id"),
            "state": task.get("state"),
            "duration": task.get("duration"),
            "start_date": task.get("start_date"),
            "end_date": task.get("end_date"),
        }
        for task in payload.get("task_instances", [])
    ]


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
