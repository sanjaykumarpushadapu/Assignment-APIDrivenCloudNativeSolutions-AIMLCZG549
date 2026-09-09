# Person 2 → Person 3 Handoff

## Completed package

Person 2 provides:

- `data_quality.py` — validation and quality reporting
- `preprocessing.py` — cleaning, imputation, encoding and standardization
- `eda.py` — automated EDA artifact generation
- `runner.py` — end-to-end quality → preprocessing → EDA execution
- `logging_utils.py` — structured execution logging
- `config.py` — environment-driven configuration
- `dags/diabetes_risk_pipeline.py` — cloud-agnostic Airflow orchestration
- Unit/integration tests for the above

## Primary dataset handoff

```text
data/processed/diabetes_cleaned.csv
```

Verified source row count: 253,680.

Verified exact duplicate count: 23,899.

Expected cleaned row count: 229,781 for the current source when exact duplicates are removed.

## EDA contract for Person 3

Each successful run refreshes:

- `summary_statistics.csv`
- `missing_value_summary.csv`
- `target_distribution.csv`
- `target_distribution.png`
- feature-distribution charts for BMI, Age, General Health, High BP, High Cholesterol, Physical Activity, Cholesterol Check and Smoking
- `correlation_matrix.csv`
- bivariate outputs for BMI, Age, High BP, High Cholesterol, Physical Activity and General Health against the target
- `binned_features.csv`

Person 3 should use `diabetes_cleaned.csv` for interpretable EDA. If Person 3's final EDA specification differs, `eda.py` can be adjusted without changing the orchestration contract.

## Important boundary

Person 2 has not implemented model training, model deployment, final dashboarding, or APIs. Those remain with Persons 3 and 4 according to the workload plan.
