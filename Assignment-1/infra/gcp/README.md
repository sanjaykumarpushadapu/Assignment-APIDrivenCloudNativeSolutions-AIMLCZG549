# GCP Deployment Boundary

GCP is the planned production platform. Person 2's core pipeline remains cloud agnostic.

The intended production mapping is:

```text
Cloud Storage
  ↓
Cloud Composer (managed Apache Airflow)
  ↓
Python pipeline
  ↓
Cloud Storage
```

Cloud Logging/Monitoring can consume execution/task information for the later dashboard implementation.

No credentials or GCP project identifiers are committed to this repository.
