"""Score the reviewed RAG evaluation set against a running local API.

This script is for final evaluation only. It refuses candidate/unreviewed data,
does not change model or retrieval settings, and leaves answer-quality judgments
for a human reviewer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "test" / "rag_evaluation_candidate.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "evaluation" / "rag_test_results.json"
TEAM_REVIEWERS = {
    "Sanjay",
    "Pushadapu Sanjay Kumar",
    "Sathish Krishnan V",
    "Chezrla Raga Suma",
    "Bhuvnesh Mishra",
}


def read_reviewed_cases(path: Path) -> list[dict[str, Any]]:
    """Load cases only after a named human reviewer approves the held-out set."""
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"The RAG evaluation file is empty: {path}")

    # Keep development and unreviewed questions out of final evaluation runs.
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        required = {
            "case_id",
            "question",
            "expected_action",
            "expected_source_chunk_ids",
            "answer_key",
            "review_status",
            "reviewer",
            "reviewed_on",
            "use_for_tuning",
        }
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Case {row_number} is missing fields: {sorted(missing)}")
        if row["case_id"] in seen_ids:
            raise ValueError(f"Duplicate case ID: {row['case_id']}")
        seen_ids.add(row["case_id"])
        if (
            row["review_status"] != "approved"
            or row["reviewer"] not in TEAM_REVIEWERS
            or not row["reviewed_on"]
        ):
            raise ValueError(
                f"{row['case_id']} is not approved by a named human reviewer."
            )
        if row["use_for_tuning"] is not False:
            raise ValueError(f"{row['case_id']} must remain unused for tuning.")
        if row["expected_action"] not in {"answer_from_corpus", "refer_to_staff"}:
            raise ValueError(f"Unsupported expected_action in {row['case_id']}.")
        if not row["question"].strip():
            raise ValueError(f"Empty question in {row['case_id']}.")
    return rows


def post_question(api_url: str, route: str, question: str) -> dict[str, Any]:
    """Post one question to retrieve or chat without changing runtime settings."""
    request = Request(
        f"{api_url.rstrip('/')}/{route.lstrip('/')}",
        data=json.dumps({"question": question}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(
            f"API request failed for {request.full_url}: {error}"
        ) from error
    if not isinstance(result, dict):
        raise ValueError(f"API returned a non-object response for {request.full_url}.")
    return result


def evaluate_cases(
    api_url: str, cases: list[dict[str, Any]]
) -> dict[str, Any]:
    """Collect retrieval and abstention outcomes without auto-scoring prose."""
    results = []
    for index, case in enumerate(cases, start=1):
        retrieved = post_question(api_url, "retrieve", case["question"])
        chatted = post_question(api_url, "chat", case["question"])
        source_ids = [source["chunk_id"] for source in retrieved.get("sources", [])]
        expected_ids = case["expected_source_chunk_ids"]
        expected_abstention = case["expected_action"] == "refer_to_staff"
        observed_abstention = bool(chatted.get("abstained"))
        print(f"[{index}/{len(cases)}] {case['case_id']} complete")
        results.append(
            {
                "case_id": case["case_id"],
                "question": case["question"],
                "expected_action": case["expected_action"],
                "expected_source_chunk_ids": expected_ids,
                "answer_key": case["answer_key"],
                "retrieved_source_chunk_ids": source_ids,
                "retrieval_hit_at_k": bool(set(expected_ids) & set(source_ids))
                if expected_ids
                else None,
                "observed_abstained": observed_abstention,
                "expected_abstention": expected_abstention,
                "decision_matches_expectation": (
                    observed_abstention == expected_abstention
                ),
                "answer": chatted.get("answer"),
                "chat_sources": chatted.get("sources", []),
                "human_answer_supported": None,
                "human_citation_correct": None,
                "reviewer_notes": None,
            }
        )

    answerable = [row for row in results if row["expected_source_chunk_ids"]]
    referrals = [row for row in results if row["expected_abstention"]]
    correctly_referred = sum(row["observed_abstained"] for row in referrals)
    answerable_abstentions = sum(
        row["observed_abstained"] for row in answerable
    )
    return {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_only": True,
        "api_url": api_url,
        "case_count": len(results),
        "answerable_case_count": len(answerable),
        "referral_case_count": len(referrals),
        "retrieval_hit_rate_at_k": (
            sum(row["retrieval_hit_at_k"] for row in answerable) / len(answerable)
            if answerable
            else None
        ),
        "abstention_decision_accuracy": (
            sum(row["decision_matches_expectation"] for row in results) / len(results)
        ),
        "referral_recall": (
            correctly_referred / len(referrals) if referrals else None
        ),
        "answerable_false_abstention_rate": (
            answerable_abstentions / len(answerable) if answerable else None
        ),
        "human_review_required_for_answer_support_and_citations": True,
        "results": results,
    }


def main() -> int:
    """Run the reviewed, held-out cases once and save the raw outcomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-url", default="http://127.0.0.1:8001", help="Running API base URL."
    )
    parser.add_argument(
        "--dataset", type=Path, default=DATASET_PATH, help="Approved evaluation JSONL."
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="JSON results path."
    )
    args = parser.parse_args()
    dataset_path = args.dataset.resolve()

    # Never call the model while the question set is still a draft.
    cases = read_reviewed_cases(dataset_path)
    result = evaluate_cases(args.api_url, cases)
    result["dataset"] = str(dataset_path.relative_to(PROJECT_ROOT))
    result["dataset_sha256"] = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
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
    print(f"Saved case-level outcomes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
