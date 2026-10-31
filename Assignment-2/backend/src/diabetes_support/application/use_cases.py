from diabetes_support.application.ports import (
    Classifier,
    KnowledgeAnswerer,
    KnowledgeRetriever,
    Summarizer,
)
from diabetes_support.domain.status import ServiceStatus


class AnalyzeSupportRequest:
    def __init__(self, classifier: Classifier, summarizer: Summarizer) -> None:
        self._classifier = classifier
        self._summarizer = summarizer

    def execute(self, message: str) -> dict[str, object]:
        # Produce the summary first so its unconfigured placeholder fails before
        # we spend time loading/running the classifier for an incomplete response.
        summary = self._summarizer.summarize(message)
        return {
            "classification": self._classifier.classify(message),
            "summary": summary,
        }


class AnswerQuestion:
    def __init__(self, knowledge_answerer: KnowledgeAnswerer) -> None:
        self._knowledge_answerer = knowledge_answerer

    def execute(self, question: str) -> dict[str, object]:
        return self._knowledge_answerer.answer(question)


class RetrieveKnowledge:
    def __init__(self, knowledge_retriever: KnowledgeRetriever) -> None:
        self._knowledge_retriever = knowledge_retriever

    def execute(self, question: str) -> dict[str, object]:
        return {
            "question": question,
            "sources": self._knowledge_retriever.retrieve(question),
        }


class GetServiceStatus:
    def __init__(
        self,
        classifier: Classifier,
        summarizer: Summarizer,
        knowledge_retriever: KnowledgeRetriever,
    ) -> None:
        self._classifier = classifier
        self._summarizer = summarizer
        self._knowledge_retriever = knowledge_retriever

    def execute(self) -> ServiceStatus:
        return ServiceStatus(
            classifier=self._classifier.status,
            summarizer=self._summarizer.status,
            knowledge_index=self._knowledge_retriever.status,
        )
