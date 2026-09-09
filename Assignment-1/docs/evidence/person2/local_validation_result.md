# Person 2 Local Validation Result

Execution date: 2026-09-08

## Input

- File: `data/raw/diabetes_012_health_indicators_BRFSS2015.csv`
- Rows: 253,680
- Columns: 22
- Target: `Diabetes_012`

## Data quality

| Check | Result |
|---|---:|
| Missing values | 0 |
| Exact duplicate records | 23,899 (9.42%) |
| Invalid target values | 0 |
| Invalid known numeric-range values | 0 |
| Invalid binary values | 0 |
| Quality status | PASS_WITH_WARNINGS |

## Preprocessing

- Exact duplicates removed: 23,899
- Cleaned analytical rows: 229,781
- Numeric missing-value imputation: supported; no imputation required for the current source because missing count is zero
- Categorical encoding: supported; the approved dataset contains numeric/binary/ordinal fields and therefore requires no categorical one-hot encoding in the current run
- Standardization: applied only to continuous/count fields in the separate model-ready output (`BMI`, `MentHlth`, `PhysHlth`)
- Target preserved without scaling

## Outputs

- `data/processed/diabetes_cleaned.csv`: 229,781 × 22
- `data/processed/diabetes_model_ready.csv`: 229,781 × 22
- `data/processed/preprocessing_report.json`
- `data/outputs/quality/data_quality.json`
- `data/outputs/quality/missing_values.csv`
- `data/outputs/eda/summary_statistics.csv`
- `data/outputs/eda/missing_value_summary.csv`
- `data/outputs/eda/target_distribution.csv`
- `data/outputs/eda/target_distribution.png`
- `data/outputs/eda/correlation_matrix.csv`
- `data/outputs/eda/binned_features.csv`
- feature-distribution and bivariate chart directories under `data/outputs/eda/`
- execution log under `data/outputs/execution/`

## Automated tests

`pytest -q` result:

```text
17 passed, 1 skipped
```

The one skipped test requires an Airflow runtime. Airflow is intentionally not part of the core Python dependency set; the DAG is designed for an Airflow/Cloud Composer runtime.

## Scheduling evidence

The DAG contains `*/2 * * * *` and `max_active_runs=1`. Two consecutive scheduled-run screenshots remain a deployment-time task once Airflow/Cloud Composer is available.
