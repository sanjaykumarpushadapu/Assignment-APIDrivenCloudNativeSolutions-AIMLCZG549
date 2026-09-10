import joblib
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def train_random_forest(
    input_path: Path,
    report_dir: Path,
):
    # Make sure output directory exists
    report_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    df = pd.read_csv(input_path)

    # Normalize column names
    df.columns = [
        column.strip().lower()
        for column in df.columns
    ]

    # Define features and target
    X = df.drop("diabetes_012", axis=1)
    y = df["diabetes_012"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Random Forest model
    rf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    # Train model
    rf.fit(X_train, y_train)

    # Save trained Random Forest model
    model_path = report_dir / "random_forest_model.joblib"

    joblib.dump(
        rf,
        model_path
    )

    print(
        f"Random Forest model saved to: {model_path}"
    )

    # Feature importance
    feature_importance = pd.DataFrame({
        "Feature": X.columns,
        "Importance": rf.feature_importances_
    })

    feature_importance = feature_importance.sort_values(
        "Importance",
        ascending=False
    )

    print(feature_importance.head(15))

    # Save feature importance CSV
    feature_importance.to_csv(
        report_dir / "feature_importance.csv",
        index=False
    )

    # Create feature importance chart
    feature_importance.head(15).plot(
        x="Feature",
        y="Importance",
        kind="bar",
        figsize=(12, 7),
        legend=False
    )

    plt.title("Random Forest Feature Importance")
    plt.xlabel("Feature")
    plt.ylabel("Importance")
    plt.tight_layout()

    plt.savefig(
        report_dir / "feature_importance.png",
        bbox_inches="tight",
        dpi=300
    )

    plt.close()

    return {
        "model_path": str(model_path),
        "feature_importance_path": str(
            report_dir / "feature_importance.csv"
        ),
        "feature_importance_plot": str(
            report_dir / "feature_importance.png"
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

    train_random_forest(
        model_ready_path,
        DEFAULT_REPORT_DIR,
    )
