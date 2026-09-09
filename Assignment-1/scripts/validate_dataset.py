"""Validate the approved dataset using the Person-2 data-quality contract."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from diabetes_risk.pipeline.config import PipelineConfig
from diabetes_risk.pipeline.data_quality import run_data_quality


if __name__ == "__main__":
    config = PipelineConfig.from_env()
    frame = pd.read_csv(config.dataset_path)
    report = run_data_quality(frame, config.target_column, strict_schema=True)
    print(json.dumps(report, indent=2, default=str))
