"""Generate source-grounded answers with staff-referral safeguards."""

import re

from diabetes_support.application.ports import KnowledgeRetriever
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime

_PERSONAL_CARE_PATTERNS = (
    re.compile(
        r"\b(?:should|can|could|may)\s+i\s+"
        r"(?:change|adjust|increase|decrease|stop(?:\s+taking)?|start|take)\s+"
        r"(?:my\s+)?(?:diabetes\s+)?"
        r"(?:medication|meds?|medicine|dose|insulin|treatment)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bhow\s+do\s+i\s+(?:change|adjust|stop(?:\s+taking)?|start|take)\s+"
        r"(?:my\s+)?(?:diabetes\s+)?"
        r"(?:medication|meds?|medicine|dose|insulin|treatment)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bdo\s+i\s+have\s+(?:diabetes|a\s+diagnosis)\b", re.I),
    re.compile(
        r"\bmy\s+(?:medication|meds?|medicine|dose|insulin|treatment|diagnosis|"
        r"blood\s+sugar|blood\s+glucose|symptoms?)\b",
        re.IGNORECASE,
    ),
)
_CITATION_ONLY_PATTERN = re.compile(r"(?:\[[A-Z0-9]+-\d+\]\s*)+")
_ABSTAIN_TEXT = (
    "I can’t answer this safely from the available information. "
    "Please contact your clinic team for guidance."
)


class Seq2SeqKnowledgeAnswerer:
    """Answer from retrieved WHO passages using the shared base-model runtime."""

    def __init__(
        self,
        settings: ModelSettings,
        *,
        runtime: Seq2SeqRuntime,
        retriever: KnowledgeRetriever,
        minimum_retrieval_score: float,
    ) -> None:
        """Reuse the configured base model and the existing local retriever."""
        self._settings = settings
        self._runtime = runtime
        self._retriever = retriever
        self._minimum_retrieval_score = minimum_retrieval_score

    @property
    def status(self) -> ComponentStatus:
        """Report ready when both retrieval and the answer model are loaded."""
        return ComponentStatus(
            ready=self._retriever.status.ready and self._runtime.status.ready,
            version=self._runtime.status.version,
        )

    def answer(self, question: str, /) -> dict[str, object]:
        """Return a cited answer or a staff-referral response when unsupported."""
        question = question.strip()
        if not question:
            raise ValueError("The question must not be empty.")
        if self._requires_clinician(question):
            return self._abstain()

        sources = self._retriever.retrieve(question)
        if not sources:
            return self._abstain()
        # Avoid generating an answer from passages with weak semantic matches.
        top_score = max(float(source["score"]) for source in sources)
        if top_score < self._minimum_retrieval_score:
            return self._abstain()

        prompt = self._build_prompt(question, sources)
        generated = self._runtime.generate(
            prompt, max_new_tokens=self._settings.answer_max_new_tokens
        )
        generated = generated.strip()
        if (
            not generated
            or generated.upper().startswith("ABSTAIN")
            or _CITATION_ONLY_PATTERN.fullmatch(generated)
        ):
            return self._abstain()

        return {
            "answer": generated,
            "abstained": False,
            # The API returns retrieved records as citations; the model need not
            # reproduce chunk IDs accurately in generated prose.
            "sources": sources,
        }

    @staticmethod
    def _requires_clinician(question: str) -> bool:
        """Route common personal diagnosis and treatment requests to clinic staff."""
        return any(pattern.search(question) for pattern in _PERSONAL_CARE_PATTERNS)

    @staticmethod
    def _build_prompt(question: str, sources: list[dict[str, object]]) -> str:
        """Tell the model to answer only from the supplied source passages."""
        context = "\n".join(
            f"[{source['chunk_id']}] {source['section']}: {source['text']}"
            for source in sources
        )
        return (
            "Answer the question using only the source passages below. "
            "Do not add medical advice, diagnoses, or facts from memory. "
            "If the passages do not answer the question, output only ABSTAIN. "
            "Otherwise, answer briefly using facts stated in the passages.\n\n"
            f"Question: {question}\n"
            f"Passages:\n{context}\n"
            "Answer:"
        )

    @staticmethod
    def _abstain() -> dict[str, object]:
        """Return a fixed staff-referral message without misleading citations."""
        return {"answer": _ABSTAIN_TEXT, "abstained": True, "sources": []}
