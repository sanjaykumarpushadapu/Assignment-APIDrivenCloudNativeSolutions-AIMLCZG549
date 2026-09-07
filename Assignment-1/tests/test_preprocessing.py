import pandas as pd

from diabetes_risk.pipeline.preprocessing import preprocess


def test_preprocess_normalizes_columns_and_fills_missing_values() -> None:
    frame = pd.DataFrame({" Age ": [20, None], "Risk Group": ["low", None]})

    result = preprocess(frame)

    assert list(result.columns) == ["age", "risk_group"]
    assert result["age"].isna().sum() == 0
    assert result["risk_group"].tolist() == ["low", "unknown"]