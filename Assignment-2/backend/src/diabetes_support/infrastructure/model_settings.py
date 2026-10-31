"""Read shared model settings from .env and the environment."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODEL_NAME = "google/flan-t5-base"
DEFAULT_MODEL_REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"


@dataclass(frozen=True)
class ModelSettings:
    model_name: str = DEFAULT_MODEL_NAME
    model_revision: str | None = None
    device: str = "cpu"
    cache_dir: Path = PROJECT_ROOT / "artifacts" / "huggingface"
    max_input_tokens: int = 512
    classification_max_new_tokens: int = 32
    summary_max_new_tokens: int = 128
    local_files_only: bool = False

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("MODEL_NAME must not be empty.")
        if self.device not in {"cpu", "cuda", "mps", "auto"}:
            raise ValueError("MODEL_DEVICE must be cpu, cuda, mps or auto.")
        if (
            self.max_input_tokens < 1
            or self.classification_max_new_tokens < 1
            or self.summary_max_new_tokens < 1
        ):
            raise ValueError("Model token limits must be positive integers.")

    @property
    def resolved_revision(self) -> str | None:
        # Keep the verified baseline pinned. Other models must not inherit its SHA.
        return self.model_revision or (
            DEFAULT_MODEL_REVISION if self.model_name == DEFAULT_MODEL_NAME else None
        )

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "ModelSettings":
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

        model_name = text("MODEL_NAME", DEFAULT_MODEL_NAME)
        if not model_name:
            raise ValueError("MODEL_NAME must not be empty.")
        candidate = project_path(model_name)
        if candidate.is_dir():
            model_name = str(candidate.resolve())
        elif model_name.startswith(("./", "../", "/", "~", "artifacts/")):
            raise ValueError(f"Model checkpoint directory does not exist: {candidate}")

        offline = text("MODEL_LOCAL_FILES_ONLY", "false").lower()
        if offline not in {"true", "false"}:
            raise ValueError("MODEL_LOCAL_FILES_ONLY must be true or false.")

        return cls(
            model_name=model_name,
            model_revision=text("MODEL_REVISION", "") or None,
            device=text("MODEL_DEVICE", "cpu").lower(),
            cache_dir=project_path(text("MODEL_CACHE_DIR", "artifacts/huggingface")),
            max_input_tokens=positive_int("MODEL_MAX_INPUT_TOKENS", 512),
            classification_max_new_tokens=positive_int(
                "CLASSIFICATION_MAX_NEW_TOKENS", 32
            ),
            summary_max_new_tokens=positive_int("SUMMARY_MAX_NEW_TOKENS", 128),
            local_files_only=offline == "true",
        )
