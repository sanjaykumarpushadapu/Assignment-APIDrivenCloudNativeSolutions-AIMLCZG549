from fastapi import FastAPI

from diabetes_support.application.use_cases import (
    AnalyzeSupportRequest,
    AnswerQuestion,
    GetServiceStatus,
    RetrieveKnowledge,
)
from diabetes_support.infrastructure.knowledge_retriever import (
    RetrievalSettings,
    TransformerKnowledgeRetriever,
)
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_classifier import Seq2SeqClassifier
from diabetes_support.infrastructure.seq2seq_knowledge_answerer import (
    Seq2SeqKnowledgeAnswerer,
)
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime
from diabetes_support.infrastructure.seq2seq_summarizer import Seq2SeqSummarizer
from diabetes_support.presentation.api import create_api_app


def create_application() -> FastAPI:
    """Build the API with a tuned classifier and a shared base-model runtime."""
    # Keep the tuned classifier separate; summaries and answers share the base model.
    classifier_settings = ModelSettings.from_env(component="classifier")
    summarizer_settings = ModelSettings.from_env(component="summarizer")
    classifier = Seq2SeqClassifier(
        classifier_settings, runtime=Seq2SeqRuntime(classifier_settings)
    )
    base_runtime = Seq2SeqRuntime(summarizer_settings)
    summarizer = Seq2SeqSummarizer(summarizer_settings, runtime=base_runtime)
    retrieval_settings = RetrievalSettings.from_env()
    knowledge_retriever = TransformerKnowledgeRetriever(retrieval_settings)
    knowledge_answerer = Seq2SeqKnowledgeAnswerer(
        summarizer_settings,
        runtime=base_runtime,
        retriever=knowledge_retriever,
        minimum_retrieval_score=retrieval_settings.min_score,
    )

    return create_api_app(
        analyze_support_request=AnalyzeSupportRequest(classifier, summarizer),
        answer_question=AnswerQuestion(knowledge_answerer),
        retrieve_knowledge=RetrieveKnowledge(knowledge_retriever),
        get_service_status=GetServiceStatus(
            classifier,
            summarizer,
            knowledge_retriever,
        ),
    )


app = create_application()
