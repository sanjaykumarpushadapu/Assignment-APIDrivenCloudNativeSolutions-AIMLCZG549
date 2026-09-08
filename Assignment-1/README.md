# Diabetes Risk Prediction

Project skeleton for Group 49's **Diabetes Risk Prediction Using Health and Lifestyle Indicators** assignment.

The implementation is intentionally platform-neutral until the team resolves the cloud platform questions in `Assignment_1_Workload_Plan.md`.

## Structure

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

Every pipeline stage runs through one command: `python -m diabetes_risk.pipeline <command> ...`. Run `--help` to see all commands, and run the tests:

**Windows (PowerShell):**

```powershell
python -m diabetes_risk.pipeline --help
pytest
```

**macOS / Linux (Terminal):**

```bash
python -m diabetes_risk.pipeline --help
pytest
```

Run the API:

**Windows (PowerShell):**

```powershell
uvicorn diabetes_risk.api.main:app --reload --host 127.0.0.1 --port 9000
```

**macOS / Linux (Terminal):**

```bash
uvicorn diabetes_risk.api.main:app --reload --host 127.0.0.1 --port 9000
```

OpenAPI documentation is available at `http://127.0.0.1:9000/docs`.

Run the dashboard:

**Windows (PowerShell):**

```powershell
streamlit run src/diabetes_risk/dashboard/app.py
```

**macOS / Linux (Terminal):**

```bash
streamlit run src/diabetes_risk/dashboard/app.py
```

## Dataset

Download the approved Kaggle dataset and place the selected CSV in `data/raw/`. Do not commit dataset files or credentials. The expected input path is configured with `DIABETES_DATASET_PATH`.

### `ingest` — validate and log an ingestion of the raw file

Checks columns, target, and row count, then appends a timestamped, hashed entry to a manifest for evidence. `--source` and `--manifest` are both optional — without them, `--source` falls back to the `DIABETES_DATASET_PATH` environment variable (or `data/raw/diabetes_012_health_indicators_BRFSS2015.csv` if that isn't set), and `--manifest` falls back to `data/raw/ingestion_manifest.json`. Same command on both OSes, since it's the Python CLI, not a shell script:

```bash
# using the built-in defaults
python -m diabetes_risk.pipeline ingest

# specifying explicit paths instead of the defaults
python -m diabetes_risk.pipeline ingest --source data/raw/diabetes_012_health_indicators_BRFSS2015.csv --manifest data/raw/ingestion_manifest.json
```

### `run` — preprocess an input CSV

Cleans, imputes, and normalizes an input file (see `pipeline/preprocessing.py`), then writes `processed.csv` and `run_summary.json` to `--output-dir` (default `data/processed`). Pass `--target-column` so the label column is excluded from normalization:

```bash
python -m diabetes_risk.pipeline run data/raw/diabetes_012_health_indicators_BRFSS2015.csv --target-column Diabetes_012
```

## Project report

The shared, editable content for the final submission lives in
[`docs/report/REPORT.md`](docs/report/REPORT.md) — one file, four numbered
sections (one per team member's work package), filled in step by step
alongside `Assignment_1_Workload_Plan.md`.

## Next decisions

Before adding cloud-specific code, record the selected platform, storage, scheduler, dashboard, API set, authentication, and region in the workload plan.
