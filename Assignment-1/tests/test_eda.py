import pandas as pd

from diabetes_risk.pipeline.eda import generate_eda


def test_generate_eda_writes_required_outputs(tmp_path) -> None:
    frame = pd.DataFrame(
        {
            "Diabetes_012": [0, 1, 2, 2],
            "BMI": [20.0, 25.0, 30.0, 35.0],
            "Age": [2, 5, 8, 11],
            "HighBP": [0, 1, 1, 1],
            "HighChol": [0, 0, 1, 1],
            "PhysActivity": [1, 1, 0, 0],
            "GenHlth": [1, 2, 4, 5],
            "CholCheck": [1, 1, 1, 1],
            "Smoker": [0, 0, 1, 1],
        }
    )
    metadata = generate_eda(frame, tmp_path)
    for name in ["summary_statistics.csv", "missing_value_summary.csv", "target_distribution.csv", "target_distribution.png", "correlation_matrix.csv", "binned_features.csv", "eda_metadata.json"]:
        assert (tmp_path / name).exists(), name
    assert metadata["target_column"] == "diabetes_012"
    assert len(metadata["feature_distribution_charts"]) == 8
