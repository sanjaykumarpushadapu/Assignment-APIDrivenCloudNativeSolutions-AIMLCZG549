"""Sequence-to-sequence implementation of the Summarizer interface."""

from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime


def build_summary_prompt(message: str) -> str:
    """Build the same prompt for inference and summarizer training."""
    return (
        "Create a concise, factual staff handoff summary of this clinic support "
        "message. Include every separate request, even when requests concern "
        "different topics. Preserve dates, times, conditions, exclusions, and "
        "negative instructions that affect what staff should do. Keep clear what "
        "is confirmed, uncertain, pending, or being asked; do not turn a question "
        "into a statement or infer an outcome. Preserve reported symptoms and "
        "requests for clinical follow-up without answering medical questions. "
        "Do not add facts, diagnoses, or medical advice.\n"
        f"Message: {message}\nSummary:"
    )


class Seq2SeqSummarizer:
    """Create a concise staff handoff summary using the configured shared model."""

    def __init__(
        self,
        settings: ModelSettings,
        *,
        runtime: Seq2SeqRuntime,
    ) -> None:
        self.settings = settings
        self.runtime = runtime

    @property
    def status(self) -> ComponentStatus:
        return self.runtime.status

    def summarize(self, message: str, /) -> str:
        message = message.strip()
        if not message:
            raise ValueError("The message must not be empty.")

        prompt = build_summary_prompt(message)
        # Compare candidate sequences and discourage repeated phrases for summaries.
        # Other tasks keep the runtime's default decoding settings.
        generated_summary = self.runtime.generate(
            prompt,
            max_new_tokens=self.settings.summary_max_new_tokens,
            num_beams=4,
            no_repeat_ngram_size=3,
        ).strip()
        # A blank generation falls back to the source, rather than an empty handoff.
        # Never append source sentences to a paraphrase: this creates duplication.
        return generated_summary or message
