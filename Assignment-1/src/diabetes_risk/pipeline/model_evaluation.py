"""
Model evaluation pipeline.

This module:
1. Loads the diabetes dataset.
2. Creates a reproducible train/test split.
3. Loads the previously trained Random Forest model.
4. Trains Logistic Regression with StandardScaler.
5. Saves the Logistic Regression model and scaler.
6. Evaluates both models.
7. Saves comparison metrics.
8. Saves classification reports.
9. Saves confusion matrices.
10. Generates a model comparison visualization.
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def evaluate_models(
    input_path: Path,
    report_dir: Path,
) -> dict[str, str]:
    """Load/train models and generate evaluation artifacts."""

    # ---------------------------------------------------------
    # 1. Create output directory
    # ---------------------------------------------------------
    report_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 2. Load dataset
    # ---------------------------------------------------------
    df = pd.read_csv(input_path)

    print(f"Dataset loaded: {input_path}")
    print(f"Dataset shape: {df.shape}")

    # ---------------------------------------------------------
    # 3. Normalize column names
    # ---------------------------------------------------------
    df.columns = [
        column.strip().lower()
        for column in df.columns
    ]

    # ---------------------------------------------------------
    # 4. Define features and target
    # ---------------------------------------------------------
    X = df.drop(columns=["diabetes_012"])
    y = df["diabetes_012"]

    # ---------------------------------------------------------
    # 5. Reproduce the same train/test split
    # ---------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print(f"Training records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    # =========================================================
    # RANDOM FOREST
    # =========================================================

    # ---------------------------------------------------------
    # 6. Load previously trained Random Forest
    # ---------------------------------------------------------
    random_forest_path = (
        report_dir / "random_forest_model.joblib"
    )

    if not random_forest_path.exists():
        raise FileNotFoundError(
            f"Random Forest model not found at: "
            f"{random_forest_path}\n"
            "Run the Random Forest training stage first."
        )

    random_forest_model = joblib.load(
        random_forest_path
    )

    print(
        f"\nRandom Forest model loaded from: "
        f"{random_forest_path}"
    )

    # ---------------------------------------------------------
    # 7. Generate Random Forest predictions
    # ---------------------------------------------------------
    rf_predictions = random_forest_model.predict(
        X_test
    )

    # =========================================================
    # LOGISTIC REGRESSION
    # =========================================================

    # ---------------------------------------------------------
    # 8. Create scaler
    # ---------------------------------------------------------
    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    X_test_scaled = scaler.transform(
        X_test
    )

    # ---------------------------------------------------------
    # 9. Create Logistic Regression model
    # ---------------------------------------------------------
    logistic_model = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    )

    # ---------------------------------------------------------
    # 10. Train Logistic Regression
    # ---------------------------------------------------------
    print("\nTraining Logistic Regression model...")

    logistic_model.fit(
        X_train_scaled,
        y_train,
    )

    print(
        "Logistic Regression training completed."
    )

    # ---------------------------------------------------------
    # 11. Save scaler + Logistic Regression model
    # ---------------------------------------------------------
    logistic_model_path = (
        report_dir
        / "logistic_regression_model.joblib"
    )

    joblib.dump(
        {
            "scaler": scaler,
            "model": logistic_model,
        },
        logistic_model_path,
    )

    print(
        f"Logistic Regression model saved to: "
        f"{logistic_model_path}"
    )

    # ---------------------------------------------------------
    # 12. Generate Logistic Regression predictions
    # ---------------------------------------------------------
    lr_predictions = logistic_model.predict(
        X_test_scaled
    )

    # =========================================================
    # MODEL METRICS
    # =========================================================

    def calculate_metrics(
        model_name: str,
        y_true: pd.Series,
        predictions,
    ) -> dict[str, object]:
        """Calculate evaluation metrics for one model."""

        return {
            "Model": model_name,
            "Accuracy": accuracy_score(
                y_true,
                predictions,
            ),
            "Balanced Accuracy": balanced_accuracy_score(
                y_true,
                predictions,
            ),
            "Precision": precision_score(
                y_true,
                predictions,
                average="weighted",
                zero_division=0,
            ),
            "Recall": recall_score(
                y_true,
                predictions,
                average="weighted",
                zero_division=0,
            ),
            "F1 Score": f1_score(
                y_true,
                predictions,
                average="weighted",
                zero_division=0,
            ),
        }

    # ---------------------------------------------------------
    # 13. Calculate metrics
    # ---------------------------------------------------------
    results = [
        calculate_metrics(
            "Logistic Regression",
            y_test,
            lr_predictions,
        ),
        calculate_metrics(
            "Random Forest",
            y_test,
            rf_predictions,
        ),
    ]

    results_df = pd.DataFrame(results)

    # ---------------------------------------------------------
    # 14. Display model comparison
    # ---------------------------------------------------------
    print("\nModel Comparison")
    print(
        results_df.to_string(index=False)
    )

    # ---------------------------------------------------------
    # 15. Save model evaluation CSV
    # ---------------------------------------------------------
    comparison_path = (
        report_dir / "model_evaluation.csv"
    )

    results_df.to_csv(
        comparison_path,
        index=False,
    )

    print(
        f"\nModel comparison saved to: "
        f"{comparison_path}"
    )

    # =========================================================
    # MODEL COMPARISON CHART
    # =========================================================

    # ---------------------------------------------------------
    # 16. Create model comparison chart
    # ---------------------------------------------------------
    metrics = [
        "Accuracy",
        "Balanced Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
    ]

    chart_data = results_df.set_index(
        "Model"
    )[metrics]

    chart_data.plot(
        kind="bar",
        figsize=(12, 7),
    )

    plt.title(
        "Model Performance Comparison"
    )

    plt.xlabel("Model")
    plt.ylabel("Score")
    plt.ylim(0, 1)
    plt.xticks(rotation=0)

    plt.legend(
        title="Metric",
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )

    plt.tight_layout()

    comparison_chart_path = (
        report_dir / "model_comparison.png"
    )

    plt.savefig(
        comparison_chart_path,
        bbox_inches="tight",
        dpi=300,
    )

    plt.close()

    print(
        f"Model comparison chart saved to: "
        f"{comparison_chart_path}"
    )

    # =========================================================
    # CLASSIFICATION REPORTS
    # =========================================================

    # ---------------------------------------------------------
    # 17. Generate classification reports
    # ---------------------------------------------------------
    model_predictions = {
        "logistic_regression": lr_predictions,
        "random_forest": rf_predictions,
    }

    for model_name, predictions in model_predictions.items():

        report = classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        )

        report_df = pd.DataFrame(
            report
        ).transpose()

        report_path = (
            report_dir
            / f"{model_name}_classification_report.csv"
        )

        report_df.to_csv(
            report_path
        )

        print(
            f"Classification report saved to: "
            f"{report_path}"
        )

    # =========================================================
    # CONFUSION MATRICES
    # =========================================================

    # ---------------------------------------------------------
    # 18. Generate confusion matrices
    # ---------------------------------------------------------
    for model_name, predictions in model_predictions.items():

        cm = confusion_matrix(
            y_test,
            predictions,
        )

        cm_df = pd.DataFrame(cm)

        cm_path = (
            report_dir
            / f"{model_name}_confusion_matrix.csv"
        )

        cm_df.to_csv(
            cm_path,
            index=False,
        )

        print(
            f"Confusion matrix saved to: "
            f"{cm_path}"
        )

    print(
        "\nModel evaluation completed successfully."
    )

    # ---------------------------------------------------------
    # 19. Return artifact paths
    # ---------------------------------------------------------
    return {
        "random_forest_model": str(
            random_forest_path
        ),
        "logistic_regression_model": str(
            logistic_model_path
        ),
        "model_evaluation": str(
            comparison_path
        ),
        "model_comparison_plot": str(
            comparison_chart_path
        ),
    }


if __name__ == "__main__":
    import os

    from .cli import DEFAULT_REPORT_DIR

    model_ready_path = Path(
        os.environ.get(
            "DIABETES_MODEL_READY_PATH",
            "data/processed/diabetes_model_ready.csv",
        )
    )

    evaluate_models(
        input_path=model_ready_path,
        report_dir=DEFAULT_REPORT_DIR,
    )
