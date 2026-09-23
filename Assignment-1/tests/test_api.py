import pytest
from fastapi.testclient import TestClient

from diabetes_risk.api.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metadata_endpoint() -> None:
    response = TestClient(app).get("/api/v1/metadata")

    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "Diabetes Risk Prediction Using Health and Lifestyle Indicators"
    assert "disclaimer" in body


def test_dashboard_renders_activity_metrics_and_api_sources() -> None:
    from diabetes_risk.dashboard.app import app as dashboard_app

    response = TestClient(dashboard_app).get("/")

    assert response.status_code == 200
    for expected in (
        "Latest Pipeline Run Status",
        "Pipeline Processing Duration",
        "Composer DAG Run History",
        "Errors",
        "Warnings",
        "/api/v1/workflow",
        "/api/v1/runs/latest",
        "/api/v1/dataset",
        "/api/v1/schedule",
    ):
        assert expected in response.text


def test_workflow_endpoint_returns_run_history(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import gcp_service

    runs = [{"dag_run_id": "scheduled__run", "state": "success"}]
    monkeypatch.setattr(gcp_service, "get_dag_run_history", lambda limit=10: runs)

    response = TestClient(app).get("/api/v1/workflow")

    assert response.status_code == 200
    assert response.json() == runs


def test_latest_run_endpoint_returns_execution_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import local_service

    run = {
        "run_id": "run-1",
        "status": "SUCCESS",
        "duration_seconds": 2.5,
        "records_processed": 90,
        "errors": [],
        "warnings": [],
        "started_at": "2026-09-23T09:00:00Z",
        "ended_at": "2026-09-23T09:00:02Z",
    }
    monkeypatch.setattr(local_service, "get_latest_run", lambda: run)

    response = TestClient(app).get("/api/v1/runs/latest")

    assert response.status_code == 200
    assert response.json() == run


def test_dataset_endpoint_returns_quality_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import local_service

    summary = {"input_rows": 100, "output_rows": 90, "quality_status": "PASS"}
    monkeypatch.setattr(local_service, "get_dataset_quality", lambda: summary)

    response = TestClient(app).get("/api/v1/dataset")

    assert response.status_code == 200
    assert response.json() == summary


def test_schedule_endpoint_returns_501_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without GCP_PROJECT_ID/GCP_LOCATION/GCP_COMPOSER_ENVIRONMENT set,
    get_composer_environment_details() should fail with a clear 501
    rather than a raw exception or a confusing SDK error.
    """
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GCP_LOCATION", raising=False)
    monkeypatch.delenv("GCP_COMPOSER_ENVIRONMENT", raising=False)

    response = TestClient(app).get("/api/v1/schedule")

    assert response.status_code == 501
    assert response.json()["error"] == "not_implemented"


def test_schedule_endpoint_returns_composer_details(monkeypatch: pytest.MonkeyPatch) -> None:
    """With gcp_service's Composer Environments API call mocked out (no
    real network/GCP call in the test suite), the endpoint should
    re-expose whatever get_composer_environment_details() returns.
    """
    from diabetes_risk.api import gcp_service

    fake_details = {
        "name": "diabetes-risk-env",
        "state": "RUNNING",
        "airflow_version": "composer-2.9.1-airflow-2.9.3",
        "gcs_bucket": "us-central1-diabetes-risk-e-xxxxx-bucket",
    }
    monkeypatch.setattr(gcp_service, "get_composer_environment_details", lambda config=None: fake_details)

    response = TestClient(app).get("/api/v1/schedule")

    assert response.status_code == 200
    assert response.json() == fake_details


def test_model_endpoint_returns_501_when_bucket_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without DIABETES_GCS_BUCKET set, get_model_comparison() should
    fail with a clear 501 rather than a confusing GCS client error.
    """
    monkeypatch.delenv("DIABETES_GCS_BUCKET", raising=False)

    response = TestClient(app).get("/api/v1/model")

    assert response.status_code == 501
    assert response.json()["error"] == "not_implemented"


def test_model_endpoint_returns_model_comparison(monkeypatch: pytest.MonkeyPatch) -> None:
    """With local_service's GCS read mocked out (no real network/GCP call
    in the test suite), the endpoint should re-expose whatever
    get_model_comparison() returns.
    """
    from diabetes_risk.api import local_service

    fake_comparison = {
        "logistic_regression": {"accuracy": 0.6292, "f1_score": 0.7033},
        "random_forest": {"accuracy": 0.8247, "f1_score": 0.7874},
        "top_feature": "bmi",
    }
    monkeypatch.setattr(local_service, "get_model_comparison", lambda: fake_comparison)

    response = TestClient(app).get("/api/v1/model")

    assert response.status_code == 200
    assert response.json() == fake_comparison


def test_get_model_comparison_parses_real_csv_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit test of local_service.get_model_comparison() itself, with the
    GCS read mocked to return the exact CSV content produced by the
    pipeline's own model_evaluation.csv / feature_importance.csv (see
    docs/report/REPORT.md Section 3.8), so the CSV-parsing logic is
    verified against real data shape without touching the network.
    """
    from diabetes_risk.api import local_service

    evaluation_csv = (
        "Model,Accuracy,Balanced Accuracy,Precision,Recall,F1 Score\n"
        "Logistic Regression,0.6291533389907957,0.5134734660482799,"
        "0.8368635135314382,0.6291533389907958,0.7033326853523207\n"
        "Random Forest,0.8246621842156798,0.38388004945671655,"
        "0.7741890979196636,0.8246621842156798,0.7873602658457236\n"
    )
    importance_csv = "Feature,Importance\nbmi,0.18348920369859098\nage,0.12378971011758458\n"

    def fake_read_gcs_text(bucket_name: str, object_name: str) -> str:
        if object_name.endswith("model_evaluation.csv"):
            return evaluation_csv
        if object_name.endswith("feature_importance.csv"):
            return importance_csv
        raise AssertionError(f"unexpected object read: {object_name}")

    monkeypatch.setenv("DIABETES_GCS_BUCKET", "diabetes-risk-group49-pipeline")
    monkeypatch.setattr(local_service, "_read_gcs_text", fake_read_gcs_text)

    result = local_service.get_model_comparison()

    assert result["top_feature"] == "bmi"
    assert result["random_forest"]["accuracy"] == pytest.approx(0.8246621842156798)
    assert result["logistic_regression"]["f1_score"] == pytest.approx(0.7033326853523207)


def test_get_dataset_quality_merges_gcs_reports(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import local_service

    objects = {
        "data/outputs/quality/data_quality.json": {
            "rows": 253680,
            "columns": 22,
            "schema": {"missing_columns": []},
        },
        "data/processed/preprocessing_report.json": {
            "input_rows": 253680,
            "output_rows": 229781,
            "duplicates_removed": 23899,
            "missing_values_after": {"Diabetes_012": 0, "BMI": 0},
            "target_column": "Diabetes_012",
        },
    }
    monkeypatch.setenv("DIABETES_GCS_BUCKET", "test-bucket")
    monkeypatch.setattr(local_service, "_read_gcs_json", lambda bucket, name: objects[name])

    result = local_service.get_dataset_quality()

    assert result == {
        "input_rows": 253680,
        "output_rows": 229781,
        "input_columns": 22,
        "duplicate_records_removed": 23899,
        "missing_values_after": 0,
        "quality_status": "PASS",
        "target_column": "Diabetes_012",
    }


def test_get_latest_run_reads_execution_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import local_service

    manifest = {"run_id": "20260911T074519440443Z", "status": "SUCCESS"}
    monkeypatch.setenv("DIABETES_GCS_BUCKET", "test-bucket")
    monkeypatch.setattr(local_service, "_read_gcs_json", lambda bucket, name: manifest)

    assert local_service.get_latest_run() == manifest


def test_get_dag_run_history_maps_airflow_response(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import gcp_service
    from diabetes_risk.api.gcp_config import GCPConfig

    calls = []

    def fake_get(config, path, params=None):
        calls.append((path, params))
        return {"dag_runs": [{"dag_run_id": "scheduled__run", "state": "success", "start_date": "start"}]}

    monkeypatch.setattr(gcp_service, "_airflow_api_get", fake_get)
    config = GCPConfig("project", "region", "composer", None)

    result = gcp_service.get_dag_run_history(dag_id="risk/pipeline", limit=3, config=config)

    assert calls == [("dags/risk%2Fpipeline/dagRuns", {"limit": 3, "order_by": "-execution_date"})]
    assert result == [{"dag_run_id": "scheduled__run", "state": "success", "start_date": "start", "end_date": None}]


def test_get_task_instance_status_maps_airflow_response(monkeypatch: pytest.MonkeyPatch) -> None:
    from diabetes_risk.api import gcp_service
    from diabetes_risk.api.gcp_config import GCPConfig

    calls = []

    def fake_get(config, path, params=None):
        calls.append(path)
        return {"task_instances": [{"task_id": "preprocess", "state": "success", "duration": 1.25}]}

    monkeypatch.setattr(gcp_service, "_airflow_api_get", fake_get)
    config = GCPConfig("project", "region", "composer", None)

    result = gcp_service.get_task_instance_status("risk/pipeline", "scheduled__run", config)

    assert calls == ["dags/risk%2Fpipeline/dagRuns/scheduled__run/taskInstances"]
    assert result == [{"task_id": "preprocess", "state": "success", "duration": 1.25, "start_date": None, "end_date": None}]
