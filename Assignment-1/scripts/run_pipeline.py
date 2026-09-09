"""Convenience entry point for running the complete Person-2 pipeline."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from diabetes_risk.pipeline.config import PipelineConfig
from diabetes_risk.pipeline.runner import run


if __name__ == "__main__":
    config = PipelineConfig.from_env()
    result = run(
        config.dataset_path,
        config.processed_dir,
        target_column=config.target_column,
        report_dir=config.output_dir,
    )
    print(json.dumps(result, indent=2, default=str))
