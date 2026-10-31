"""Lazy shared sequence-to-sequence model and tokenizer."""

from threading import Lock

from diabetes_support.domain.errors import ComponentNotConfiguredError
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import ModelSettings


class Seq2SeqRuntime:
    """Load one configured model and reuse it to generate text for each task."""

    def __init__(self, settings: ModelSettings) -> None:
        self.settings = settings
        self._device: str | None = None
        self._tokenizer = None
        self._model = None
        self._load_lock = Lock()

    @property
    def device(self) -> str | None:
        return self._device

    @property
    def status(self) -> ComponentStatus:
        ready = self._model is not None
        version = (
            f"{self.settings.model_name}@{self.settings.resolved_revision or 'default'}"
            if ready
            else None
        )
        return ComponentStatus(ready=ready, version=version)

    def load(self) -> None:
        # Load once, even when two requests arrive together on a fresh server.
        with self._load_lock:
            if self._model is not None:
                return
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            except ImportError as error:
                raise ComponentNotConfiguredError(
                    "Install the inference extra to use a Transformers "
                    "sequence-to-sequence model."
                ) from error

            device = self.settings.device
            if device == "auto":
                device = (
                    "cuda"
                    if torch.cuda.is_available()
                    else "mps" if torch.backends.mps.is_available() else "cpu"
                )
            if device == "cuda" and not torch.cuda.is_available():
                raise ValueError("CUDA is unavailable. Choose cpu or another device.")
            if device == "mps" and not torch.backends.mps.is_available():
                raise ValueError("MPS is unavailable. Choose cpu or another device.")

            # Model and tokenizer must use the same source and revision.
            options = {
                "revision": self.settings.resolved_revision,
                "cache_dir": self.settings.cache_dir,
                "local_files_only": self.settings.local_files_only,
            }
            tokenizer = AutoTokenizer.from_pretrained(
                self.settings.model_name, **options
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                self.settings.model_name, use_safetensors=True, **options
            ).to(device)
            model.eval()
            self._device = device
            self._tokenizer = tokenizer
            self._model = model

    def generate(self, prompt: str, *, max_new_tokens: int) -> str:
        self.load()
        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=False)
        if inputs["input_ids"].shape[1] > self.settings.max_input_tokens:
            raise ValueError(
                f"The prompt exceeds the {self.settings.max_input_tokens}-token "
                "input limit."
            )
        inputs = {name: tensor.to(self._device) for name, tensor in inputs.items()}
        with torch.inference_mode():
            output = self._model.generate(
                **inputs, max_new_tokens=max_new_tokens, do_sample=False
            )
        return self._tokenizer.decode(output[0], skip_special_tokens=True).strip()
