# Diabetes Risk Prediction

Project repository for Group 49's **Diabetes Risk Prediction Using Health and Lifestyle Indicators** assignment.

The project contains a platform-neutral Python data pipeline, cloud-neutral Apache Airflow orchestration, and placeholders for the later dashboard/API work. GCP Cloud Composer is the planned production deployment target, but the core pipeline and DAG do not depend on GCP SDKs.

## Current status

- **Person 1:** Complete. Business context, dataset verification, and ingestion validation are in place.
- **Person 2:** Complete, including verified Cloud Composer deployment evidence (two consecutive scheduled runs, two minutes apart, all tasks successful).
- **Person 3:** Complete. EDA interpretation (dataset overview, target distribution, feature distribution, correlation, bivariate analysis) is documented in `docs/report/REPORT.md` Section 3. An optional Random Forest vs. Logistic Regression model comparison is also implemented and evaluated, including feature importance and class-level metrics.
- **Person 4:** Pending. Dashboard, API testing, and final demonstration remain.

## Project structure

```text
src/diabetes_risk/
  api/          FastAPI application and OpenAPI endpoints
  dashboard/    Streamlit dashboard entry point
  pipeline/     Ingestion, data quality, preprocessing, EDA, runner, and logging
tests/          Focused unit/integration tests
data/           Raw, processed, and generated pipeline artifacts
dags/           Cloud-neutral Apache Airflow DAG
infra/          GCP deployment notes for Cloud Composer
docs/report/    Shared REPORT.md — final submission content, built step by step
```

## Environment setup

Copy the example file to create your own local `.env` (it's gitignored — never commit it). It's loaded automatically by pipeline commands via `python-dotenv`, so any value you change here takes effect without exporting shell variables manually.

**Windows (PowerShell):**

```powershell
copy .env.example .env
```

**macOS / Linux (Terminal):**

```bash
cp .env.example .env
```

The defaults are already correct for local development — you only need to edit `.env` if you move the dataset, want processed output written somewhere else, or point at a different report directory:

```text
DIABETES_DATASET_PATH=data/raw/diabetes_012_health_indicators_BRFSS2015.csv
DIABETES_OUTPUT_DIR=data/processed
DIABETES_REPORT_DIR=data/outputs
```

## Local setup

Requires Python 3.11 or newer.

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

**macOS / Linux (Terminal):**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Run the pipeline

Every pipeline stage runs through one CLI command: `python -m diabetes_risk.pipeline <command> ...`.

**Windows (PowerShell):**

```powershell
python -m diabetes_risk.pipeline --help
python -m diabetes_risk.pipeline ingest
```

**macOS / Linux (Terminal):**

```bash
python -m diabetes_risk.pipeline --help
python -m diabetes_risk.pipeline ingest
```

### Ingestion command

```bash
python -m diabetes_risk.pipeline ingest
```

Or with explicit paths:

```bash
python -m diabetes_risk.pipeline ingest --source data/raw/diabetes_012_health_indicators_BRFSS2015.csv --manifest data/raw/ingestion_manifest.json
```

This validates the dataset, checks required columns and the target field, computes the SHA-256 hash, and appends a timestamped entry to the ingestion manifest.

### Preprocessing command

```bash
python -m diabetes_risk.pipeline run data/raw/diabetes_012_health_indicators_BRFSS2015.csv --target-column Diabetes_012
```

This runs data-quality validation, removes exact duplicates, imputes missing values where required, creates the analytical cleaned dataset, creates a standardized model-ready dataset, generates EDA artifacts, and writes a structured execution log.

### Optional model comparison commands

```bash
python -m diabetes_risk.pipeline randomforestclassifier
python -m diabetes_risk.pipeline model_evaluation
```

`randomforestclassifier` trains a Random Forest on `data/processed/diabetes_model_ready.csv` (override with `DIABETES_MODEL_READY_PATH`) and writes the model, feature-importance CSV, and feature-importance plot to `data/outputs` (override with `DIABETES_REPORT_DIR`). `model_evaluation` must be run after it -- it loads the saved Random Forest model, trains a Logistic Regression model for comparison, and writes `model_evaluation.csv`, `model_comparison.png`, and per-model classification-report/confusion-matrix CSVs to the same report directory. See `docs/report/REPORT.md` Section 3.8 for the verified results.

## Run the API

**Windows (PowerShell):**

```powershell
uvicorn diabetes_risk.api.main:app --reload --host 127.0.0.1 --port 9000
```

**macOS / Linux (Terminal):**

```bash
uvicorn diabetes_risk.api.main:app --reload --host 127.0.0.1 --port 9000
```

OpenAPI documentation is available at `http://127.0.0.1:9000/docs`.

### GCP setup for the API layer

The API's application-detail endpoints (`/api/v1/workflow`, `/api/v1/runs/latest`, `/api/v1/dataset`, `/api/v1/schedule`, `/api/v1/model`) call GCP's built-in APIs -- Cloud Composer, the Airflow REST API, and Cloud Storage -- per the assessment's "Use Built-in APIs" requirement (activity 3.1). `/health` and `/api/v1/metadata` need no GCP setup at all.

**Current implementation status:**

| Endpoint | Service function | Status |
|---|---|---|
| `/api/v1/schedule` | `gcp_service.get_composer_environment_details()` | **Implemented** (Cloud Composer Environments API) |
| `/api/v1/model` | `local_service.get_model_comparison()` | **Implemented** (Cloud Storage API) |
| `/api/v1/workflow`, `/api/v1/runs/latest` | `gcp_service.get_dag_run_history()`, `get_task_instance_status()` | Skeleton -- `NotImplementedError` (Airflow REST API, needs IAP auth) |
| `/api/v1/dataset` | `local_service.get_dataset_quality()` | Skeleton -- `NotImplementedError` (Cloud Storage API) |

The two implemented functions are the reference pattern for the rest -- same config, same credential handling, same "raise a clean `NotImplementedError`/501 if not configured" style. Copy that pattern for `get_dag_run_history()`, `get_task_instance_status()`, `get_environment_health()`, and `get_dataset_quality()`.

**One-time GCP setup (already done for this project's own `diabetes-risk-group49` project -- repeat for a different project/account):**

1. Confirm the Composer environment is running:
   ```bash
   gcloud composer environments describe diabetes-risk-env --location=us-central1 --project=<your-project-id>
   ```
2. Create a read-only service account and grant it the three required roles:
   ```bash
   gcloud iam service-accounts create diabetes-api-reader \
     --project=<your-project-id> \
     --display-name="Diabetes API read-only access"

   gcloud projects add-iam-policy-binding <your-project-id> \
     --member="serviceAccount:diabetes-api-reader@<your-project-id>.iam.gserviceaccount.com" \
     --role="roles/composer.viewer"

   gcloud projects add-iam-policy-binding <your-project-id> \
     --member="serviceAccount:diabetes-api-reader@<your-project-id>.iam.gserviceaccount.com" \
     --role="roles/monitoring.viewer"

   gcloud projects add-iam-policy-binding <your-project-id> \
     --member="serviceAccount:diabetes-api-reader@<your-project-id>.iam.gserviceaccount.com" \
     --role="roles/storage.objectViewer"
   ```
3. Download a key for that service account (never commit this file):
   ```bash
   gcloud iam service-accounts keys create ~/diabetes-api-key.json \
     --iam-account=diabetes-api-reader@<your-project-id>.iam.gserviceaccount.com
   ```
4. Install the GCP client libraries into your virtualenv: `pip install -e ".[gcp]"`.
5. Copy `.env.example` to `.env` (it's gitignored) and fill in:
   ```
   GCP_PROJECT_ID=<your-project-id>
   GCP_LOCATION=us-central1
   GCP_COMPOSER_ENVIRONMENT=diabetes-risk-env
   GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/diabetes-api-key.json
   DIABETES_GCS_BUCKET=diabetes-risk-group49-pipeline
   ```
   `GCP_LOCATION` and `GCP_COMPOSER_ENVIRONMENT` are already filled in `.env.example` for this team's environment. `DIABETES_GCS_BUCKET` is `diabetes-risk-group49-pipeline` -- this is a bucket created directly inside the `diabetes-risk-group49` project (its DAG-code default in `dags/diabetes_risk_pipeline.py`, and the Composer environment's own `DIABETES_GCS_BUCKET` Airflow environment variable, are both set to this value). An earlier bucket, `apicloudsolutions49-diabetes-pipeline`, was used briefly but turned out to belong to a *different* GCP project (`apicloudsolutions49`), where the team's service account couldn't be granted IAM access -- don't use that bucket name.
6. Run the API (see "Run the API" above) and check `/api/v1/schedule` and `/api/v1/model` return real data, not a 501.

**Giving another teammate access**, instead of sharing the key file, grant their own Google/BITS account the same three roles and have them run `gcloud auth application-default login` (then they can leave `GOOGLE_APPLICATION_CREDENTIALS` blank):
```bash
gcloud projects add-iam-policy-binding <your-project-id> \
  --member="user:teammate@example.com" --role="roles/composer.viewer"
gcloud projects add-iam-policy-binding <your-project-id> \
  --member="user:teammate@example.com" --role="roles/monitoring.viewer"
gcloud projects add-iam-policy-binding <your-project-id> \
  --member="user:teammate@example.com" --role="roles/storage.objectViewer"
```

**Implementing the remaining functions:** see `infra/gcp/api/README.md` for the Airflow REST API's IAP-authentication step (needed for `get_dag_run_history()`/`get_task_instance_status()`), which is separate from the service-account auth used for Composer/Storage calls. Each remaining function's docstring in `gcp_service.py`/`local_service.py` names the exact API call, required IAM role, and suggested return shape.

## Run the dashboard

The dashboard is a small FastAPI app (its own server, separate from `api/main.py`) that displays activity/execution details (assessment activity 1.5) by calling the real API's endpoints client-side -- it has no hard-coded data of its own. Run the API first (see "Run the API" above, default port 9000), then start the dashboard on a different port:

**Windows (PowerShell):**

```powershell
uvicorn diabetes_risk.dashboard.app:app --reload --host 127.0.0.1 --port 8000
```

**macOS / Linux (Terminal):**

```bash
uvicorn diabetes_risk.dashboard.app:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in a browser. If you run the API on a different host/port, set `DIABETES_API_BASE_URL` in `.env` to match. The Schedule panel and the Model Comparison chart are backed by real GCP calls (see "GCP setup for the API layer" above) and show real data once `.env` is configured; the remaining panels correctly show "Not implemented yet" (a 501 from the API) until `gcp_service.get_dag_run_history()`/`get_task_instance_status()` and `local_service.get_dataset_quality()` are implemented.

## Dataset

The approved dataset is the Kaggle BRFSS diabetes health indicators dataset. The confirmed raw file is:

```text
data/raw/diabetes_012_health_indicators_BRFSS2015.csv
```

The project expects the following verified dataset profile:

- **Row count:** 253,680
- **Column count:** 22
- **Target column:** `Diabetes_012`
- **Source:** Kaggle Diabetes Health Indicators Dataset

The raw dataset CSV above is intentionally committed (see `.gitignore`) since it is CC0/public-domain and keeps the repository clone-and-run without a separate download step. Do not commit any other generated data files or credentials.

## Project report

The shared report for the final submission lives in [`docs/report/REPORT.md`](docs/report/REPORT.md). The workload and delivery plan are in `Assignment_1_Workload_Plan.md`.

## Remaining assignment work

Person 2 and Person 3 implementation are complete. The remaining team work is:

1. Person 4: dashboard, four API details, API testing evidence, and final demo video
2. Final review, documentation, screenshots, and submission upload

## Orchestration and deployment

The Airflow DAG in `dags/diabetes_risk_pipeline.py` is cloud agnostic and schedules the complete Person-2 pipeline every two minutes with `max_active_runs=1`. The same DAG is intended for local Airflow testing and later deployment to GCP Cloud Composer. GCP-specific deployment notes live under `infra/gcp/`.

Do not commit credentials, service-account keys, or environment-specific secrets.
