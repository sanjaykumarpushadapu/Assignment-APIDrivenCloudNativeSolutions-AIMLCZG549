import json

import pandas as pd

from diabetes_risk.pipeline.runner import run


def test_run_writes_cleaned_eda_and_execution_outputs(tmp_path) -> None:
    input_path = tmp_path / "input.csv"
    columns = {
        "Diabetes_012": [0.0, 1.0, 1.0, 1.0], "HighBP": [0.0, 1.0, 1.0, 1.0],
        "HighChol": [0.0, 0.0, 1.0, 1.0], "CholCheck": [1.0, 1.0, 1.0, 1.0],
        "BMI": [20.0, 30.0, 30.0, 25.0], "Smoker": [0.0, 0.0, 1.0, 1.0],
        "Stroke": [0.0, 0.0, 0.0, 0.0], "HeartDiseaseorAttack": [0.0, 0.0, 1.0, 1.0],
        "PhysActivity": [1.0, 1.0, 0.0, 0.0], "Fruits": [1.0, 1.0, 0.0, 0.0],
        "Veggies": [1.0, 1.0, 0.0, 1.0], "HvyAlcoholConsump": [0.0, 0.0, 1.0, 0.0],
        "AnyHealthcare": [1.0, 1.0, 1.0, 1.0], "NoDocbcCost": [0.0, 0.0, 1.0, 0.0],
        "GenHlth": [1.0, 2.0, 4.0, 5.0], "MentHlth": [0.0, 2.0, 5.0, 0.0],
        "PhysHlth": [0.0, 3.0, 7.0, 0.0], "DiffWalk": [0.0, 0.0, 1.0, 1.0],
        "Sex": [0.0, 1.0, 1.0, 0.0], "Age": [2.0, 5.0, 8.0, 11.0],
        "Education": [4.0, 5.0, 3.0, 6.0], "Income": [5.0, 6.0, 2.0, 8.0],
    }
    frame = pd.DataFrame(columns)
    frame.iloc[3] = frame.iloc[2]
    frame.to_csv(input_path, index=False)
    output_dir = tmp_path / "processed"
    report_dir = tmp_path / "outputs"

    summary = run(input_path, output_dir, target_column="Diabetes_012", report_dir=report_dir)

    assert summary["status"] == "SUCCESS"
    assert summary["input_rows"] == 4
    assert summary["output_rows"] == 3
    assert summary["records_processed"] == 4
    assert (output_dir / "diabetes_cleaned.csv").exists()
    assert (output_dir / "diabetes_model_ready.csv").exists()
    assert (output_dir / "preprocessing_report.json").exists()
    assert (report_dir / "quality" / "data_quality.json").exists()
    assert (report_dir / "eda" / "correlation_matrix.csv").exists()
    log_path = report_dir / "execution" / f"run_{summary['run_id']}.json"
    assert log_path.exists()
    assert json.loads(log_path.read_text())["status"] == "SUCCESS"
