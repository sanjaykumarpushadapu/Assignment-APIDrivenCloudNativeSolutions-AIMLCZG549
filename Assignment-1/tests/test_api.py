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
        "/api/v1/schedule",
        "/api/v1/model",
    ],
)
def test_skeleton_endpoints_return_clean_501(path: str) -> None:
    """The GCP/local service-layer functions are still skeletons
    (NotImplementedError). Until they're implemented, every endpoint that
    delegates to one should fail with a clean, documented 501 -- not a
    raw 500 -- so this is real, useful HTTP-status-code evidence
    (assessment activity 3.3) even before gcp_service.py is filled in.
    """
    response = TestClient(app).get(path)

    assert response.status_code == 501
    body = response.json()
    assert body["error"] == "not_implemented"
    assert "TODO" in body["detail"]
