"""Fine-tune FLAN-T5 for handoff summaries using reviewed train/validation pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
TRAIN_FILE = ROOT / "data/training/summarization_train.jsonl"
VALIDATION_FILE = ROOT / "data/validation/summarization_validation.jsonl"
DEFAULT_OUTPUT = ROOT / "artifacts/models/clinic-summary"
sys.path.insert(0, str(ROOT / "backend/src"))

from diabetes_support.infrastructure.model_settings import ModelSettings  # noqa: E402
from diabetes_support.infrastructure.seq2seq_summarizer import (  # noqa: E402
    build_summary_prompt,
)


def resolve_device(requested: str, torch: Any) -> str:
    """Resolve automatic device choice or validate an explicit one."""
    if requested not in {"auto", "cpu", "mps", "cuda"}:
        raise ValueError("Device must be auto, cpu, mps, or cuda.")
    mps = getattr(torch.backends, "mps", None)
    if requested == "auto":
        if torch.cuda.is_available():
            return "cuda"
        return "mps" if mps is not None and mps.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is unavailable.")
    if requested == "mps" and (mps is None or not mps.is_available()):
        raise ValueError("MPS was requested but is unavailable.")
    return requested


def read_partition(path: Path) -> list[dict[str, str]]:
    """Read reviewed message/summary pairs and reject malformed records."""
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"Dataset is empty: {path}")
    seen: set[str] = set()
    required = {
        "example_id",
        "scenario_family_id",
        "message",
        "summary",
        "review_status",
        "reviewer",
    }
    for number, row in enumerate(rows, 1):
        if required - row.keys():
            raise ValueError(
                f"{path.name} row {number} is missing {sorted(required - row.keys())}"
            )
        if row["example_id"] in seen:
            raise ValueError(f"Duplicate example ID: {row['example_id']}")
        seen.add(row["example_id"])
        if not row["message"].strip() or not row["summary"].strip():
            raise ValueError(f"Empty message or summary: {row['example_id']}")
        if row["review_status"] != "approved" or not row["reviewer"].strip():
            raise ValueError(f"Unreviewed training pair: {row['example_id']}")
    return rows


def validate_partitions(
    train: list[dict[str, str]], validation: list[dict[str, str]]
) -> None:
    """Reject exact messages and scenario families shared across the split."""
    if {r["example_id"] for r in train} & {r["example_id"] for r in validation}:
        raise ValueError("An example ID appears in both partitions.")
    if {r["message"] for r in train} & {r["message"] for r in validation}:
        raise ValueError("Training and validation contain an identical message.")
    if {r["scenario_family_id"] for r in train} & {
        r["scenario_family_id"] for r in validation
    }:
        raise ValueError("A scenario family appears in both partitions.")


def tokenize_rows(
    rows: list[dict[str, str]], tokenizer: Any, settings: ModelSettings
) -> list[dict[str, list[int]]]:
    """Tokenize the inference prompt and reviewed target summary."""
    features = []
    for row in rows:
        source = tokenizer(
            build_summary_prompt(row["message"]),
            truncation=True,
            max_length=settings.max_input_tokens,
        )
        target = tokenizer(
            text_target=row["summary"],
            truncation=True,
            max_length=settings.summary_max_new_tokens,
        )
        features.append(
            {
                "input_ids": source["input_ids"],
                "attention_mask": source["attention_mask"],
                "labels": target["input_ids"],
            }
        )
    return features


def make_batch(features: list[dict[str, list[int]]], tokenizer: Any) -> dict[str, Any]:
    """Pad source and target tokens and ignore target padding in the loss."""
    batch = tokenizer.pad(
        [
            {"input_ids": r["input_ids"], "attention_mask": r["attention_mask"]}
            for r in features
        ],
        return_tensors="pt",
    )
    labels = tokenizer.pad(
        [{"input_ids": r["labels"]} for r in features], return_tensors="pt"
    )["input_ids"]
    labels[labels == tokenizer.pad_token_id] = -100
    batch["labels"] = labels
    return batch


def rouge_l_f1(reference: str, prediction: str) -> float:
    """Compute token-level ROUGE-L F1 without another package dependency."""
    expected, actual = reference.casefold().split(), prediction.casefold().split()
    if not expected or not actual:
        return 0.0
    previous = [0] * (len(actual) + 1)
    for word in expected:
        current = [0]
        for index, candidate in enumerate(actual, 1):
            current.append(
                previous[index - 1] + 1
                if word == candidate
                else max(previous[index], current[index - 1])
            )
        previous = current
    overlap = previous[-1]
    precision, recall = overlap / len(actual), overlap / len(expected)
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def evaluate(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, str]],
    settings: ModelSettings,
    device: str,
    torch: Any,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Generate validation summaries using the application's decoding settings."""
    predictions = []
    model.eval()
    with torch.inference_mode():
        for index, row in enumerate(rows, start=1):
            inputs = tokenizer(
                build_summary_prompt(row["message"]),
                return_tensors="pt",
                truncation=True,
                max_length=settings.max_input_tokens,
            ).to(device)
            generated = model.generate(
                **inputs,
                max_new_tokens=settings.summary_max_new_tokens,
                do_sample=False,
                num_beams=4,
                no_repeat_ngram_size=3,
            )[0]
            prediction = tokenizer.decode(generated, skip_special_tokens=True).strip()
            predictions.append(
                {
                    "example_id": row["example_id"],
                    "reference": row["summary"],
                    "prediction": prediction,
                    "rouge_l_f1": rouge_l_f1(row["summary"], prediction),
                    "input_words": len(row["message"].split()),
                    "prediction_words": len(prediction.split()),
                }
            )
            if index % 10 == 0 or index == len(rows):
                print(f"  Validation: {index}/{len(rows)} examples", flush=True)
    scores = [r["rouge_l_f1"] for r in predictions]
    ratios = [r["prediction_words"] / max(r["input_words"], 1) for r in predictions]
    return {
        "mean_rouge_l_f1": sum(scores) / len(scores),
        "mean_output_input_word_ratio": sum(ratios) / len(ratios),
    }, predictions


def main() -> int:
    """Train on approved pairs and select epochs using validation only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"))
    parser.add_argument(
        "--base-model",
        help="Base checkpoint to fine-tune; defaults to SUMMARIZER_BASE_MODEL_NAME.",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--smoke", action="store_true", help="Run one update without saving."
    )
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.gradient_accumulation_steps) < 1:
        parser.error("Epochs, batch size, and accumulation must be positive.")
    if args.learning_rate <= 0:
        parser.error("Learning rate must be positive.")
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.smoke:
        parser.error(f"Output directory is not empty: {args.output_dir}")

    env = {**dotenv_values(ROOT / ".env"), **os.environ}
    requested = args.device or str(env.get("TRAINING_DEVICE") or "auto").lower()
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = resolve_device(requested, torch)
    settings = ModelSettings.from_env(ROOT / ".env", component="summarizer")
    train_rows = read_partition(TRAIN_FILE)
    if args.smoke:
        # Smoke needs one training row; it does not inspect validation data.
        train_rows = train_rows[:1]
        validation_rows = []
    else:
        validation_rows = read_partition(VALIDATION_FILE)
        validate_partitions(train_rows, validation_rows)

    # Keep the training base separate from SUMMARIZER_MODEL_NAME, which selects
    # the inference checkpoint after training is complete.
    base_model_name = (
        args.base_model
        or env.get("SUMMARIZER_BASE_MODEL_NAME")
        or "google/flan-t5-base"
    )
    if base_model_name.startswith(("./", "../", "/", "~", "artifacts/")):
        base_path = Path(base_model_name).expanduser()
        if not base_path.is_absolute():
            base_path = ROOT / base_path
        if not base_path.is_dir():
            parser.error(f"Base checkpoint directory does not exist: {base_path}")
        base_model_name = str(base_path.resolve())
    base_model_revision = env.get("SUMMARIZER_BASE_MODEL_REVISION") or None
    settings = replace(
        settings,
        model_name=base_model_name,
        model_revision=base_model_revision,
    )

    mode = "smoke check" if args.smoke else "fine-tuning"
    print(
        f"Starting summarizer {mode}: {len(train_rows)} training example(s), "
        f"{len(validation_rows)} validation example(s), device={device}.",
        flush=True,
    )
    print(f"Loading tokenizer and base model: {settings.display_name}...", flush=True)

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    load_options = {
        "revision": settings.resolved_revision,
        "cache_dir": settings.cache_dir,
        "local_files_only": settings.local_files_only,
    }
    tokenizer = AutoTokenizer.from_pretrained(settings.model_name, **load_options)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        settings.model_name, use_safetensors=True, **load_options
    ).to(device)
    model.config.use_cache = False
    model.generation_config.use_cache = False
    model.gradient_checkpointing_enable()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    train_features = tokenize_rows(train_rows, tokenizer, settings)
    print("Base model loaded; tokenized training examples.", flush=True)

    if args.smoke:
        batch = make_batch(train_features, tokenizer)
        batch = {name: value.to(device) for name, value in batch.items()}
        loss = model(**batch).loss
        loss_value = float(loss.detach().cpu())
        loss.backward()
        optimizer.step()
        print(
            json.dumps(
                {
                    "mode": "one_step_smoke",
                    "model": settings.display_name,
                    "device": device,
                    "examples": len(train_rows),
                    "loss": round(loss_value, 4),
                    "validation_loaded": False,
                    "test_loaded": False,
                    "checkpoint_saved": False,
                },
                indent=2,
            )
        )
        return 0

    order = list(range(len(train_features)))
    history, best_score, total_steps = [], -1.0, 0
    for epoch in range(1, args.epochs + 1):
        print(f"Epoch {epoch}/{args.epochs}: training...", flush=True)
        random.shuffle(order)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        epoch_loss = 0.0
        starts = list(range(0, len(order), args.batch_size))
        for batch_number, start in enumerate(starts):
            samples = [
                train_features[i] for i in order[start : start + args.batch_size]
            ]
            batch = make_batch(samples, tokenizer)
            batch = {name: value.to(device) for name, value in batch.items()}
            loss = model(**batch).loss
            epoch_loss += float(loss.detach().cpu())
            window_start = (
                batch_number // args.gradient_accumulation_steps
            ) * args.gradient_accumulation_steps
            window_size = min(
                args.gradient_accumulation_steps, len(starts) - window_start
            )
            (loss / window_size).backward()
            if (
                batch_number + 1
            ) % args.gradient_accumulation_steps == 0 or batch_number + 1 == len(
                starts
            ):
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                total_steps += 1
            progress_interval = max(1, len(starts) // 10)
            if (batch_number + 1) % progress_interval == 0 or batch_number + 1 == len(
                starts
            ):
                print(
                    f"  Training: {batch_number + 1}/{len(starts)} batches",
                    flush=True,
                )

        print(f"Epoch {epoch}/{args.epochs}: validating...", flush=True)
        model.config.use_cache = True
        model.generation_config.use_cache = True
        model.gradient_checkpointing_disable()
        metrics, predictions = evaluate(
            model, tokenizer, validation_rows, settings, device, torch
        )
        record = {
            "epoch": epoch,
            "mean_training_loss": round(epoch_loss / len(starts), 4),
            "optimizer_steps": total_steps,
            "validation": metrics,
        }
        history.append(record)
        print(json.dumps(record, indent=2))
        score = metrics["mean_rouge_l_f1"]
        if score > best_score:
            best_score = score
            args.output_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(args.output_dir, safe_serialization=True)
            tokenizer.save_pretrained(args.output_dir)
            summary = {
                "base_model": settings.display_name,
                "base_revision": settings.resolved_revision,
                "device": device,
                "seed": args.seed,
                "epochs_completed": epoch,
                "optimizer_steps": total_steps,
                "training_examples": len(train_rows),
                "validation_examples": len(validation_rows),
                "training_file_sha256": hashlib.sha256(
                    TRAIN_FILE.read_bytes()
                ).hexdigest(),
                "validation_file_sha256": hashlib.sha256(
                    VALIDATION_FILE.read_bytes()
                ).hexdigest(),
                "best_validation": metrics,
                "history": history,
                "validation_predictions": predictions,
                "test_set_loaded": False,
            }
            (args.output_dir / "training_summary.json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        model.config.use_cache = False
        model.generation_config.use_cache = False
        model.gradient_checkpointing_enable()
    print(f"Best validation ROUGE-L F1: {best_score:.4f}")
    print(f"Selected checkpoint: {args.output_dir}")
    print("Summarizer fine-tuning complete.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
