# Two-Minute Scheduling and Verification

## Required schedule

The assignment requires the preprocessing and EDA workflow to run every two minutes. The Airflow DAG implements:

```text
schedule = "*/2 * * * *"
max_active_runs = 1
catchup = False
```

## Verification plan

After Airflow/Cloud Composer is available, capture at least two consecutive scheduled runs approximately two minutes apart. For each run record:

- trigger time
- completion status
- distinct execution/log entry
- refreshed EDA output timestamp

The current local environment does not contain an Airflow runtime, so scheduled-run screenshots are a deployment-time evidence item rather than a fabricated result.
