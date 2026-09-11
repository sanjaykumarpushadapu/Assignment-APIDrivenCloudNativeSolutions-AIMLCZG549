"""Single command-line entry point for ingestion and pipeline stages."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .ingestion import ingest
from .runner import run


# ============================================================
# DEFAULT PATHS
# ============================================================

DEFAULT_DATASET_PATH = (
    "data/raw/diabetes_012_health_indicators_BRFSS2015.csv"
)

DEFAULT_MODEL_READY_PATH = Path(
    os.environ.get(
        "DIABETES_MODEL_READY_PATH",
        "data/processed/diabetes_model_ready.csv",
    )
)

DEFAULT_REPORT_DIR = Path(
    os.environ.get(
        "DIABETES_REPORT_DIR",
        "data/outputs",
    )
)


# ============================================================
# BUILD COMMAND-LINE PARSER
# ============================================================

def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="python -m diabetes_risk.pipeline",
        description="Diabetes risk data pipeline commands.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ========================================================
    # INGESTION
    # ========================================================

    ingest_parser = subparsers.add_parser(
        "ingest",
        help=(
            "Validate the raw dataset and append "
            "an ingestion manifest entry."
        ),
    )

    ingest_parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            os.environ.get(
                "DIABETES_DATASET_PATH",
                DEFAULT_DATASET_PATH,
            )
        ),
    )

    ingest_parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "data/raw/ingestion_manifest.json"
        ),
    )

    # ========================================================
    # PERSON 2 - DATA QUALITY / PREPROCESSING / EDA
    # ========================================================

    run_parser = subparsers.add_parser(
        "run",
        help=(
            "Run data quality, preprocessing "
            "and automated EDA."
        ),
    )

    run_parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=None,
        help=(
            "Input CSV; defaults to "
            "DIABETES_DATASET_PATH."
        ),
    )

    run_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )

    run_parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
    )

    run_parser.add_argument(
        "--target-column",
        default=None,
    )

    run_parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help=(
            "Do not remove exact duplicate records."
        ),
    )

    # ========================================================
    # PERSON 3 - RANDOM FOREST
    # ========================================================

    subparsers.add_parser(
        "randomforestclassifier",
        help=(
            "Train Random Forest classifier and "
            "generate feature importance report."
        ),
    )

    # ========================================================
    # PERSON 3 - MODEL EVALUATION
    # ========================================================

    subparsers.add_parser(
        "model_evaluation",
        help=(
            "Evaluate and compare Logistic Regression "
            "and Random Forest models."
        ),
    )

    return parser


# ============================================================
# MAIN COMMAND
# ============================================================

def main(argv: list[str] | None = None) -> None:
    """Run the selected pipeline command."""

    load_dotenv()

    parser = _build_parser()
    args = parser.parse_args(argv)

    # ========================================================
    # INGESTION
    # ========================================================

    if args.command == "ingest":

        report = ingest(
            args.source,
            args.manifest,
        )

        print(
            json.dumps(
                report.as_dict(),
                indent=2,
            )
        )

        return

    # ========================================================
    # PERSON 2 - DATA QUALITY / PREPROCESSING / EDA
    # ========================================================

    if args.command == "run":

        input_path = args.input or Path(
            os.environ.get(
                "DIABETES_DATASET_PATH",
                DEFAULT_DATASET_PATH,
            )
        )

        output_dir = args.output_dir or Path(
            os.environ.get(
                "DIABETES_OUTPUT_DIR",
                "data/processed",
            )
        )

        report_dir = args.report_dir or Path(
            os.environ.get(
                "DIABETES_REPORT_DIR",
                "data/outputs",
            )
        )

        target = args.target_column or os.environ.get(
            "DIABETES_TARGET_COLUMN",
            "Diabetes_012",
        )

        summary = run(
            input_path,
            output_dir,
            target_column=target,
            report_dir=report_dir,
            drop_duplicates=not args.keep_duplicates,
        )

        print(
            json.dumps(
                summary,
                indent=2,
                default=str,
            )
        )

        return

    # ========================================================
    # PERSON 3 - RANDOM FOREST
    # ========================================================

    if args.command == "randomforestclassifier":

        from .randomforestclassifier import train_random_forest

        input_path = Path(
            os.environ.get(
                "DIABETES_MODEL_READY_PATH",
                DEFAULT_MODEL_READY_PATH,
            )
        )

        report_dir = Path(
            os.environ.get(
                "DIABETES_REPORT_DIR",
                "data/outputs",
            )
        )

        result = train_random_forest(
            input_path=input_path,
            report_dir=report_dir,
        )

        print(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

        return

    # ========================================================
    # PERSON 3 - MODEL EVALUATION
    # ========================================================

    if args.command == "model_evaluation":

        from .model_evaluation import evaluate_models

        input_path = Path(
            os.environ.get(
                "DIABETES_MODEL_READY_PATH",
                DEFAULT_MODEL_READY_PATH,
            )
        )

        report_dir = Path(
            os.environ.get(
                "DIABETES_REPORT_DIR",
                "data/outputs",
            )
        )

        result = evaluate_models(
            input_path=input_path,
            report_dir=report_dir,
        )

        print(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

        return


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
