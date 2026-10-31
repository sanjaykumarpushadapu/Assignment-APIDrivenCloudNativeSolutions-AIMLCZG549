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

    def fake_generate(
        self, prompt: str, *, max_new_tokens: int, **_decoding: int
    ) -> str:
        if "Create a concise staff handoff summary" in prompt:
            return (
                "Patient requests an appointment change to Friday and help "
                "downloading the leaflet from the portal."
            )
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
    assert summary == (
        "Patient requests an appointment change to Friday and help downloading "
        "the leaflet from the portal."
    )
    assert response.json()["classification"]["category"] == "appointment_support"


def test_chat_abstains_for_personal_medication_advice() -> None:
    response = client.post(
        "/chat",
        json={"question": "Should I change my diabetes medication?"},
    )

    assert response.status_code == 200
    assert response.json()["abstained"] is True
    assert response.json()["sources"] == []
    assert "contact your clinic team" in response.json()["answer"]
