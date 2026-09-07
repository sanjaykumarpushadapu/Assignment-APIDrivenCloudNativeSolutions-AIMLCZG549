import pandas as pd


def preprocess(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply the initial, repeatable cleaning contract for the pipeline."""
    cleaned = frame.copy()
    cleaned.columns = [column.strip().lower().replace(" ", "_") for column in cleaned.columns]
    numeric_columns = cleaned.select_dtypes(include="number").columns
    for column in numeric_columns:
        cleaned[column] = cleaned[column].fillna(cleaned[column].median())
    categorical_columns = cleaned.select_dtypes(exclude="number").columns
    for column in categorical_columns:
        cleaned[column] = cleaned[column].fillna("unknown")
    return cleaned