"""Single command-line entry point for every pipeline stage.

Rather than each stage module (``ingestion.py``, ``runner.py``, and
future stages like an EDA module) defining its own ``main()`` and being
invoked via a different ``python -m diabetes_risk.pipeline.<module>``
path, all stages are wired into one consistent command surface here:

    python -m diabetes_risk.pipeline ingest [--source ...] [--manifest ...]
    python -m diabetes_risk.pipeline run <input.csv> [--output-dir ...]

Each stage's actual logic stays in its own module and is fully testable
and importable on its own (see ``ingestion.ingest()`` and
``runner.run()``) -- this file only parses arguments and dispatches to
them, so adding a new stage later means adding one subcommand here, not
inventing a new invocation pattern.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .ingestion import ingest
from .runner import run

DEFAULT_DATASET_PATH = "data/raw/diabetes_012_health_indicators_BRFSS2015.csv"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m diabetes_risk.pipeline",
        description="Diabetes risk data pipeline commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest", help="Validate the raw dataset and log the result to an ingestion manifest."
    )
    ingest_parser.add_argument(
        "--source",
        type=Path,
        default=Path(os.environ.get("DIABETES_DATASET_PATH", DEFAULT_DATASET_PATH)),
        help="Path to the raw CSV (default: $DIABETES_DATASET_PATH, falling back to the known raw file).",
    )
    ingest_parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/raw/ingestion_manifest.json"),
        help="Path to the ingestion manifest to append to.",
    )

    run_parser = subparsers.add_parser("run", help="Preprocess an input CSV and write the cleaned output.")
    run_parser.add_argument("input", type=Path, help="Path to the input CSV file")
    run_parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    run_parser.add_argument(
        "--target-column",
        default=None,
        help="Target column to exclude from normalization (e.g. Diabetes_012).",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    # A local .env (see .env.example) is loaded once here, at the single
    # entry point, so every subcommand picks up its variables the same way.
    load_dotenv()

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest":
        report = ingest(args.source, args.manifest)
        print(json.dumps(report.as_dict(), indent=2))
    elif args.command == "run":
        summary = run(args.input, args.output_dir, target_column=args.target_column)
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
