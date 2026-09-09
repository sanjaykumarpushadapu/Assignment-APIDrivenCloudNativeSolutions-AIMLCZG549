"""Single command-line entry point for ingestion and Person-2 pipeline stages."""
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
    parser = argparse.ArgumentParser(prog="python -m diabetes_risk.pipeline", description="Diabetes risk data pipeline commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Validate the raw dataset and append an ingestion manifest entry.")
    ingest_parser.add_argument("--source", type=Path, default=Path(os.environ.get("DIABETES_DATASET_PATH", DEFAULT_DATASET_PATH)))
    ingest_parser.add_argument("--manifest", type=Path, default=Path("data/raw/ingestion_manifest.json"))

    run_parser = subparsers.add_parser("run", help="Run data quality, preprocessing and automated EDA.")
    run_parser.add_argument("input", type=Path, nargs="?", default=None, help="Input CSV; defaults to DIABETES_DATASET_PATH.")
    run_parser.add_argument("--output-dir", type=Path, default=None)
    run_parser.add_argument("--report-dir", type=Path, default=None)
    run_parser.add_argument("--target-column", default=None)
    run_parser.add_argument("--keep-duplicates", action="store_true", help="Do not remove exact duplicate records.")
    return parser


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest":
        report = ingest(args.source, args.manifest)
        print(json.dumps(report.as_dict(), indent=2))
        return

    if args.command == "run":
        input_path = args.input or Path(os.environ.get("DIABETES_DATASET_PATH", DEFAULT_DATASET_PATH))
        output_dir = args.output_dir or Path(os.environ.get("DIABETES_OUTPUT_DIR", "data/processed"))
        report_dir = args.report_dir or Path(os.environ.get("DIABETES_REPORT_DIR", "data/outputs"))
        target = args.target_column or os.environ.get("DIABETES_TARGET_COLUMN", "Diabetes_012")
        summary = run(
            input_path,
            output_dir,
            target_column=target,
            report_dir=report_dir,
            drop_duplicates=not args.keep_duplicates,
        )
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
