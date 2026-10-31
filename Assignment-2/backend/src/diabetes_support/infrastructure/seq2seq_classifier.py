"""Configurable seq2seq implementation of the application's Classifier interface."""

import argparse
import json

from diabetes_support.domain.errors import ComponentNotConfiguredError
from diabetes_support.domain.status import ComponentStatus
from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_runtime import Seq2SeqRuntime

# These descriptions guide the model; they are not training examples or rules.
LABELS = {
    "appointment_support": "book, confirm, cancel or change an appointment",
    "education_resource_request": "request general education material or join a class",
    "portal_technical_support": "report a login, website or upload failure",
    "records_insurance_admin": "request records, insurance, billing or paperwork help",
    "clinical_staff_referral": "request personal medical advice or clinical review",
}


class Seq2SeqClassifier:
    """Reuse a configured seq2seq runtime for support-message predictions."""

    def __init__(
        self,
        settings: ModelSettings | None = None,
        *,
        runtime: Seq2SeqRuntime | None = None,
    ) -> None:
        self.settings = settings or ModelSettings.from_env()
        self.runtime = runtime or Seq2SeqRuntime(self.settings)

    @property
    def status(self) -> ComponentStatus:
        # Readiness means the shared weights are loaded, not that accuracy is known.
        return self.runtime.status

    def load(self) -> None:
        """Load the shared model explicitly when a caller needs eager loading."""
        self.runtime.load()

    def classify(self, message: str, /) -> dict[str, object]:
        message = message.strip()
        if not message:
            raise ValueError("The message must not be empty.")

        choices = "\n".join(f"- {name}: {meaning}" for name, meaning in LABELS.items())
        prompt = (
            "Classify this clinic support message. Return exactly one category name.\n"
            f"Categories:\n{choices}\n"
            "If the message also asks for personal medical advice, choose "
            "clinical_staff_referral. Otherwise choose the main request.\n"
            f"Message: {message}\nCategory:"
        )
        raw_output = self.runtime.generate(
            prompt, max_new_tokens=self.settings.classification_max_new_tokens
        )
        category = raw_output if raw_output in LABELS else None
        return {
            "model": self.settings.model_name,
            "model_revision": self.settings.resolved_revision,
            "device": self.runtime.device,
            "raw_output": raw_output,
            "category": category,
            "valid_category": category is not None,
            "weights_updated_during_inference": False,
        }


def main() -> int:
    """Exercise the actual application classifier directly from the terminal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default="Please move my appointment to Friday.")
    args = parser.parse_args()
    try:
        result = Seq2SeqClassifier().classify(args.message)
    except (ValueError, ComponentNotConfiguredError) as error:
        parser.error(str(error))
    print(json.dumps({"message": args.message, **result}, indent=2))
    return 0 if result["valid_category"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
