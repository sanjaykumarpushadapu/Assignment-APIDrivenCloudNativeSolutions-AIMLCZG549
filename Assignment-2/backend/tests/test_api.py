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


def test_analysis_returns_summary_and_category(monkeypatch) -> None:
    from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime

    def fake_generate(self, prompt: str, *, max_new_tokens: int) -> str:
        if "Create a concise staff handoff summary" in prompt:
            return "Patient wants an appointment change and help with the leaflet."
        return "appointment_support"

    monkeypatch.setattr(Seq2SeqRuntime, "generate", fake_generate)
    response = client.post(
        "/analyze",
        json={
            "message": "Please move my appointment to Friday. I also cannot download "
            "the education leaflet from the portal."
        },
    )

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary.startswith("Patient wants an appointment change")
    assert "Please move my appointment to Friday." in summary
    assert "I also cannot download the education leaflet from the portal." in summary
    assert response.json()["classification"]["category"] == "appointment_support"


def test_chat_reports_missing_knowledge_configuration() -> None:
    response = client.post(
        "/chat",
        json={"question": "Where can I find the clinic leaflet?"},
    )

    assert response.status_code == 503
    assert "not been configured" in response.json()["detail"]
