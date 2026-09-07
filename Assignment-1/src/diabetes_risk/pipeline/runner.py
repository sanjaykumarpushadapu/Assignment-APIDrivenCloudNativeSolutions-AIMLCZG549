import argparse
import json
from pathlib import Path

import pandas as pd

from .preprocessing import preprocess


def run(input_path: Path, output_dir: Path) -> dict[str, object]:
    """Run the local pipeline and write a processed CSV plus a summary."""
    frame = pd.read_csv(input_path)
    processed = preprocess(frame)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_dir / "processed.csv", index=False)
    summary = {
        "input_rows": len(frame),
        "output_rows": len(processed),
        "columns": list(processed.columns),
        "missing_values": int(processed.isna().sum().sum()),
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the diabetes risk data pipeline.")
    parser.add_argument("input", type=Path, help="Path to the input CSV file")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output_dir), indent=2))