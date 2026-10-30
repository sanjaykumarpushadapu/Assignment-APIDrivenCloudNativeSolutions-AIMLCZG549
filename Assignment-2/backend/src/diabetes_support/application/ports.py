from typing import Protocol

from diabetes_support.domain.status import ComponentStatus


class Classifier(Protocol):
    @property
    def status(self) -> ComponentStatus: ...

    def classify(self, message: str, /) -> dict[str, object]: ...


class Summarizer(Protocol):
    @property
    def status(self) -> ComponentStatus: ...

    def summarize(self, message: str, /) -> str: ...


class KnowledgeAnswerer(Protocol):
    @property
    def status(self) -> ComponentStatus: ...

    def answer(self, question: str, /) -> dict[str, object]: ...
