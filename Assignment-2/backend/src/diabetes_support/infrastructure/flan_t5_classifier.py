"""Configurable seq2seq implementation of the application's Classifier interface."""

import argparse
import json
from threading import Lock

from diabetes_support.domain.errors import ComponentNotConfiguredError
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.classifier_settings import ClassifierSettings

# These descriptions go into the instruction. They are not training examples or
# keyword-matching rules: the model must choose a category from the message.
LABELS = {
    "appointment_support": "book, confirm, cancel or change an appointment",
    "education_resource_request": "request general education material or join a class",
    "portal_technical_support": "report a login, website or upload failure",
    "records_insurance_admin": "request records, insurance, billing or paperwork help",
    "clinical_staff_referral": "request personal medical advice or clinical review",
}


class FlanT5Classifier:
    """Reuse one configured seq2seq model for support-message predictions."""

    def __init__(self, settings: ClassifierSettings | None = None) -> None:
        self.settings = (
            settings if settings is not None else ClassifierSettings.from_env()
        )
        self._device = None
        self._tokenizer = None
        self._model = None
        self._load_lock = Lock()

    @property
    def status(self) -> ComponentStatus:
        # Ready means the weights are loaded; it does not imply measured accuracy.
        ready = self._model is not None
        return ComponentStatus(
            ready=ready,
            version=(
                f"{self.settings.model}@{self.settings.resolved_revision or 'default'}"
                if ready
                else None
            ),
        )

    def load(self) -> None:
        # Loading is deferred until needed. The lock prevents simultaneous first
        # requests from loading duplicate copies into memory.
        with self._load_lock:
            if self._model is not None:
                return
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            except ImportError as error:
                raise ComponentNotConfiguredError(
                    "Install the inference extra to use the FLAN-T5 classifier."
                ) from error

            device = self.settings.device
            if device == "auto":
                device = (
                    "cuda"
                    if torch.cuda.is_available()
                    else "mps" if torch.backends.mps.is_available() else "cpu"
                )
            if device == "cuda" and not torch.cuda.is_available():
                raise ValueError(
                    "CUDA is unavailable. Choose cpu or another available device."
                )
            if device == "mps" and not torch.backends.mps.is_available():
                raise ValueError(
                    "MPS is unavailable. Choose cpu or another available device."
                )

            # The same source and revision load both weights and tokenizer.
            options = {
                "revision": self.settings.resolved_revision,
                "cache_dir": self.settings.cache_dir,
                "local_files_only": self.settings.local_files_only,
            }
            tokenizer = AutoTokenizer.from_pretrained(self.settings.model, **options)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                self.settings.model, use_safetensors=True, **options
            ).to(device)
            # Disable training behaviour such as dropout. No weights are updated.
            model.eval()
            self._device = device
            self._tokenizer = tokenizer
            self._model = model

    def classify(self, message: str, /) -> dict[str, object]:
        message = message.strip()
        if not message:
            raise ValueError("The message must not be empty.")

        self.load()
        import torch

        # Instructions guide inference; they are not examples used for training.
        choices = "\n".join(f"- {name}: {meaning}" for name, meaning in LABELS.items())
        prompt = (
            "Classify this clinic support message. Return exactly one category name.\n"
            f"Categories:\n{choices}\n"
            "If the message also asks for personal medical advice, choose "
            "clinical_staff_referral. Otherwise choose the main request.\n"
            f"Message: {message}\nCategory:"
        )
        # Tokenize the full prompt. Reject long inputs instead of cutting them off.
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=False)
        if inputs["input_ids"].shape[1] > self.settings.max_input_tokens:
            raise ValueError(
                f"The prompt exceeds the {self.settings.max_input_tokens}-token "
                "input limit."
            )
        # Inputs and weights must be on the same device for GPU inference.
        inputs = {name: tensor.to(self._device) for name, tensor in inputs.items()}

        # Generate output tokens without tracking gradients required for training.
        with torch.inference_mode():
            output = self._model.generate(
                **inputs, max_new_tokens=self.settings.max_new_tokens, do_sample=False
            )

        # Decode the answer and preserve unexpected output for staff review.
        raw_output = self._tokenizer.decode(output[0], skip_special_tokens=True).strip()
        category = raw_output if raw_output in LABELS else None
        return {
            "model": self.settings.model,
            "model_revision": self.settings.resolved_revision,
            "device": self._device,
            "raw_output": raw_output,
            "category": category,
            "valid_category": category is not None,
            # Selecting a checkpoint does not prove who trained it.
            "weights_updated_during_inference": False,
        }


def main() -> int:
    """Exercise the actual application classifier directly from the terminal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default="Please move my appointment to Friday.")
    args = parser.parse_args()
    try:
        result = FlanT5Classifier().classify(args.message)
    except (ValueError, ComponentNotConfiguredError) as error:
        parser.error(str(error))
    print(json.dumps({"message": args.message, **result}, indent=2))
    return 0 if result["valid_category"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
