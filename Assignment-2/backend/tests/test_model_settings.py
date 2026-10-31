from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from diabetes_support.infrastructure.model_settings import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_REVISION,
    PROJECT_ROOT,
    ModelSettings,
)


@pytest.fixture(autouse=True)
def isolate_model_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    for name in list(os.environ):
        if name.startswith(("MODEL_", "CLASSIFICATION_", "SUMMARY_")):
            monkeypatch.delenv(name)


def test_default_model_keeps_verified_revision(tmp_path: Path) -> None:
    settings = ModelSettings.from_env(tmp_path / "missing.env")
    assert settings.model_name == DEFAULT_MODEL_NAME
    assert settings.resolved_revision == DEFAULT_MODEL_REVISION
    assert settings.device == "cpu"


def test_changed_model_does_not_inherit_baseline_revision(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("MODEL_NAME=google/flan-t5-small\n")
    assert ModelSettings.from_env(env).resolved_revision is None


def test_environment_overrides_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = tmp_path / ".env"
    env.write_text("MODEL_DEVICE=cpu\nCLASSIFICATION_MAX_NEW_TOKENS=16\n")
    monkeypatch.setenv("MODEL_DEVICE", "auto")
    settings = ModelSettings.from_env(env)
    assert settings.device == "auto"
    assert settings.classification_max_new_tokens == 16


def test_local_checkpoint_and_cache_paths(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    env.write_text(
        f"MODEL_NAME={checkpoint}\n"
        "MODEL_CACHE_DIR=artifacts/custom-cache\n"
        "MODEL_LOCAL_FILES_ONLY=true\n"
    )
    settings = ModelSettings.from_env(env)
    assert settings.model_name == str(checkpoint)
    assert settings.resolved_revision is None
    assert settings.cache_dir == PROJECT_ROOT / "artifacts/custom-cache"
    assert settings.local_files_only is True


@pytest.mark.parametrize(
    "entry",
    [
        "MODEL_NAME=",
        "MODEL_NAME=./missing-checkpoint-directory",
        "MODEL_DEVICE=typo",
        "MODEL_MAX_INPUT_TOKENS=0",
        "CLASSIFICATION_MAX_NEW_TOKENS=abc",
        "MODEL_LOCAL_FILES_ONLY=maybe",
    ],
)
def test_invalid_settings_fail_early(tmp_path: Path, entry: str) -> None:
    env = tmp_path / ".env"
    env.write_text(entry + "\n")
    with pytest.raises(ValueError):
        ModelSettings.from_env(env)


def test_classifier_passes_settings_to_loader_and_reuses_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import sys

    from diabetes_support.infrastructure.seq2seq_classifier import Seq2SeqClassifier

    tokenizer = Mock()
    model = Mock()
    model.to.return_value = model
    tokenizer_loader = Mock(return_value=tokenizer)
    model_loader = Mock(return_value=model)
    # Fake only the expensive external loaders; no weights or GPU are needed.
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoTokenizer=SimpleNamespace(from_pretrained=tokenizer_loader),
            AutoModelForSeq2SeqLM=SimpleNamespace(from_pretrained=model_loader),
        ),
    )
    settings = ModelSettings(
        model_name="example/custom-t5",
        model_revision="custom-revision",
        cache_dir=tmp_path,
        local_files_only=True,
    )
    classifier = Seq2SeqClassifier(settings)
    assert not classifier.status.ready
    classifier.load()
    classifier.load()
    options = {
        "revision": "custom-revision",
        "cache_dir": tmp_path,
        "local_files_only": True,
    }
    tokenizer_loader.assert_called_once_with("example/custom-t5", **options)
    model_loader.assert_called_once_with(
        "example/custom-t5", use_safetensors=True, **options
    )
    model.to.assert_called_once_with("cpu")
    assert classifier.status.ready
    assert classifier.status.version == "example/custom-t5@custom-revision"
