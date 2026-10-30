from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentStatus:
    ready: bool
    version: str | None = None


@dataclass(frozen=True)
class ServiceStatus:
    classifier: ComponentStatus
    summarizer: ComponentStatus
    knowledge_index: ComponentStatus
