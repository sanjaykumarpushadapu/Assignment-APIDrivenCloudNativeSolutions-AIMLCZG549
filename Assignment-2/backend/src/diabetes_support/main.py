from fastapi import FastAPI

from diabetes_support.application.use_cases import (
    AnalyzeSupportRequest,
    AnswerQuestion,
    GetServiceStatus,
)
from diabetes_support.infrastructure.unconfigured_components import (
    UnconfiguredClassifier,
    UnconfiguredKnowledgeAnswerer,
    UnconfiguredSummarizer,
)
from diabetes_support.presentation.api import create_api_app


def create_application() -> FastAPI:
    classifier = UnconfiguredClassifier()
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
