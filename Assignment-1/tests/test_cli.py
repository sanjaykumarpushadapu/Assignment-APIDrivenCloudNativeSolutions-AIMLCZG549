import json

import pandas as pd

from diabetes_risk.pipeline.cli import main
from diabetes_risk.pipeline.ingestion import EXPECTED_COLUMNS


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame({column: [0.0, 1.0] for column in EXPECTED_COLUMNS})


def test_cli_ingest_subcommand(tmp_path, capsys) -> None:
    source = tmp_path / "raw.csv"
    _valid_frame().to_csv(source, index=False)
    manifest = tmp_path / "manifest.json"

    main(["ingest", "--source", str(source), "--manifest", str(manifest)])

    output = json.loads(capsys.readouterr().out)
    assert output["target_present"] is True
    assert manifest.exists()


def test_cli_run_subcommand(tmp_path, capsys) -> None:
    input_path = tmp_path / "input.csv"
    pd.DataFrame({"Age": [20, 40], "Diabetes_012": [0, 1]}).to_csv(input_path, index=False)
    output_dir = tmp_path / "out"

    main(["run", str(input_path), "--output-dir", str(output_dir), "--target-column", "Diabetes_012"])

    output = json.loads(capsys.readouterr().out)
    assert output["input_rows"] == 2
    assert (output_dir / "processed.csv").exists()
