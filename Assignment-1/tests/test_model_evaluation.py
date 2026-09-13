import numpy as np
import pandas as pd

from diabetes_risk.pipeline.model_evaluation import evaluate_models
from diabetes_risk.pipeline.randomforestclassifier import train_random_forest


def _synthetic_model_ready_frame(rows_per_class: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(7)
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


def test_evaluate_models_writes_required_outputs(tmp_path) -> None:
    frame = _synthetic_model_ready_frame()
    input_path = tmp_path / "diabetes_model_ready.csv"
    frame.to_csv(input_path, index=False)
    report_dir = tmp_path / "report"

    # model_evaluation loads a previously trained Random Forest model,
    # so it must be trained first against the same input/report_dir.
    train_random_forest(input_path, report_dir)

    result = evaluate_models(input_path, report_dir)

    for name in [
        "random_forest_model.joblib",
        "logistic_regression_model.joblib",
        "model_evaluation.csv",
        "model_comparison.png",
        "logistic_regression_classification_report.csv",
        "random_forest_classification_report.csv",
        "logistic_regression_confusion_matrix.csv",
        "random_forest_confusion_matrix.csv",
    ]:
        assert (report_dir / name).exists(), name

    comparison = pd.read_csv(report_dir / "model_evaluation.csv")
    assert set(comparison["Model"]) == {"Logistic Regression", "Random Forest"}
    assert {"Accuracy", "Balanced Accuracy", "Precision", "Recall", "F1 Score"} <= set(comparison.columns)
    assert result["model_evaluation"] == str(report_dir / "model_evaluation.csv")


def test_evaluate_models_requires_trained_random_forest(tmp_path) -> None:
    frame = _synthetic_model_ready_frame()
    input_path = tmp_path / "diabetes_model_ready.csv"
    frame.to_csv(input_path, index=False)
    report_dir = tmp_path / "report"

    try:
        evaluate_models(input_path, report_dir)
    except FileNotFoundError as exc:
        assert "random_forest_model.joblib" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError when Random Forest model is missing")
