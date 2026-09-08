import json

import pandas as pd

from diabetes_risk.pipeline.runner import run


def test_run_writes_processed_csv_and_summary(tmp_path) -> None:
    input_path = tmp_path / "input.csv"
    pd.DataFrame({"Age": [20, 40, None], "Diabetes_012": [0, 1, 0]}).to_csv(input_path, index=False)
    output_dir = tmp_path / "out"

    summary = run(input_path, output_dir, target_column="Diabetes_012")

    assert (output_dir / "processed.csv").exists()
    assert (output_dir / "run_summary.json").exists()
    assert summary["input_rows"] == 3
    assert summary["output_rows"] == 3
    # the target column is excluded from normalization and untouched by imputation
    assert summary["missing_values_after"] == {}

    written_summary = json.loads((output_dir / "run_summary.json").read_text())
    assert written_summary == summary
