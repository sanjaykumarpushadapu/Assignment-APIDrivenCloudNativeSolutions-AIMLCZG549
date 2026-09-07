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

Run the local pipeline with the sample data:

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

## Next decisions

Before adding cloud-specific code, record the selected platform, storage, scheduler, dashboard, API set, authentication, and region in the workload plan.
