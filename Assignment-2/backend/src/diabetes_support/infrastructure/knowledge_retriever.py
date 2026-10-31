"""Retrieve source passages using configurable transformer embeddings."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import torch
import torch.nn.functional as functional
from dotenv import dotenv_values
from torch import Tensor
from transformers import AutoModel, AutoTokenizer

from diabetes_support.domain.errors import ComponentNotConfiguredError
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import PROJECT_ROOT

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class RetrievalSettings:
    model_name: str = DEFAULT_EMBEDDING_MODEL
    revision: str | None = None
    device: str = "auto"
    chunks_path: Path = PROJECT_ROOT / "data" / "knowledge" / "chunks.jsonl"
    cache_dir: Path = PROJECT_ROOT / "artifacts" / "huggingface"
    max_input_tokens: int = 256
    top_k: int = 3
    min_score: float = 0.20
    local_files_only: bool = False

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("RETRIEVAL_MODEL_NAME must not be empty.")
        if self.device not in {"auto", "cpu", "cuda", "mps"}:
            raise ValueError("RETRIEVAL_DEVICE must be auto, cpu, cuda or mps.")
        if self.max_input_tokens < 1 or self.top_k < 1:
            raise ValueError("Retrieval token and result limits must be positive.")
        if not -1.0 <= self.min_score <= 1.0:
            raise ValueError("RETRIEVAL_MIN_SCORE must be between -1 and 1.")

    @classmethod
    def from_env(cls) -> "RetrievalSettings":
        """Load retrieval-specific options and shared cache/offline settings."""
        values = {
            **dotenv_values(PROJECT_ROOT / ".env"),
            **os.environ,
        }

        def text(name: str, default: str) -> str:
            value = values.get(name)
            return default if value is None else str(value).strip()

        def project_path(name: str, default: str) -> Path:
            path = Path(text(name, default)).expanduser()
            return path if path.is_absolute() else PROJECT_ROOT / path

        offline = text("MODEL_LOCAL_FILES_ONLY", "false").lower()
        if offline not in {"true", "false"}:
            raise ValueError("MODEL_LOCAL_FILES_ONLY must be true or false.")

        try:
            max_input_tokens = int(text("RETRIEVAL_MAX_INPUT_TOKENS", "256"))
            top_k = int(text("RETRIEVAL_TOP_K", "3"))
            min_score = float(text("RETRIEVAL_MIN_SCORE", "0.20"))
        except ValueError as error:
            raise ValueError(
                "Retrieval limits and minimum score must be numeric."
            ) from error

        revision = text("RETRIEVAL_MODEL_REVISION", "") or None
        return cls(
            model_name=text("RETRIEVAL_MODEL_NAME", DEFAULT_EMBEDDING_MODEL),
            revision=revision,
            device=text("RETRIEVAL_DEVICE", "auto").lower(),
            chunks_path=project_path(
                "KNOWLEDGE_CHUNKS_PATH", "data/knowledge/chunks.jsonl"
            ),
            cache_dir=project_path("MODEL_CACHE_DIR", "artifacts/huggingface"),
            max_input_tokens=max_input_tokens,
            top_k=top_k,
            min_score=min_score,
            local_files_only=offline == "true",
        )


class TransformerKnowledgeRetriever:
    """Load local chunks and rank them by cosine similarity to a question."""

    def __init__(self, settings: RetrievalSettings) -> None:
        """Keep model loading lazy so the API can start without downloading weights."""
        self._settings = settings
        self._device = self._resolve_device(settings.device)
        # Only one request should load the model and build the index at a time.
        self._initialization_lock = Lock()
        self._tokenizer = None
        self._model = None
        self._chunks: list[dict[str, object]] | None = None
        self._embeddings: Tensor | None = None

    @property
    def status(self) -> ComponentStatus:
        """Report ready only after the model and chunk embeddings are loaded."""
        ready = self._model is not None and self._embeddings is not None
        name = Path(self._settings.model_name).name
        version = f"{name}@{self._settings.revision or 'default'}" if ready else None
        return ComponentStatus(ready=ready, version=version)

    def retrieve(self, question: str) -> list[dict[str, object]]:
        """Return the top matching passages with citations and similarity scores."""
        if not question.strip():
            return []
        self._ensure_index()
        assert self._model is not None
        assert self._tokenizer is not None
        assert self._embeddings is not None
        assert self._chunks is not None

        question_embedding = self._embed([question])[0]
        scores = self._embeddings @ question_embedding
        count = min(self._settings.top_k, len(self._chunks))
        indices = torch.topk(scores, k=count).indices.tolist()
        return [
            {
                "chunk_id": self._chunks[index]["chunk_id"],
                "source_title": self._chunks[index]["source_title"],
                "source_url": self._chunks[index]["source_url"],
                "section": self._chunks[index]["section"],
                "text": self._chunks[index]["text"],
                "score": float(scores[index].item()),
            }
            for index in indices
        ]

    def _ensure_index(self) -> None:
        """Load model and embed the small local corpus on the first request."""
        if self._embeddings is not None:
            return
        with self._initialization_lock:
            # Another request may have completed initialization while this one waited.
            if self._embeddings is not None:
                return
            chunks = self._read_chunks()
            try:
                load_options: dict[str, object] = {
                    "cache_dir": str(self._settings.cache_dir),
                    "local_files_only": self._settings.local_files_only,
                }
                if self._settings.revision:
                    load_options["revision"] = self._settings.revision
                tokenizer = AutoTokenizer.from_pretrained(
                    self._settings.model_name, **load_options
                )
                model = AutoModel.from_pretrained(
                    self._settings.model_name, **load_options
                ).to(self._device)
                model.eval()
                embeddings = self._embed(
                    [str(chunk["text"]) for chunk in chunks],
                    tokenizer=tokenizer,
                    model=model,
                )
            except (OSError, ValueError) as error:
                raise ComponentNotConfiguredError(
                    f"Could not load retrieval model '{self._settings.model_name}'. "
                    "Check the model name, network access and local cache settings."
                ) from error

            # Publish the complete index only after model loading and embedding succeed.
            self._tokenizer = tokenizer
            self._model = model
            self._chunks = chunks
            self._embeddings = embeddings

    def _read_chunks(self) -> list[dict[str, object]]:
        """Read and validate the JSONL chunk file before indexing it."""
        path = self._settings.chunks_path
        if not path.is_file():
            raise ComponentNotConfiguredError(
                "Knowledge chunks were not found at the configured path."
            )
        chunks: list[dict[str, object]] = []
        try:
            with path.open(encoding="utf-8") as chunk_file:
                for line_number, line in enumerate(chunk_file, start=1):
                    chunk = json.loads(line)
                    required = {
                        "chunk_id",
                        "source_title",
                        "source_url",
                        "section",
                        "text",
                    }
                    if not required.issubset(chunk) or not str(chunk["text"]).strip():
                        raise ValueError(
                            f"Invalid knowledge chunk at line {line_number}."
                        )
                    chunks.append(chunk)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise ComponentNotConfiguredError(
                "Could not read valid knowledge chunks from the configured path."
            ) from error
        if not chunks:
            raise ComponentNotConfiguredError(
                "No knowledge chunks were found at the configured path."
            )
        return chunks

    def _embed(
        self,
        texts: list[str],
        *,
        tokenizer=None,
        model=None,
    ) -> Tensor:
        """Mean-pool token embeddings and normalize them for cosine similarity."""
        if tokenizer is None:
            tokenizer = self._tokenizer
        if model is None:
            model = self._model
        assert tokenizer is not None
        assert model is not None
        encoded = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self._settings.max_input_tokens,
            return_tensors="pt",
        ).to(self._device)
        with torch.inference_mode():
            token_embeddings = model(**encoded).last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1).to(token_embeddings.dtype)
        pooled = (token_embeddings * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        return functional.normalize(pooled, p=2, dim=1)

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        """Choose a supported runtime device, preferring accelerators in auto mode."""
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        if device == "cuda" and not torch.cuda.is_available():
            raise ValueError("RETRIEVAL_DEVICE=cuda, but CUDA is unavailable.")
        if device == "mps" and not torch.backends.mps.is_available():
            raise ValueError("RETRIEVAL_DEVICE=mps, but Apple MPS is unavailable.")
        return torch.device(device)

