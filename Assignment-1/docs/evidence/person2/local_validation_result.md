# Person 2 Full-Dataset Local Validation Result

Execution date: 2026-09-09

## Full end-to-end execution

Exactly **one** fresh successful end-to-end pipeline run is retained for the project outputs. It used the complete raw dataset and did not use a two-record test fixture.

- Run ID: `20260909T063214670950Z`
- Start: `2026-09-09T06:32:14.670942Z`
- End: `2026-09-09T06:32:31.222395Z`
- Runtime: 16.55 seconds
- File: `data/raw/diabetes_012_health_indicators_BRFSS2015.csv`
- Rows read: 253,680
- Columns: 22
- Target: `Diabetes_012`
- Execution status: `SUCCESS`

## Data quality

| Check | Result |
|---|---:|
| Missing values | 0 |
| Exact duplicate records | 23,899 (9.42%) |
| Invalid target values | 0 |
| Invalid known numeric-range values | 0 |
| Invalid binary values | 0 |
| Quality status | PASS_WITH_WARNINGS |

The warning status is due to duplicate records only; the raw source is preserved unchanged.

## Preprocessing

- Exact duplicates removed: 23,899
- Cleaned analytical rows: 229,781
- Cleaned analytical shape: 229,781 × 22
- Numeric missing-value imputation: supported; no imputation required because the full raw dataset contains zero missing values
- Categorical encoding: supported; no one-hot encoding required for the current numeric/binary/ordinal source
- Standardization: applied only to `BMI`, `MentHlth`, and `PhysHlth` in the separate model-ready output
- Target preserved without scaling

## Refreshed EDA target distribution

| `Diabetes_012` | Records | Percentage |
|---:|---:|---:|
| 0 | 190,055 | 82.71% |
| 1 | 4,629 | 2.01% |
| 2 | 35,097 | 15.27% |
| **Total** | **229,781** | **100.00%** |

## Outputs from the full-dataset run

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
- `data/outputs/execution/run_20260909T063214670950Z.json`
- `data/outputs/execution/latest_run.json`

## Automated tests

The previously established automated test suite remains:

```text
17 passed, 1 skipped
```

The one skipped test requires an Airflow runtime. Airflow is intentionally not part of the core Python dependency set; the DAG is designed for an Airflow/Cloud Composer runtime.

## Scheduling evidence

The DAG contains `*/2 * * * *` and `max_active_runs=1`. Two consecutive scheduled-run screenshots remain a deployment-time task once Airflow/Cloud Composer is available.
