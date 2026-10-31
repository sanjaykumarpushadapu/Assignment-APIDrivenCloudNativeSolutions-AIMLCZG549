"""Sequence-to-sequence implementation of the Summarizer interface."""

import re

from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "please",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def _content_words(text: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", text.casefold()))
    return words - _STOP_WORDS


def _append_uncovered_sentences(message: str, summary: str) -> str:
    """Keep source sentences when the generated summary drops their details."""
    summary_words = _content_words(summary)
    sentences = re.split(r"(?<=[.!?])\s+", message.strip())
    missing = [
        sentence
        for sentence in sentences
        if (words := _content_words(sentence)) and not words.issubset(summary_words)
    ]
    if not missing:
        return summary

    # Prefer a little repetition to silently losing part of the user's message.
    return " ".join(part for part in (summary, *missing) if part)


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

        prompt = (
            "Create a concise staff handoff summary of this clinic support "
            "message. List every separate request, including requests about "
            "different topics. Keep stated dates and details. Do not add facts, "
            "diagnoses, or medical advice.\n"
            f"Message: {message}\nSummary:"
        )
        generated_summary = self.runtime.generate(
            prompt, max_new_tokens=self.settings.summary_max_new_tokens
        )
        return _append_uncovered_sentences(message, generated_summary)
