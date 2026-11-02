from pydantic import BaseModel, Field, field_validator


class SupportMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must contain non-whitespace text.")
        return value


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must contain non-whitespace text.")
        return value


class RetrievedSource(BaseModel):
    chunk_id: str
    source_title: str
    source_url: str
    section: str
    text: str
    score: float


class RetrievalResponse(BaseModel):
    question: str
    sources: list[RetrievedSource]


class ChatResponse(BaseModel):
    answer: str
    abstained: bool
    sources: list[RetrievedSource]


class ComponentMetadata(BaseModel):
    ready: bool
    version: str | None = None


class ServiceMetadata(BaseModel):
    classifier: ComponentMetadata
    summarizer: ComponentMetadata
    knowledge_index: ComponentMetadata
