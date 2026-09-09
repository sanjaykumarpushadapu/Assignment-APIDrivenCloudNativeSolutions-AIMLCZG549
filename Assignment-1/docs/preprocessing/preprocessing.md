# Person 2 — Preprocessing

## Transformation contract

The preprocessing implementation is cloud-platform agnostic and operates on pandas DataFrames. It performs transformations in this order:

1. Normalize column names to lowercase snake case.
2. Detect and remove exact duplicate records, retaining the first occurrence.
3. Median-impute numeric missing values where required.
4. Mode-impute non-numeric values where required.
5. One-hot encode non-numeric categorical fields where required.
6. Preserve existing binary and ordinal indicators in interpretable form.
7. Preserve the target column without scaling.
8. Produce an analytical cleaned dataset with original feature scales.
9. Produce a separate standardized model-ready dataset for future model work.

## Outputs

```text
data/processed/diabetes_cleaned.csv
data/processed/diabetes_model_ready.csv
data/processed/preprocessing_report.json
```

`diabetes_cleaned.csv` is the primary handoff to Person 3 because it preserves interpretable feature values for EDA. `diabetes_model_ready.csv` applies z-score standardization to continuous/count features (`BMI`, `MentHlth`, and `PhysHlth`) and is reserved for downstream model experimentation if Person 3 includes the optional model.

## Why two outputs?

Scaling BMI or health-count fields before EDA would make the charts less interpretable in the report. Separating the analytical cleaned data from the standardized model-ready data satisfies the normalization requirement without sacrificing meaningful EDA units.
