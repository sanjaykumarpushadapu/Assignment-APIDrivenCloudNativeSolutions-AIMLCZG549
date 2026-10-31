from fastapi import FastAPI

from diabetes_support.application.use_cases import (
    AnalyzeSupportRequest,
    AnswerQuestion,
    GetServiceStatus,
)
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_classifier import Seq2SeqClassifier
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime
from diabetes_support.infrastructure.seq2seq_summarizer import Seq2SeqSummarizer
from diabetes_support.infrastructure.unconfigured_components import (
    UnconfiguredKnowledgeAnswerer,
)
from diabetes_support.presentation.api import create_api_app


def create_application() -> FastAPI:
    # Both tasks share one lazy model and tokenizer in this API process.
    settings = ModelSettings.from_env()
    runtime = Seq2SeqRuntime(settings)
    classifier = Seq2SeqClassifier(settings, runtime=runtime)
    summarizer = Seq2SeqSummarizer(settings, runtime=runtime)
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
