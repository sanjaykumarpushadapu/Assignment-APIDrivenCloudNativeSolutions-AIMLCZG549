from fastapi import FastAPI, HTTPException

from diabetes_support.application.use_cases import (
    AnalyzeSupportRequest,
    AnswerQuestion,
    GetServiceStatus,
    RetrieveKnowledge,
)
from diabetes_support.domain.errors import ComponentNotConfiguredError
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.presentation.schemas import (
    ChatRequest,
    ComponentMetadata,
    RetrievalResponse,
    ServiceMetadata,
    SupportMessageRequest,
)


def _component_metadata(status: ComponentStatus) -> ComponentMetadata:
    return ComponentMetadata(ready=status.ready, version=status.version)


def create_api_app(
    analyze_support_request: AnalyzeSupportRequest,
    answer_question: AnswerQuestion,
    retrieve_knowledge: RetrieveKnowledge,
    get_service_status: GetServiceStatus,
) -> FastAPI:
    app = FastAPI(
        title="Diabetes Care Support Assistant API",
        description=(
            "Staff-facing support workflow prototype. " "Outputs require staff review."
        ),
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metadata", response_model=ServiceMetadata)
    def metadata() -> ServiceMetadata:
        status = get_service_status.execute()
        return ServiceMetadata(
            classifier=_component_metadata(status.classifier),
            summarizer=_component_metadata(status.summarizer),
            knowledge_index=_component_metadata(status.knowledge_index),
        )

    @app.post("/analyze")
    def analyze(request: SupportMessageRequest) -> dict[str, object]:
        try:
            return analyze_support_request.execute(request.message)
        except ComponentNotConfiguredError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.post("/chat")
    def chat(request: ChatRequest) -> dict[str, object]:
        try:
            return answer_question.execute(request.question)
        except ComponentNotConfiguredError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.post("/retrieve", response_model=RetrievalResponse)
    def retrieve(request: ChatRequest) -> dict[str, object]:
        """Return source passages so retrieval can be checked before chat generation."""
        try:
            return retrieve_knowledge.execute(request.question)
        except ComponentNotConfiguredError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    return app
