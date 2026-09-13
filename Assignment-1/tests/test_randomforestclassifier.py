import numpy as np
import pandas as pd

from diabetes_risk.pipeline.randomforestclassifier import train_random_forest


def _synthetic_model_ready_frame(rows_per_class: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    records = []
    for target in (0, 1, 2):
        for _ in range(rows_per_class):
            records.append(
                {
                    "Diabetes_012": target,
                    "BMI": float(rng.uniform(18, 40)),
                    "Age": float(rng.integers(1, 13)),
                    "HighBP": float(rng.integers(0, 2)),
                    "HighChol": float(rng.integers(0, 2)),
                    "PhysActivity": float(rng.integers(0, 2)),
                    "GenHlth": float(rng.integers(1, 6)),
                }
            )
    return pd.DataFrame(records)


def test_train_random_forest_writes_required_outputs(tmp_path) -> None:
    frame = _synthetic_model_ready_frame()
    input_path = tmp_path / "diabetes_model_ready.csv"
    frame.to_csv(input_path, index=False)
    report_dir = tmp_path / "report"

    result = train_random_forest(input_path, report_dir)

    assert (report_dir / "random_forest_model.joblib").exists()
    assert (report_dir / "feature_importance.csv").exists()
    assert (report_dir / "feature_importance.png").exists()
    assert result["model_path"] == str(report_dir / "random_forest_model.joblib")

    importance = pd.read_csv(report_dir / "feature_importance.csv")
    assert set(importance.columns) == {"Feature", "Importance"}
    assert "diabetes_012" not in {c.lower() for c in importance["Feature"]}
    assert len(importance) == 6
