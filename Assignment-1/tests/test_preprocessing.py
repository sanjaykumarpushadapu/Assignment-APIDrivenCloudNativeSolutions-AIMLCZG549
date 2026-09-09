import pandas as pd

from diabetes_risk.pipeline.preprocessing import preprocess


def test_preprocess_normalizes_columns_removes_duplicates_and_imputes() -> None:
    frame = pd.DataFrame(
        {
            " Age ": [20, 40, 40],
            "BMI": [20.0, 30.0, 30.0],
            "Risk Group": ["low", "high", "high"],
            "Diabetes_012": [0, 1, 1],
        }
    )
    result, report = preprocess(frame, target_column="Diabetes_012")
    assert list(result.columns) == ["age", "bmi", "diabetes_012", "risk_group_high", "risk_group_low"]
    assert len(result) == 2
    assert result["bmi"].isna().sum() == 0
    assert "risk_group_high" in result.columns
    assert "risk_group_low" in result.columns
    assert report["duplicates_detected"] == 1
    assert report["duplicates_removed"] == 1


def test_binary_features_are_not_unnecessarily_scaled() -> None:
    frame = pd.DataFrame({"HighBP": [0, 1], "BMI": [20.0, 30.0], "Diabetes_012": [0, 2]})
    result, _ = preprocess(frame, target_column="Diabetes_012")
    assert result["highbp"].tolist() == [0, 1]
    assert abs(result["bmi"].mean()) < 1e-12
    assert result["diabetes_012"].tolist() == [0, 2]


def test_empty_categorical_and_numeric_missing_reports_are_complete() -> None:
    frame = pd.DataFrame({"Age": [20, 40], "Diabetes_012": [0, 1]})
    result, report = preprocess(frame, target_column="Diabetes_012")
    assert result["age"].notna().all()
    assert report["missing_values_after"]["age"] == 0
