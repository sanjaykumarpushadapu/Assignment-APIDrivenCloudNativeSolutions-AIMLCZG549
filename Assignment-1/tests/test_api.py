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


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/workflow",
        "/api/v1/runs/latest",
        "/api/v1/dataset",
    ],
)
def test_skeleton_endpoints_return_clean_501(path: str) -> None:
    """The remaining GCP/local service-layer functions are still
    skeletons (NotImplementedError) -- see gcp_service.py/local_service.py
    for which ones. Until they're implemented, every endpoint that
    delegates to one should fail with a clean, documented 501 -- not a
    raw 500 -- so this is real, useful HTTP-status-code evidence
    (assessment activity 3.3) even before those functions are filled in.
    ("/api/v1/schedule" and "/api/v1/model" are covered separately below,
    now that gcp_service.get_composer_environment_details() and
    local_service.get_model_comparison() are implemented for real.)
    """
    response = TestClient(app).get(path)

    assert response.status_code == 501
    body = response.json()
    assert body["error"] == "not_implemented"
    assert "TODO" in body["detail"]


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
