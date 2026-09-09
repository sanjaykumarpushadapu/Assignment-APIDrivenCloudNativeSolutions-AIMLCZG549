"""End-to-end Person-2 pipeline runner.

The runner is storage/orchestration neutral: local paths are accepted as Path
objects and can later be adapted to cloud object storage by the deployment layer.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .data_quality import run_data_quality
from .eda import generate_eda
from .logging_utils import create_run_id, utc_now, write_execution_log
from .preprocessing import preprocess

LOGGER = logging.getLogger(__name__)


def run(
    input_path: Path,
    output_dir: Path,
    target_column: str | None = None,
    *,
    report_dir: Path | None = None,
    drop_duplicates: bool = True,
) -> dict[str, Any]:
    """Execute data quality, preprocessing and EDA and persist all artifacts."""
    started = utc_now()
    run_id = create_run_id()
    target = target_column or "Diabetes_012"
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = report_dir or output_dir.parent / "outputs"
    quality_dir = reports / "quality"
    eda_dir = reports / "eda"
    execution_dir = reports / "execution"

    summary: dict[str, Any] = {
        "run_id": run_id,
        "started_at": started.isoformat(),
        "input_path": str(input_path),
        "target_column": target,
        "status": "RUNNING",
        "errors": [],
        "warnings": [],
    }

    try:
        if not input_path.exists():
            raise FileNotFoundError(f"Input dataset not found: {input_path}")

        frame = pd.read_csv(input_path)
        summary["input_rows"] = int(len(frame))
        summary["input_columns"] = int(len(frame.columns))

        quality = run_data_quality(frame, target, strict_schema=True)
        quality_dir.mkdir(parents=True, exist_ok=True)
        (quality_dir / "data_quality.json").write_text(json.dumps(quality, indent=2, default=str), encoding="utf-8")
        pd.DataFrame(quality["missing_values"]).to_csv(quality_dir / "missing_values.csv", index=False)
        summary["data_quality"] = quality

        processed, preprocessing_report = preprocess(
            frame, target_column=target, drop_duplicates=drop_duplicates, standardize=False
        )
        model_ready, model_ready_report = preprocess(
            frame, target_column=target, drop_duplicates=drop_duplicates, standardize=True
        )
        processed_path = output_dir / "diabetes_cleaned.csv"
        model_ready_path = output_dir / "diabetes_model_ready.csv"
        processed.to_csv(processed_path, index=False)
        model_ready.to_csv(model_ready_path, index=False)
        (output_dir / "preprocessing_report.json").write_text(
            json.dumps({**preprocessing_report, "model_ready": model_ready_report}, indent=2, default=str), encoding="utf-8"
        )

        normalized_target = target.strip().lower().replace(" ", "_")
        eda_metadata = generate_eda(processed, eda_dir, target_column=normalized_target)
        summary.update(
            {
                "output_rows": int(len(processed)),
                "records_processed": int(len(frame)),
                "records_output": int(len(processed)),
                "duplicates_detected": int(preprocessing_report["duplicates_detected"]),
                "processed_data_path": str(processed_path),
                "model_ready_data_path": str(model_ready_path),
                "preprocessing_report_path": str(output_dir / "preprocessing_report.json"),
                "eda_outputs": eda_metadata,
                "warnings": [] if quality["quality_status"] == "PASS" else ["One or more non-fatal data-quality checks require review."],
                "status": "SUCCESS",
            }
        )
    except Exception as exc:  # noqa: BLE001 - execution summary must capture failures
        LOGGER.exception("Pipeline run %s failed", run_id)
        summary["status"] = "FAILED"
        summary["errors"] = [f"{type(exc).__name__}: {exc}"]
        raise
    finally:
        ended = utc_now()
        summary["ended_at"] = ended.isoformat()
        summary["duration_seconds"] = (ended - started).total_seconds()
        log_path = execution_dir / f"run_{summary['run_id']}.json"
        summary["execution_log_path"] = str(log_path)
        write_execution_log(summary, execution_dir)
        (execution_dir / "latest_run.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )

    return summary
