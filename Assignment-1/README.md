# Diabetes Risk Prediction

Group 49 project for **Diabetes Risk Prediction Using Health and Lifestyle Indicators**. The repository contains a Python data pipeline, a Cloud Composer DAG, a FastAPI service, and a dashboard that reads live application data from the API.

## Project Status

- Pipeline, EDA, and optional model comparison are implemented.
- The Cloud Composer DAG is deployed on a two-minute schedule; current evidence is recorded in the report.
- The API and dashboard are deployed to Cloud Run. API and dashboard evidence is recorded in the report.
- The final demonstration video, member confirmation of the contribution summary, report export, team review, and portal submission remain outstanding. The deadline recorded in the workload plan was 18 September 2026 and has passed.

## Project Layout

```text
src/diabetes_risk/api/       FastAPI routes and GCP-backed services
src/diabetes_risk/dashboard/ Activity dashboard
src/diabetes_risk/pipeline/  Ingestion, quality, preprocessing, EDA, and models
dags/                        Cloud Composer DAG
tests/                       Automated tests
data/                        Raw and processed datasets
docs/report/REPORT.md        Assignment report and evidence
```

## Requirements

- Python 3.11 or newer
- Optional: Docker Desktop and Docker Compose for containerized local services
- Optional: Google Cloud CLI and ADC credentials for local access to GCP-backed API data

## Setup

From this directory, create and activate a virtual environment, then install the development dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

The default dataset and output paths are defined in `.env.example`. The raw dataset is `data/raw/diabetes_012_health_indicators_BRFSS2015.csv` (253,680 rows, 22 columns; target: `Diabetes_012`).

For local API access to Cloud Storage and Composer, configure Google Application Default Credentials and install the optional GCP dependencies:

```powershell
gcloud auth application-default login
pip install -e ".[gcp]"
```

### Local GCP Configuration

The `.env.example` file contains the project's current GCP settings. Copy it once, then set the project ID if it is blank:

```powershell
Copy-Item .env.example .env
```

Use these values for the deployed project:

```dotenv
GCP_PROJECT_ID=diabetes-risk-group49
GCP_LOCATION=us-central1
GCP_COMPOSER_ENVIRONMENT=diabetes-risk-env
GCP_IAP_SERVICE_ACCOUNT=diabetes-risk-runtime@diabetes-risk-group49.iam.gserviceaccount.com
DIABETES_GCS_BUCKET=diabetes-risk-group49-pipeline
```

The project ID, location, Composer environment, and bucket must match the GCP resources you are accessing. `GCP_IAP_SERVICE_ACCOUNT` is used for optional Composer Airflow REST task/run inspection. The GCP identity used locally needs read access to the bucket and Composer environment; direct Airflow REST access additionally requires permission to impersonate the configured runtime service account. Ask the project administrator to grant the appropriate roles if an API returns permission errors.

The Google libraries use ADC from `gcloud auth application-default login`; do not put credentials, access tokens, or credential-file paths in `.env` or source control. The complete example, including local dashboard/API settings, is in `.env.example`.

For IAM role setup and deployment details, use the repository's deployment configuration and assignment report rather than copying one-time resource-creation commands into a local environment.

## Run the Pipeline

```powershell
python -m diabetes_risk.pipeline --help
python -m diabetes_risk.pipeline ingest
python -m diabetes_risk.pipeline run data/raw/diabetes_012_health_indicators_BRFSS2015.csv --target-column Diabetes_012
```

The run command validates and preprocesses the data, creates the cleaned and model-ready datasets, generates EDA artifacts, and writes execution logs.

The optional model comparison is run after preprocessing:

```powershell
python -m diabetes_risk.pipeline randomforestclassifier
python -m diabetes_risk.pipeline model_evaluation
```

Run the automated tests with:

```powershell
pytest
```

## Run the API and Dashboard

Start each service in a separate terminal:

```powershell
uvicorn diabetes_risk.api.main:app --reload --host 127.0.0.1 --port 9000
uvicorn diabetes_risk.dashboard.app:app --reload --host 127.0.0.1 --port 8000
```

- Dashboard: <http://127.0.0.1:8000/>
- API health: <http://127.0.0.1:9000/health>
- Swagger/OpenAPI: <http://127.0.0.1:9000/docs>

The four required application-detail endpoints are `/api/v1/workflow`, `/api/v1/runs/latest`, `/api/v1/dataset`, and `/api/v1/schedule`. `/api/v1/model` provides optional model-comparison details.

## Docker Compose

After creating `.env`, start the API and dashboard containers from this directory:

```powershell
docker compose up --build -d
```

Compose exposes the API on port `8082` and dashboard on port `8083`. Stop the services with `docker compose down`.

## Deployment

Cloud Composer runs the scheduled DAG. Cloud Run hosts the API and dashboard. The repository-root `.github/workflows/deploy-gcp.yml` contains the CI/CD workflow, using GitHub OIDC for deployment authentication.

- Dashboard: <https://diabetes-risk-dashboard-573458509120.us-central1.run.app/>
- API health: <https://diabetes-risk-api-573458509120.us-central1.run.app/health>
- Swagger/OpenAPI: <https://diabetes-risk-api-573458509120.us-central1.run.app/docs>

## Assignment Documents

- [Assignment report and evidence](docs/report/REPORT.md)
- [Workload plan and submission checklist](Assignment_1_Workload_Plan.md)
