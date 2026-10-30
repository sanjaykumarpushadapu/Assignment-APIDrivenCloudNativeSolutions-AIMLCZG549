from diabetes_support.domain.errors import ComponentNotConfiguredError
from diabetes_support.domain.status import ComponentStatus


class UnconfiguredClassifier:
    @property
    def status(self) -> ComponentStatus:
        return ComponentStatus(ready=False)

    def classify(self, _message: str) -> dict[str, object]:
        raise ComponentNotConfiguredError(
            "The fine-tuned classifier has not been configured."
        )


class UnconfiguredSummarizer:
    @property
    def status(self) -> ComponentStatus:
        return ComponentStatus(ready=False)

    def summarize(self, _message: str) -> str:
        raise ComponentNotConfiguredError(
            "The summarization model has not been configured."
        )


class UnconfiguredKnowledgeAnswerer:
    @property
    def status(self) -> ComponentStatus:
        return ComponentStatus(ready=False)

    def answer(self, _question: str) -> dict[str, object]:
        raise ComponentNotConfiguredError(
            "The knowledge index and answer model have not been configured."
        )
