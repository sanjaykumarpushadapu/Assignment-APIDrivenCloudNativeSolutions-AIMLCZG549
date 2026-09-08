# Diabetes Risk Prediction

Project repository for Group 49's **Diabetes Risk Prediction Using Health and Lifestyle Indicators** assignment.

This project currently contains the local Python foundation for the assignment: dataset ingestion validation, a reusable pipeline CLI, and a project structure for the later cloud/dashboard/API work. The platform decision and the final cloud implementation are still pending as recorded in `Assignment_1_Workload_Plan.md`.

## Current status

- **Person 1:** Complete. Business context, dataset verification, and ingestion validation are in place.
- **Person 2:** Pending. Data quality, preprocessing, workflow automation, and execution logging remain.
- **Person 3:** Pending. EDA, feature importance, and optional model analysis remain.
- **Person 4:** Pending. Dashboard, API testing, and final demonstration remain.

## Project structure

```text
src/diabetes_risk/
  api/          FastAPI application and OpenAPI endpoints
  dashboard/    Streamlit dashboard entry point
  pipeline/     Ingestion, validation, preprocessing, and EDA stages
tests/          Focused tests for the local pipeline
data/           Local raw, processed, and output data (ignored by Git)
reports/        Generated charts and summary outputs (ignored by Git)
infra/          Placeholder for selected-cloud deployment assets
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

This cleans and normalizes the CSV and writes processed output to the default `data/processed` directory.

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

Before final submission, the team must still complete the following:

1. Person 2: data-quality checks, preprocessing, workflow automation, and execution logging
2. Person 3: EDA, feature-importance analysis, and any optional model evaluation
3. Person 4: dashboard, four API details, API testing evidence, and final demo video
4. Final review, documentation, screenshots, and submission upload

## Next platform decision

Before the cloud-specific implementation is finalized, the group must decide:

- selected cloud platform
- region and account access
- schedule cadence and execution method
- dashboard technology
- API set and authentication method
- deployment or hosting method

This decision should be recorded in `Assignment_1_Workload_Plan.md` before the final cloud implementation is locked in.
