"""Environment/configuration helpers; no cloud SDK dependency."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class PipelineConfig:
    dataset_path: Path
    processed_dir: Path
    output_dir: Path
    execution_dir: Path
    target_column: str = "Diabetes_012"

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        load_dotenv()
        output_dir = Path(os.getenv("DIABETES_OUTPUT_DIR", "data/processed"))
        report_dir = Path(os.getenv("DIABETES_REPORT_DIR", "data/outputs"))
        return cls(
            dataset_path=Path(os.getenv("DIABETES_DATASET_PATH", "data/raw/diabetes_012_health_indicators_BRFSS2015.csv")),
            processed_dir=output_dir,
            output_dir=report_dir,
            execution_dir=report_dir / "execution",
            target_column=os.getenv("DIABETES_TARGET_COLUMN", "Diabetes_012"),
        )
