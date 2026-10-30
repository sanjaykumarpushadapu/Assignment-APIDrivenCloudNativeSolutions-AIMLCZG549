from pydantic import BaseModel, Field


class SupportMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ComponentMetadata(BaseModel):
    ready: bool
    version: str | None = None


class ServiceMetadata(BaseModel):
    classifier: ComponentMetadata
    summarizer: ComponentMetadata
    knowledge_index: ComponentMetadata
