# Diabetes Risk Prediction

Project repository for Group 49's **Diabetes Risk Prediction Using Health and Lifestyle Indicators** assignment.

The project contains a platform-neutral Python data pipeline, cloud-neutral Apache Airflow orchestration, and placeholders for the later dashboard/API work. GCP Cloud Composer is the planned production deployment target, but the core pipeline and DAG do not depend on GCP SDKs.

## Current status

- **Person 1:** Complete. Business context, dataset verification, and ingestion validation are in place.
- **Person 2:** Complete for the local implementation. Data quality, preprocessing, automated EDA generation, Airflow DAG, scheduling configuration, execution logging, tests, and handoff documentation are implemented. Cloud Composer scheduled-run evidence remains a deployment-time activity.
- **Person 3:** Pending. EDA, feature importance, and optional model analysis remain.
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
DIABETES_REPORT_DIR=reports/generated
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

## Run the dashboard

**Windows (PowerShell):**

```powershell
streamlit run src/diabetes_risk/dashboard/app.py
```

**macOS / Linux (Terminal):**

```bash
streamlit run src/diabetes_risk/dashboard/app.py
```

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

Do not commit dataset files or credentials.

## Project report

The shared report for the final submission lives in [`docs/report/REPORT.md`](docs/report/REPORT.md). The workload and delivery plan are in `Assignment_1_Workload_Plan.md`.

## Remaining assignment work

Person 2 implementation is complete. The remaining team work is:

1. Person 3: EDA interpretation, feature-importance analysis, and any optional model evaluation
2. Person 4: dashboard, four API details, API testing evidence, and final demo video
3. Final review, documentation, screenshots, and submission upload

## Orchestration and deployment

The Airflow DAG in `dags/diabetes_risk_pipeline.py` is cloud agnostic and schedules the complete Person-2 pipeline every two minutes with `max_active_runs=1`. The same DAG is intended for local Airflow testing and later deployment to GCP Cloud Composer. GCP-specific deployment notes live under `infra/gcp/`.

Do not commit credentials, service-account keys, or environment-specific secrets.
