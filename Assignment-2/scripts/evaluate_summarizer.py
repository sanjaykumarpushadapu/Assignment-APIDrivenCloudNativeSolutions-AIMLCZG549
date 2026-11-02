"""Evaluate a summarizer on reviewed held-out message/reference pairs.

This script is for final evaluation, not tuning. It reports lexical overlap and
preserves each output for a human review of completeness and faithfulness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "test" / "summarization_evaluation_candidate.jsonl"
TEAM_REVIEWERS = {
    "Sanjay",
    "Pushadapu Sanjay Kumar",
    "Sathish Krishnan V",
    "Chezrla Raga Suma",
    "Bhuvnesh Mishra",
}
sys.path.insert(0, str(ROOT / "backend" / "src"))

from diabetes_support.infrastructure.model_settings import ModelSettings  # noqa: E402
from diabetes_support.infrastructure.seq2seq_summarizer import (  # noqa: E402
    build_summary_prompt,
)


def read_reviewed_examples(path: Path) -> list[dict[str, Any]]:
    """Load test pairs only after human review and approval."""
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"The summary evaluation file is empty: {path}")

    # Keep held-out references away from training, prompt selection and tuning.
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        required = {
            "example_id",
            "message",
            "summary",
            "essential_facts",
            "review_status",
            "reviewer",
            "reviewed_on",
            "use_for_tuning",
        }
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Example {row_number} is missing: {sorted(missing)}")
        if row["example_id"] in seen_ids:
            raise ValueError(f"Duplicate example ID: {row['example_id']}")
        seen_ids.add(row["example_id"])
        if (
            row["review_status"] != "approved"
            or row["reviewer"] not in TEAM_REVIEWERS
            or not row["reviewed_on"]
        ):
            raise ValueError(
                f"{row['example_id']} is not approved by a named human reviewer."
            )
        if row["use_for_tuning"] is not False:
            raise ValueError(f"{row['example_id']} must remain unused for tuning.")
        if not row["message"].strip() or not row["summary"].strip():
            raise ValueError(f"Empty message or summary in {row['example_id']}.")
        if not isinstance(row["essential_facts"], list) or not row["essential_facts"]:
            raise ValueError(f"Missing essential facts in {row['example_id']}.")
    return rows


def rouge_l_f1(reference: str, prediction: str) -> float:
    """Calculate token-level ROUGE-L F1 for one reference and output."""
    expected, actual = reference.casefold().split(), prediction.casefold().split()
    if not expected or not actual:
        return 0.0
    previous = [0] * (len(actual) + 1)
    for word in expected:
        current = [0]
        for index, candidate in enumerate(actual, start=1):
            current.append(
                previous[index - 1] + 1
                if word == candidate
                else max(previous[index], current[index - 1])
            )
        previous = current
    overlap = previous[-1]
    precision = overlap / len(actual)
    recall = overlap / len(expected)
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def resolve_model_name(value: str | None, default: str) -> tuple[str, str | None]:
    """Resolve a local checkpoint path while leaving Hub model IDs unchanged."""
    selected = value or default
    path = Path(selected).expanduser()
    if path.is_absolute() or selected.startswith("./") or (ROOT / path).exists():
        return str((ROOT / path).resolve() if not path.is_absolute() else path), None
    return selected, None


def evaluate_model(
    rows: list[dict[str, Any]], settings: ModelSettings, device: str
) -> dict[str, Any]:
    """Generate summaries with application prompt and decoding settings."""
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        settings.model_name,
        revision=settings.resolved_revision,
        cache_dir=str(settings.cache_dir),
        local_files_only=settings.local_files_only,
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(
        settings.model_name,
        revision=settings.resolved_revision,
        cache_dir=str(settings.cache_dir),
        local_files_only=settings.local_files_only,
        use_safetensors=True,
    ).to(device)
    model.eval()

    results = []
    with torch.inference_mode():
        for index, row in enumerate(rows, start=1):
            encoded = tokenizer(
                build_summary_prompt(row["message"]),
                return_tensors="pt",
                truncation=True,
                max_length=settings.max_input_tokens,
            ).to(device)
            tokens = model.generate(
                **encoded,
                max_new_tokens=settings.summary_max_new_tokens,
                do_sample=False,
                num_beams=4,
                no_repeat_ngram_size=3,
            )[0]
            prediction = tokenizer.decode(tokens, skip_special_tokens=True).strip()
            score = rouge_l_f1(row["summary"], prediction)
            print(f"[{index}/{len(rows)}] {row['example_id']} complete", flush=True)
            results.append(
                {
                    "example_id": row["example_id"],
                    "category": row["category"],
                    "message": row["message"],
                    "reference_summary": row["summary"],
                    "essential_facts": row["essential_facts"],
                    "prediction": prediction,
                    "rouge_l_f1": round(score, 4),
                    "human_all_essential_facts_retained": None,
                    "human_unsupported_facts_added": None,
                    "reviewer_notes": None,
                }
            )

    scores = [row["rouge_l_f1"] for row in results]
    ratios = [
        len(row["prediction"].split()) / max(len(row["message"].split()), 1)
        for row in results
    ]
    return {
        "model": settings.display_name,
        "model_revision": settings.resolved_revision,
        "device": device,
        "example_count": len(results),
        "mean_rouge_l_f1": round(sum(scores) / len(scores), 4),
        "mean_output_input_word_ratio": round(sum(ratios) / len(ratios), 4),
        "human_review_required": True,
        "results": results,
    }


def main() -> int:
    """Run one checkpoint against the approved test set and save raw results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        help="Hub model ID or local checkpoint path; defaults to .env summarizer.",
    )
    parser.add_argument("--device", choices=("cpu", "mps", "cuda", "auto"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    # Fail before loading model weights if the held-out set is not approved.
    rows = read_reviewed_examples(DATASET_PATH)
    base_settings = ModelSettings.from_env(ROOT / ".env", component="summarizer")
    model_name, model_revision = resolve_model_name(
        args.model, base_settings.model_name
    )
    settings = ModelSettings(
        **{
            **base_settings.__dict__,
            "model_name": model_name,
            "model_revision": model_revision,
        }
    )
    device = args.device or settings.device
    if device == "auto":
        import torch

        device = (
            "cuda"
            if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available() else "cpu"
        )

    result = evaluate_model(rows, settings, device)
    result.update(
        {
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset": str(DATASET_PATH.relative_to(ROOT)),
            "dataset_sha256": hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest(),
            "test_used_for_training_or_model_selection": False,
        }
    )
    slug = re.sub(r"[^a-z0-9]+", "-", settings.display_name.lower()).strip("-")
    output_path = args.output or ROOT / "artifacts" / "evaluation" / (
        f"summarization_test_{slug}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key != "results"
            },
            indent=2,
        )
    )
    print(f"Saved case-level outcomes to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
