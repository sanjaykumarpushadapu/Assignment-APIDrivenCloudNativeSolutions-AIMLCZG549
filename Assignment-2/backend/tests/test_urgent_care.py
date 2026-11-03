import pytest

from diabetes_support.infrastructure.seq2seq_knowledge_answerer import (
    Seq2SeqKnowledgeAnswerer,
)


@pytest.mark.parametrize(
    "question",
    [
        "My father is unconscious, what is the next step?",
        "My father is unconscious. What is the next step?",
        "What is diabetes and my father is unconscious?",
        "A person is not unconscious, but my father is unconscious.",
        "Someone with diabetes is unconscious and cannot wake up.",
        "They are having a seizure and have diabetes.",
    ],
)
def test_urgent_event_is_not_hidden_by_unrelated_explanatory_text(
    question: str,
) -> None:
    answerer = object.__new__(Seq2SeqKnowledgeAnswerer)

    result = answerer.answer(question)

    assert result["abstained"] is True
    assert "urgent medical attention" in result["answer"]


@pytest.mark.parametrize(
    "question",
    [
        "What is severe hypoglycemia?",
        "What are symptoms of a seizure?",
        "I am not unconscious. What is diabetes?",
        "I do not have severe hypoglycemia. What is a normal symptom?",
    ],
)
def test_general_or_negated_emergency_terms_do_not_trigger_urgent_path(
    question: str,
) -> None:
    assert Seq2SeqKnowledgeAnswerer._requires_urgent_care(question) is False