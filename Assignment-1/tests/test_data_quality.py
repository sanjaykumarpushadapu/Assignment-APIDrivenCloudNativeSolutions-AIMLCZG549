import pandas as pd
import pytest

from diabetes_risk.pipeline.data_quality import DataQualityError, run_data_quality
from diabetes_risk.pipeline.ingestion import EXPECTED_COLUMNS


def valid_frame(rows: int = 2) -> pd.DataFrame:
    values = {
        "Diabetes_012": [0.0, 1.0], "HighBP": [0.0, 1.0], "HighChol": [0.0, 1.0],
        "CholCheck": [1.0, 1.0], "BMI": [20.0, 30.0], "Smoker": [0.0, 1.0],
        "Stroke": [0.0, 1.0], "HeartDiseaseorAttack": [0.0, 1.0], "PhysActivity": [1.0, 0.0],
        "Fruits": [1.0, 0.0], "Veggies": [1.0, 0.0], "HvyAlcoholConsump": [0.0, 1.0],
        "AnyHealthcare": [1.0, 1.0], "NoDocbcCost": [0.0, 1.0], "GenHlth": [1.0, 5.0],
        "MentHlth": [0.0, 30.0], "PhysHlth": [0.0, 30.0], "DiffWalk": [0.0, 1.0],
        "Sex": [0.0, 1.0], "Age": [2.0, 11.0], "Education": [1.0, 6.0], "Income": [1.0, 8.0],
    }
    return pd.DataFrame(values)


def test_quality_reports_duplicates_and_no_missing_values() -> None:
    frame = pd.concat([valid_frame(), valid_frame().iloc[[0]]], ignore_index=True)
    report = run_data_quality(frame)
    assert report["rows"] == 3
    assert report["duplicate_count"] == 1
    assert report["missing_value_total"] == 0
    assert report["quality_status"] == "PASS_WITH_WARNINGS"


def test_quality_detects_invalid_target() -> None:
    frame = valid_frame()
    frame.loc[0, "Diabetes_012"] = 7
    report = run_data_quality(frame)
    assert report["target_validation"]["invalid_values"] == [7.0]
    assert report["quality_status"] == "WARN"


def test_quality_rejects_missing_expected_column_in_strict_mode() -> None:
    frame = valid_frame().drop(columns=["BMI"])
    with pytest.raises(DataQualityError):
        run_data_quality(frame, strict_schema=True)


def test_quality_detects_invalid_binary_value() -> None:
    frame = valid_frame()
    frame.loc[0, "HighBP"] = 2
    report = run_data_quality(frame)
    assert report["binary_value_validation"]["HighBP"]["invalid_values"] == [2.0]
