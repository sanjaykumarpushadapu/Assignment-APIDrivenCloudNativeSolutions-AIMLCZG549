"""Read classifier settings from .env, with environment variables taking priority."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BASELINE_MODEL = "google/flan-t5-base"
BASELINE_REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"


@dataclass(frozen=True)
class ClassifierSettings:
    model: str = BASELINE_MODEL
    revision: str | None = None
    device: str = "cpu"
    cache_dir: Path = PROJECT_ROOT / "artifacts" / "huggingface"
    max_input_tokens: int = 512
    max_new_tokens: int = 32
    local_files_only: bool = False

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("CLASSIFIER_MODEL must not be empty.")
        if self.device not in {"cpu", "cuda", "mps", "auto"}:
            raise ValueError("CLASSIFIER_DEVICE must be cpu, cuda, mps or auto.")
        if self.max_input_tokens < 1 or self.max_new_tokens < 1:
            raise ValueError("Classifier token limits must be positive integers.")

    @property
    def resolved_revision(self) -> str | None:
        # Keep the verified baseline pinned. Other models must not inherit its SHA.
        return self.revision or (
            BASELINE_REVISION if self.model == BASELINE_MODEL else None
        )

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "ClassifierSettings":
        # Read only; do not mutate process variables when loading a .env file.
        values = {**dotenv_values(env_file or PROJECT_ROOT / ".env"), **os.environ}

        def text(name: str, default: str) -> str:
            value = values.get(name)
            return default if value is None else value.strip()

        def positive_int(name: str, default: int) -> int:
            try:
                number = int(text(name, str(default)))
            except ValueError as error:
                raise ValueError(f"{name} must be a positive integer.") from error
            if number < 1:
                raise ValueError(f"{name} must be a positive integer.")
            return number

        def project_path(value: str) -> Path:
            path = Path(value).expanduser()
            return path if path.is_absolute() else PROJECT_ROOT / path

        model = text("CLASSIFIER_MODEL", BASELINE_MODEL)
        if not model:
            raise ValueError("CLASSIFIER_MODEL must not be empty.")
        candidate = project_path(model)
        if candidate.is_dir():
            model = str(candidate.resolve())
        elif model.startswith(("./", "../", "/", "~", "artifacts/")):
            raise ValueError(
                f"Classifier checkpoint directory does not exist: {candidate}"
            )

        offline = text("CLASSIFIER_LOCAL_FILES_ONLY", "false").lower()
        if offline not in {"true", "false"}:
            raise ValueError("CLASSIFIER_LOCAL_FILES_ONLY must be true or false.")

        return cls(
            model=model,
            revision=text("CLASSIFIER_REVISION", "") or None,
            device=text("CLASSIFIER_DEVICE", "cpu").lower(),
            cache_dir=project_path(
                text("CLASSIFIER_CACHE_DIR", "artifacts/huggingface")
            ),
            max_input_tokens=positive_int("CLASSIFIER_MAX_INPUT_TOKENS", 512),
            max_new_tokens=positive_int("CLASSIFIER_MAX_NEW_TOKENS", 32),
            local_files_only=offline == "true",
        )
