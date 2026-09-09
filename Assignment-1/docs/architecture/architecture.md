# Person 2 Architecture Boundary

```text
                 Apache Airflow DAG
                 (cloud agnostic)
                         |
                         v
              diabetes_risk.pipeline
                         |
        +----------------+----------------+
        |                |                |
   Data Quality     Preprocessing        EDA
        |                |                |
        +----------------+----------------+
                         |
                         v
              Local / Cloud Storage
                         |
                  Cloud Composer
                (GCP deployment)
```

The DAG is the orchestration abstraction. GCP is a deployment target, not a dependency of the data-processing code.
