from fastapi import FastAPI

from diabetes_support.application.use_cases import (
    AnalyzeSupportRequest,
    AnswerQuestion,
    GetServiceStatus,
)
from diabetes_support.infrastructure.flan_t5_classifier import FlanT5Classifier
from diabetes_support.infrastructure.unconfigured_components import (
    UnconfiguredKnowledgeAnswerer,
    UnconfiguredSummarizer,
)
from diabetes_support.presentation.api import create_api_app


def create_application() -> FastAPI:
    # The adapter loads its model on first use, then reuses it for later requests.
    classifier = FlanT5Classifier()
    summarizer = UnconfiguredSummarizer()
    knowledge_answerer = UnconfiguredKnowledgeAnswerer()

    return create_api_app(
        analyze_support_request=AnalyzeSupportRequest(classifier, summarizer),
        answer_question=AnswerQuestion(knowledge_answerer),
        get_service_status=GetServiceStatus(
            classifier,
            summarizer,
            knowledge_answerer,
        ),
    )


app = create_application()
