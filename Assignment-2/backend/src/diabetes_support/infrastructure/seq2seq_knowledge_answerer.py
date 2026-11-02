"""Generate source-grounded answers with staff-referral safeguards."""

import re

from diabetes_support.application.ports import KnowledgeRetriever
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime

# These requests need a clinician because general WHO passages cannot safely
# determine an individual's dose, reading, diagnosis, or urgent symptoms.
_PERSONAL_CARE_PATTERNS = (
    re.compile(
        r"\b(?:should|can|could|may)\s+i\b.{0,45}"
        r"\b(?:change|adjust|increase|decrease|stop|start|take|skip|miss)\b"
        r".{0,45}\b(?:medication|meds?|medicine|dose|insulin|treatment|pill)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bhow\s+do\s+i\b.{0,45}\b(?:change|adjust|increase|decrease|"
        r"stop|start|take|skip)\b.{0,45}"
        r"\b(?:medication|meds?|medicine|dose|insulin|treatment|pill)\b",
        re.IGNORECASE,
    ),
    # Include common individual-dose wording that the corpus cannot answer.
    re.compile(
        r"\b(?:missed|forgot|miss)\s+(?:my\s+)?(?:diabetes\s+)?"
        r"(?:medication|meds?|medicine|dose|insulin|pill|tablets?)\b|"
        r"\b(?:my\s+)?(?:morning|evening|next\s+)?diabetes\s+"
        r"(?:medication|medicine|dose|tablet|pill)s?\s+(?:was|were)\s+missed\b|"
        r"\b(?:double|repeat|skip|hold)\s+(?:my\s+)?(?:next\s+)?"
        r"(?:dose|tablet|pill|medication|medicine)\b",
        re.IGNORECASE,
    ),
    # Catch missed-dose questions even when the event is described passively.
    re.compile(
        r"\b(?:missed|forgot|miss)\b.{0,70}\b"
        r"(?:diabetes|medication|medicine|tablets?|pills?|dose)\b",
        re.IGNORECASE,
    ),
    # Catch questions that ask a model to interpret a personal glucose value.
    re.compile(
        r"\b(?:glucose|blood\s+sugar|blood\s+glucose)\s+"
        r"(?:number|result|reading)\s+(?:is\s+)?\d{2,3}\b",
        re.IGNORECASE,
    ),
    # Detect diagnosis requests phrased around test or laboratory results.
    re.compile(
        r"\b(?:whether|if)\s+i\s+have\s+diabetes\b|"
        r"\b(?:do|mean)\s+(?:these\s+)?(?:blood\s+)?test\s+"
        r"results?\b.{0,60}\bdiabetes\b|"
        r"\b(?:based\s+on|from)\s+my\s+(?:lab|laboratory|test)\s+"
        r"(?:results?|numbers?)\b.{0,60}\bdiabetes\b|"
        r"\bmy\s+blood\s+work\b.{0,80}\bdiabetes\b|"
        r"\bblood\s+work\b.{0,80}\b(?:prove|mean|show)\b.{0,40}\bdiabetes\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:is\s+it\s+safe|safe|interact(?:s|ing)?)\b.{0,70}"
        r"\b(?:with\s+(?:my\s+)?(?:other\s+)?(?:medications?|meds?|"
        r"medicines?|insulin)|medication|meds?|medicine|insulin)\b|"
        r"\b(?:can|may|should)\s+i\s+take\b.{0,70}"
        r"\bwith\s+(?:my\s+)?(?:other\s+)?(?:medications?|meds?|medicines?)\b|"
        r"\b(?:take|combine|use)\b.{0,100}\b(?:together\s+with|with)\b"
        r".{0,60}\b(?:prescription|medicine|medication|drug|tablet|pill)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bdo\s+i\s+have\s+(?:diabetes|a\s+diagnosis)\b", re.I),
    re.compile(
        r"\bmy\s+(?:medication|meds?|medicine|dose|insulin|treatment|diagnosis|"
        r"blood\s+sugar|blood\s+glucose|glucose\s+reading|symptoms?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:my\s+)?(?:blood\s+sugar|blood\s+glucose|glucose)\s+"
        r"(?:reading\s+)?(?:is\s+)?\d{2,3}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:severe|very\s+low|very\s+high|dangerously\s+low|"
        r"dangerously\s+high)\b.{0,35}\b(?:blood\s+sugar|blood\s+glucose|"
        r"glucose|hypoglyc?emia|hyperglyc?emia)\b|"
        r"\b(?:hypoglyc?emia|hyperglyc?emia)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:faint(?:ed|ing)?|unconscious|confused|seizure|cannot\s+wake)\b"
        r".{0,55}\b(?:diabetes|blood\s+sugar|glucose|insulin)\b|"
        r"\b(?:diabetes|blood\s+sugar|glucose|insulin)\b.{0,55}"
        r"\b(?:faint(?:ed|ing)?|unconscious|confused|seizure|cannot\s+wake)\b",
        re.IGNORECASE,
    ),
)
# The corpus has no clinic-specific booking, portal, leaflet, or session details.
_CLINIC_PROCESS_PATTERNS = (
    re.compile(
        r"\b(?:clinic|appointment|booking|booked\s+visit)\b.{0,70}"
        r"\b(?:move|reschedule|cancel|confirm|available\s+slot|change)\b|"
        r"\b(?:move|reschedule|cancel|confirm|change)\b.{0,70}"
        r"\b(?:clinic|appointment|booking|booked\s+visit)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:clinic|education|preparation)\s+(?:leaflet|handout|brochure)\b|"
        r"\b(?:download|get|find|access)\b.{0,45}"
        r"\b(?:clinic|education|preparation)\s+(?:leaflet|handout|brochure)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:clinic|patient)\s+portal\b|\bportal\b.{0,45}"
        r"\b(?:sign\s*in|log\s*in|download|upload|password|not\s+working)\b|"
        r"\b(?:sign\s*in|log\s*in|download|upload|password)\b.{0,45}\bportal\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:clinic|diabetes\s+education|diabetes\s+team)\b.{0,60}"
        r"\b(?:video|remote|online|group|class|session|link|join)\b|"
        r"\b(?:video|remote|online|group|class|session)\b.{0,60}"
        r"\b(?:clinic|diabetes\s+education|diabetes\s+team)\b|"
        r"\b(?:my\s+)?(?:blood\s+)?glucose\s+(?:result|reading)\s+"
        r"(?:number\s+)?(?:is\s+)?\d{2,3}\b",
        re.IGNORECASE,
    ),
)
_CITATION_ONLY_PATTERN = re.compile(r"(?:\[[A-Z0-9]+-\d+\]\s*)+")
_URGENT_REFERRAL_TEXT = (
    "This may need urgent medical attention. Contact local emergency services "
    "or follow your clinic’s urgent-care instructions now."
)
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
        if self._requires_urgent_care(question):
            return self._abstain(_URGENT_REFERRAL_TEXT)
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
        """Route personal-care and clinic-process questions to staff."""
        return any(
            pattern.search(question)
            for pattern in (*_PERSONAL_CARE_PATTERNS, *_CLINIC_PROCESS_PATTERNS)
        )

    @staticmethod
    def _requires_urgent_care(question: str) -> bool:
        """Use an urgent-care response for severe or immediately dangerous signs."""
        return bool(
            re.search(
                r"\b(?:severe|dangerously\s+low|dangerously\s+high)\b.{0,40}"
                r"\b(?:blood\s+sugar|blood\s+glucose|glucose|hypoglyc?emia|"
                r"hyperglyc?emia)\b|"
                r"\b(?:faint(?:ed|ing)?|unconscious|seizure|cannot\s+wake)\b|"
                r"\bsevere\s+hypoglyc?emia\b",
                question,
                re.IGNORECASE,
            )
        )

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
    def _abstain(message: str = _ABSTAIN_TEXT) -> dict[str, object]:
        """Return a fixed referral response without misleading citations."""
        return {"answer": message, "abstained": True, "sources": []}
