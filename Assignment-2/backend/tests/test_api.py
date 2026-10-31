from fastapi.testclient import TestClient

from diabetes_support.main import app

client = TestClient(app)


def test_health_reports_running_service() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metadata_marks_unloaded_components_not_ready() -> None:
    response = client.get("/metadata")

    assert response.status_code == 200
    assert response.json() == {
        "classifier": {"ready": False, "version": None},
        "summarizer": {"ready": False, "version": None},
        "knowledge_index": {"ready": False, "version": None},
    }


def test_analysis_reports_missing_summarizer_configuration() -> None:
    response = client.post(
        "/analyze",
        json={"message": "Please move my education appointment."},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The summarization model has not been configured."
    )


def test_chat_reports_missing_knowledge_configuration() -> None:
    response = client.post(
        "/chat",
        json={"question": "Where can I find the clinic leaflet?"},
    )

    assert response.status_code == 503
    assert "not been configured" in response.json()["detail"]
