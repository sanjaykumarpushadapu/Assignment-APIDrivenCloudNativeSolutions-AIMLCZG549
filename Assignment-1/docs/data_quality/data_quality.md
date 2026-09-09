# Person 2 — Data Quality

## Scope

This document records the data-quality contract implemented for the Diabetes Risk Prediction assignment. The raw dataset is preserved unchanged; quality checks are performed before preprocessing.

## Checks

- Schema and target-column validation
- Row and column counts
- Pandas data types
- Summary statistics
- Missing-value count and percentage
- Exact duplicate records
- Target values (`Diabetes_012` must be 0, 1, or 2)
- Known numeric ranges
- Binary indicator values (0/1)

## Verified dataset

The repository contains `data/raw/diabetes_012_health_indicators_BRFSS2015.csv` with 253,680 rows and 22 columns. A local execution verified:

- Missing values: 0
- Exact duplicate records: 23,899 (9.42%)
- Invalid target values: 0
- Invalid known numeric-range values: 0
- Invalid binary values: 0

The duplicate count is reported as a quality warning rather than a data-failure condition. Exact duplicates are removed during preprocessing while the raw source remains unchanged.

## Quality status

For the current source data the quality status is `PASS_WITH_WARNINGS` because duplicate records are present. The data is otherwise valid against the implemented schema, target, range and binary-value checks.

## Generated evidence

The pipeline writes:

```text
data/outputs/quality/data_quality.json
data/outputs/quality/missing_values.csv
```
