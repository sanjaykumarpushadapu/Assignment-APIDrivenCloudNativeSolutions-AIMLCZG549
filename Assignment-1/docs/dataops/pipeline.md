# Person 2 — DataOps Pipeline

## Execution flow

```text
Raw CSV
  ↓
Data-quality validation
  ↓
Preprocessing
  ├── diabetes_cleaned.csv
  └── diabetes_model_ready.csv
  ↓
Automated EDA artifact generation
  ↓
Structured execution log
```

The core implementation is independent of any cloud SDK. The same Python runner can execute locally or from Airflow.

## EDA outputs refreshed by each successful run

- Summary statistics
- Missing-value summary
- Target distribution table and chart
- Feature distribution charts
- Correlation matrix
- Selected bivariate tables and charts
- Age/BMI bins
- EDA metadata

Person 3 owns the interpretation of these outputs; Person 2 owns their automated generation as required by the workload plan.
