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
    """Build the API with separately configured model runtimes per task."""
    # Each task has its own lazy runtime so either can use a different checkpoint.
    classifier_settings = ModelSettings.from_env(component="classifier")
    summarizer_settings = ModelSettings.from_env(component="summarizer")
    classifier = Seq2SeqClassifier(
        classifier_settings, runtime=Seq2SeqRuntime(classifier_settings)
    )
    summarizer = Seq2SeqSummarizer(
        summarizer_settings, runtime=Seq2SeqRuntime(summarizer_settings)
    )
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
