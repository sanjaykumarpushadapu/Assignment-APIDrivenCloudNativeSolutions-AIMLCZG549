import pytest
from fastapi.testclient import TestClient

from diabetes_support.infrastructure.seq2seq_knowledge_answerer import (
    Seq2SeqKnowledgeAnswerer,
)
from diabetes_support.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("route", "field"),
    [("/analyze", "message"), ("/chat", "question"), ("/retrieve", "question")],
)
def test_whitespace_only_inputs_are_validation_errors(route: str, field: str) -> None:
    response = client.post(route, json={field: "   "})

    assert response.status_code == 422


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
        if "Create a concise, factual staff handoff summary" in prompt:
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


@pytest.mark.parametrize(
    "question",
    [
        "I missed my diabetes medicine yesterday. Should I take an extra dose now?",
        "I forgot my diabetes tablets last night. Should I double the next dose?",
        "My evening diabetes dose was missed; should I take two tablets this morning?",
        "My latest glucose result is 290. Do I need to change what I do?",
        "Can I take my diabetes prescription together with my new medicine?",
        "Does the diabetes team provide remote education sessions?",
        "Can you take my diabetes tablets together with this new prescription?",
        "My glucose number is 305; should I alter my routine?",
        "Does my blood work prove I have diabetes?",
        "Do these blood test results mean that I have diabetes?",
        "Can you tell from my lab numbers whether I have diabetes?",
        "My glucose reading is 280. What should I do right now?",
        "Can I attend my diabetes education group by video instead of in person?",
        "Can you move my diabetes education appointment to Friday afternoon?",
        "Can you tell me whether this insulin is safe with my other medicines?",
        "What should I do about a severe low blood sugar episode?",
        "Where can I download the clinic education leaflet?",
        "The clinic portal will not let me sign in.",
        "How much insulin should my father inject tonight?",
        "Can she stop her diabetes tablets?",
    ],
)
def test_personal_care_and_clinic_process_questions_route_to_staff(
    question: str,
) -> None:
    """Avoid generating advice or workflow instructions outside corpus scope."""
    assert Seq2SeqKnowledgeAnswerer._requires_clinician(question) is True


@pytest.mark.parametrize(
    "question",
    [
        "What is diabetes?",
        "What symptoms might someone with diabetes experience?",
        "How can type 2 diabetes be prevented or delayed?",
    ],
)
def test_general_corpus_questions_are_not_routed_to_staff_by_keyword_rules(
    question: str,
) -> None:
    """Keep supported general education questions eligible for grounded chat."""
    assert Seq2SeqKnowledgeAnswerer._requires_clinician(question) is False


@pytest.mark.parametrize(
    "question",
    [
        "What should I do about a severe low blood sugar episode?",
        "Someone with diabetes is unconscious and cannot wake up.",
        "They are having a seizure and have diabetes.",
    ],
)
def test_emergency_wording_uses_urgent_care_path(question: str) -> None:
    """Return urgent-care wording without generating from unrelated sources."""
    answerer = object.__new__(Seq2SeqKnowledgeAnswerer)
    result = answerer.answer(question)

    assert result["abstained"] is True
    assert result["sources"] == []
    assert "urgent medical attention" in result["answer"]


@pytest.mark.parametrize(
    "question",
    [
        "I am not unconscious. What is diabetes?",
        "What are symptoms of a seizure?",
        "I do not have severe hypoglycemia. What is a normal symptom?",
    ],
)
def test_negated_or_general_emergency_terms_do_not_trigger_urgent_path(
    question: str,
) -> None:
    assert Seq2SeqKnowledgeAnswerer._requires_urgent_care(question) is False
