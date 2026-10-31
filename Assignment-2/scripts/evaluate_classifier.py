"""Evaluate a classifier on validation, or explicitly run final test scoring.

The default mode reads only validation data. ``--final-test`` enables one final
test-set evaluation after the model and prompt are frozen. The script never
trains or tunes the model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_FILE = (
    PROJECT_ROOT / "data" / "validation" / "classification_validation.jsonl"
)
TEST_FILE = PROJECT_ROOT / "data" / "test" / "classification_test.jsonl"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "artifacts"
    / "evaluation"
    / "classification_baseline_validation.json"
)
DEFAULT_TEST_OUTPUT = (
    PROJECT_ROOT / "artifacts" / "evaluation" / "classification_final_test.json"
)

# Allow running this script directly without installing the package first.
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from diabetes_support.infrastructure.model_settings import ModelSettings  # noqa: E402
from diabetes_support.infrastructure.seq2seq_classifier import (  # noqa: E402
    LABELS,
    Seq2SeqClassifier,
)


def read_classification_rows(path: Path) -> list[dict[str, str]]:
    """Read a classification partition and check its IDs, messages and labels."""
    # Parse each nonblank JSONL row as one model input and expected category.
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if not rows:
        raise ValueError(f"The validation file is empty: {path}")

    # Validate IDs and gold labels before asking the model for predictions.
    required_fields = {"example_id", "message", "category"}
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        missing = required_fields - row.keys()
        if missing:
            raise ValueError(f"Row {row_number} is missing fields: {sorted(missing)}")
        if row["category"] not in LABELS:
            raise ValueError(
                f"Row {row_number} has an unsupported category: {row['category']}"
            )
        if not row["message"].strip():
            raise ValueError(f"Row {row_number} has an empty message.")
        if row["example_id"] in seen_ids:
            raise ValueError(f"Duplicate example_id: {row['example_id']}")
        seen_ids.add(row["example_id"])
    return rows


def calculate_metrics(
    rows: list[dict[str, Any]], categories: list[str]
) -> dict[str, Any]:
    """Calculate accuracy and per-class and macro precision/recall/F1."""
    # Rows are actual labels; columns are model predictions, including INVALID outputs.
    confusion = {
        label: {column: 0 for column in [*categories, "INVALID"]}
        for label in categories
    }
    correct = 0
    per_class: dict[str, dict[str, float | int]] = {}

    for row in rows:
        actual = row["expected_category"]
        predicted = row["predicted_category"] or "INVALID"
        confusion[actual][predicted] += 1
        correct += actual == predicted

    for label in categories:
        # Invalid outputs miss the actual class and are counted separately below.
        true_positive = confusion[label][label]
        actual_count = sum(confusion[label].values())
        predicted_count = sum(confusion[actual][label] for actual in categories)
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / actual_count if actual_count else 0.0
        f1 = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
        per_class[label] = {
            "support": actual_count,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    # Macro scores weight all five classes equally, regardless of example count.
    macro = {
        metric: round(
            sum(scores[metric] for scores in per_class.values()) / len(categories), 4
        )
        for metric in ("precision", "recall", "f1")
    }
    # Count outputs that do not exactly match one of the allowed category names.
    invalid_count = sum(row["predicted_category"] is None for row in rows)
    return {
        "count": len(rows),
        "accuracy": round(correct / len(rows), 4),
        "macro": macro,
        "per_class": per_class,
        "invalid_output_count": invalid_count,
        "invalid_output_rate": round(invalid_count / len(rows), 4),
        "confusion_matrix": confusion,
    }


def main() -> int:
    """Run validation scoring or an explicitly requested final test evaluation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--final-test",
        action="store_true",
        help=(
            "Load the final test partition for one final score after model and "
            "prompt choices are frozen. Do not use its results for tuning."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Where to save results; defaults depend on the selected partition.",
    )
    args = parser.parse_args()

    # Only the explicit final-test flag permits opening the held-out test file.
    dataset_path = TEST_FILE if args.final_test else VALIDATION_FILE
    default_output = DEFAULT_TEST_OUTPUT if args.final_test else DEFAULT_OUTPUT
    output_path = args.output or default_output
    rows = read_classification_rows(dataset_path)
    settings = ModelSettings.from_env(PROJECT_ROOT / ".env")
    classifier = Seq2SeqClassifier(settings)

    predictions: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        # Use the application classifier so baseline inference matches the real prompt.
        result = classifier.classify(row["message"])
        predictions.append(
            {
                "example_id": row["example_id"],
                "message": row["message"],
                "expected_category": row["category"],
                "raw_output": result["raw_output"],
                "predicted_category": result["category"],
                "valid_category": result["valid_category"],
            }
        )
        category = result["category"] or "INVALID"
        print(f"[{index}/{len(rows)}] {row['example_id']}: {category}")

    # Hash the selected partition so the score can be tied to its exact contents.
    dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    categories = list(LABELS)
    output = {
        "evaluation_type": "final_test" if args.final_test else "validation_evaluation",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path.relative_to(PROJECT_ROOT)),
        "dataset_sha256": dataset_hash,
        "prompt_source": "Seq2SeqClassifier.classify",
        "generation": {
            "do_sample": False,
            "max_new_tokens": settings.classification_max_new_tokens,
            "max_input_tokens": settings.max_input_tokens,
        },
        "model": {
            "name": settings.model_name,
            "revision": settings.resolved_revision,
            "device": classifier.runtime.device,
        },
        "metrics": calculate_metrics(predictions, categories),
        "predictions": predictions,
        "test_set_loaded": args.final_test,
        "weights_updated_during_inference": False,
    }

    # Keep machine-readable predictions and metrics for the report and later comparison.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {"metrics": output["metrics"], "saved_to": str(output_path)}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
