import pandas as pd

from diabetes_risk.pipeline.preprocessing import preprocess


def test_preprocess_normalizes_columns_fills_missing_and_scales_numeric() -> None:
    frame = pd.DataFrame({" Age ": [20, 40, None], "Risk Group": ["low", "high", None]})

    result, report = preprocess(frame)

    assert list(result.columns) == ["age", "risk_group"]
    assert result["age"].isna().sum() == 0
    assert result["risk_group"].tolist() == ["low", "high", "unknown"]

    # numeric columns are min-max scaled into [0, 1]
    assert result["age"].min() == 0.0
    assert result["age"].max() == 1.0

    assert report["missing_values_before"] == {"age": 1, "risk_group": 1}
    assert report["missing_values_after"] == {}
    assert report["rows"] == 3


def test_preprocess_excludes_target_column_from_normalization() -> None:
    frame = pd.DataFrame({"age": [20, 40, 60], "diabetes_binary": [0, 1, 0]})

    result, _ = preprocess(frame, target_column="diabetes_binary")

    # target keeps its original values; only non-target numeric columns are scaled
    assert result["diabetes_binary"].tolist() == [0, 1, 0]
    assert result["age"].min() == 0.0
    assert result["age"].max() == 1.0
