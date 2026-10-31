"""Fine-tune the classifier on training data and select checkpoints on validation.

The training and validation paths are fixed here on purpose. This script never
opens the final test set. Use ``--smoke`` for one small optimizer step before a
full run; the smoke mode does not evaluate or save a checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_FILE = PROJECT_ROOT / "data" / "training" / "classification_train.jsonl"
VALIDATION_FILE = (
    PROJECT_ROOT / "data" / "validation" / "classification_validation.jsonl"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "models" / "clinic-support"

# Allow running this script directly without installing the package first.
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from evaluate_classifier import calculate_metrics  # noqa: E402

from diabetes_support.infrastructure.model_settings import ModelSettings  # noqa: E402
from diabetes_support.infrastructure.seq2seq_classifier import (  # noqa: E402
    LABELS,
    build_classification_prompt,
)


def resolve_device(requested: str, torch: Any) -> str:
    """Select a supported accelerator, or check an explicit user choice."""
    if requested not in {"auto", "cpu", "mps", "cuda"}:
        raise ValueError("Training device must be auto, cpu, mps, or cuda.")
    mps_backend = getattr(torch.backends, "mps", None)
    if requested == "auto":
        # Prefer an accelerator; fall back to CPU, which is available everywhere.
        if torch.cuda.is_available():
            return "cuda"
        if mps_backend is not None and mps_backend.is_available():
            return "mps"
        return "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError(
            "CUDA was requested, but this machine has no available CUDA device."
        )
    if requested == "mps" and (mps_backend is None or not mps_backend.is_available()):
        raise ValueError(
            "MPS was requested, but it is unavailable in this Python environment."
        )
    return requested


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a JSONL partition and check its training fields and labels."""
    # Parse each nonblank line as an independent JSON training example.
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"Dataset is empty: {path}")
    # Reject malformed examples before tokenization or a long training run begins.
    required = {"example_id", "message", "category"}
    seen_ids: set[str] = set()
    for number, row in enumerate(rows, start=1):
        missing = required - row.keys()
        if missing:
            raise ValueError(f"{path.name} row {number} is missing {sorted(missing)}")
        if row["category"] not in LABELS:
            raise ValueError(
                f"Unsupported label in {row['example_id']}: {row['category']}"
            )
        if not row["message"].strip():
            raise ValueError(f"Empty message in {row['example_id']}")
        if row["example_id"] in seen_ids:
            raise ValueError(
                f"Duplicate example ID in {path.name}: {row['example_id']}"
            )
        seen_ids.add(row["example_id"])
    return rows


def tokenize_rows(
    rows: list[dict[str, str]], tokenizer: Any, settings: ModelSettings
) -> list[dict[str, list[int]]]:
    """Turn messages and category targets into token IDs for the model."""
    features = []
    for row in rows:
        # Use the inference instruction as input and the category name as target text.
        source = tokenizer(
            build_classification_prompt(row["message"]),
            truncation=True,
            max_length=settings.max_input_tokens,
        )
        target = tokenizer(text_target=row["category"], truncation=True, max_length=16)
        features.append(
            {
                "input_ids": source["input_ids"],
                "attention_mask": source["attention_mask"],
                "target_ids": target["input_ids"],
            }
        )
    return features


def make_batch(
    features: list[dict[str, list[int]]], tokenizer: Any, torch: Any
) -> dict[str, Any]:
    """Pad a batch and mask target padding so it is ignored by the loss."""
    inputs = tokenizer.pad(
        [
            {"input_ids": item["input_ids"], "attention_mask": item["attention_mask"]}
            for item in features
        ],
        return_tensors="pt",
    )
    # Mask target padding so those positions do not contribute to training loss.
    targets = tokenizer.pad(
        [{"input_ids": item["target_ids"]} for item in features],
        return_tensors="pt",
    )["input_ids"]
    targets[targets == tokenizer.pad_token_id] = -100
    inputs["labels"] = targets
    return inputs


def evaluate(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, str]],
    settings: ModelSettings,
    device: str,
    torch: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Score a checkpoint using validation predictions and fixed decoding."""
    model.eval()
    predictions = []
    with torch.inference_mode():
        for row in rows:
            # Match the deterministic decoding settings used by baseline evaluation.
            encoded = tokenizer(
                build_classification_prompt(row["message"]),
                return_tensors="pt",
                truncation=True,
                max_length=settings.max_input_tokens,
            ).to(device)
            raw_output = tokenizer.decode(
                model.generate(
                    **encoded,
                    max_new_tokens=settings.classification_max_new_tokens,
                    do_sample=False,
                )[0],
                skip_special_tokens=True,
            ).strip()
            # Keep invalid generations as None so metrics count them as errors.
            predictions.append(
                {
                    "example_id": row["example_id"],
                    "expected_category": row["category"],
                    "raw_output": raw_output,
                    "predicted_category": raw_output if raw_output in LABELS else None,
                }
            )
    return calculate_metrics(predictions, list(LABELS)), predictions


def main() -> int:
    """Run a smoke update or fine-tune and select a checkpoint on validation data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run one update on one training example; do not evaluate or save weights.",
    )
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.gradient_accumulation_steps) < 1:
        parser.error("Epochs, batch size, and gradient accumulation must be positive.")
    if args.learning_rate <= 0:
        parser.error("Learning rate must be positive.")
    # Avoid silently replacing a previous checkpoint at a reused output path.
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.smoke:
        parser.error(
            f"Output directory is not empty: {args.output_dir}. "
            "Choose a new --output-dir to preserve existing checkpoints."
        )

    # Training device is separate from inference; OS environment overrides .env.
    env = {**dotenv_values(PROJECT_ROOT / ".env"), **os.environ}
    requested_device = args.device or str(env.get("TRAINING_DEVICE") or "auto").lower()

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    # Fail early on unsupported devices, before loading the large model.
    device = resolve_device(requested_device, torch)
    settings = ModelSettings.from_env(PROJECT_ROOT / ".env")
    # Read only training and validation data; the test partition is never opened.
    train_rows = read_rows(TRAIN_FILE)
    if args.smoke:
        train_rows = train_rows[:1]
    else:
        validation_rows = read_rows(VALIDATION_FILE)

    # Seed Python and PyTorch so example order and initialization are repeatable.
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    # Reuse the configured base model, revision, cache and offline setting.
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
    # Checkpointing reduces activation memory at the cost of recomputing activations.
    model.gradient_checkpointing_enable()
    model.train()

    # AdamW updates the model weights; inference alone never does this.
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    train_features = tokenize_rows(train_rows, tokenizer, settings)
    if args.smoke:
        # One forward/backward/optimizer step proves that training fits on this device.
        batch = make_batch(train_features[:1], tokenizer, torch)
        batch = {name: tensor.to(device) for name, tensor in batch.items()}
        loss = model(**batch).loss
        loss_value = float(loss.detach().cpu())
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        print(
            json.dumps(
                {
                    "mode": "one_step_smoke",
                    "device": device,
                    "model": settings.model_name,
                    "training_examples": len(train_rows),
                    "optimizer_updates": 1,
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
    best_f1 = -1.0
    history = []
    total_steps = 0
    for epoch in range(1, args.epochs + 1):
        # Training order is reshuffled each epoch, with a fixed seed for repeatability.
        random.shuffle(order)
        model.train()
        epoch_loss = 0.0
        micro_batches = 0
        optimizer.zero_grad(set_to_none=True)
        batch_starts = list(range(0, len(order), args.batch_size))
        for batch_number, start in enumerate(batch_starts):
            batch_features = [
                train_features[index]
                for index in order[start : start + args.batch_size]
            ]
            batch = make_batch(batch_features, tokenizer, torch)
            batch = {name: tensor.to(device) for name, tensor in batch.items()}
            loss = model(**batch).loss
            epoch_loss += float(loss.detach().cpu())
            micro_batches += 1

            # Scale a short final accumulation window correctly as well.
            window_start = (
                batch_number // args.gradient_accumulation_steps
            ) * args.gradient_accumulation_steps
            window_size = min(
                args.gradient_accumulation_steps,
                len(batch_starts) - window_start,
            )
            (loss / window_size).backward()
            window_finished = (
                batch_number + 1
            ) % args.gradient_accumulation_steps == 0 or batch_number + 1 == len(
                batch_starts
            )
            if window_finished:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                total_steps += 1

        # Disable training-only checkpointing while generating validation predictions.
        model.config.use_cache = True
        model.generation_config.use_cache = True
        model.gradient_checkpointing_disable()
        metrics, predictions = evaluate(
            model, tokenizer, validation_rows, settings, device, torch
        )
        model.config.use_cache = False
        model.generation_config.use_cache = False
        model.gradient_checkpointing_enable()
        # Keep per-epoch loss and validation results for the final experiment record.
        record = {
            "epoch": epoch,
            "mean_training_loss": round(epoch_loss / max(micro_batches, 1), 4),
            "optimizer_steps": total_steps,
            "validation_metrics": metrics,
        }
        history.append(record)
        print(json.dumps(record, indent=2))

        # Select by validation macro-F1; validation predictions do not update weights.
        if metrics["macro"]["f1"] > best_f1:
            best_f1 = metrics["macro"]["f1"]
            model.config.use_cache = True
            model.generation_config.use_cache = True
            model.gradient_checkpointing_disable()
            args.output_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(args.output_dir, safe_serialization=True)
            tokenizer.save_pretrained(args.output_dir)
            (args.output_dir / "training_summary.json").write_text(
                json.dumps(
                    {
                        "model_name": settings.model_name,
                        "model_revision": settings.resolved_revision,
                        "device": device,
                        "training_device_requested": requested_device,
                        "seed": args.seed,
                        "epochs_completed": epoch,
                        "optimizer_steps": total_steps,
                        "batch_size": args.batch_size,
                        "gradient_accumulation_steps": args.gradient_accumulation_steps,
                        "learning_rate": args.learning_rate,
                        "training_examples": len(train_rows),
                        "validation_examples": len(validation_rows),
                        "training_file_sha256": hashlib.sha256(
                            TRAIN_FILE.read_bytes()
                        ).hexdigest(),
                        "validation_file_sha256": hashlib.sha256(
                            VALIDATION_FILE.read_bytes()
                        ).hexdigest(),
                        "best_validation_macro_f1": best_f1,
                        "history": history,
                        "best_validation_predictions": predictions,
                        "test_set_loaded": False,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            model.config.use_cache = False
            model.generation_config.use_cache = False
            model.gradient_checkpointing_enable()

    print(f"Best validation macro-F1: {best_f1:.4f}")
    print(f"Selected checkpoint saved to: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
