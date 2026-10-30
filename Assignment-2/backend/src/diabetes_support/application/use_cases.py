from diabetes_support.application.ports import Classifier, KnowledgeAnswerer, Summarizer
from diabetes_support.domain.status import ServiceStatus


class AnalyzeSupportRequest:
    def __init__(self, classifier: Classifier, summarizer: Summarizer) -> None:
        self._classifier = classifier
        self._summarizer = summarizer

    def execute(self, message: str) -> dict[str, object]:
        return {
            "classification": self._classifier.classify(message),
            "summary": self._summarizer.summarize(message),
        }


class AnswerQuestion:
    def __init__(self, knowledge_answerer: KnowledgeAnswerer) -> None:
        self._knowledge_answerer = knowledge_answerer

    def execute(self, question: str) -> dict[str, object]:
        return self._knowledge_answerer.answer(question)


class GetServiceStatus:
    def __init__(
        self,
        classifier: Classifier,
        summarizer: Summarizer,
        knowledge_answerer: KnowledgeAnswerer,
    ) -> None:
        self._classifier = classifier
        self._summarizer = summarizer
        self._knowledge_answerer = knowledge_answerer

    def execute(self) -> ServiceStatus:
        return ServiceStatus(
            classifier=self._classifier.status,
            summarizer=self._summarizer.status,
            knowledge_index=self._knowledge_answerer.status,
        )
