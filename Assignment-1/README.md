# Diabetes Risk Prediction

Project repository for Group 49's **Diabetes Risk Prediction Using Health and Lifestyle Indicators** assignment.

The project contains a platform-neutral Python data pipeline, a Cloud Composer deployment DAG with Google Cloud Storage hand-offs, and placeholders for the later dashboard/API work. The pipeline modules remain independent of cloud SDKs; the deployment DAG uses GCS because Composer tasks exchange datasets and artifacts through Cloud Storage.

## Current status

- **Person 1:** Complete. Business context, dataset verification, and ingestion validation are in place.
- **Person 2:** Complete, including verified Cloud Composer deployment evidence (two consecutive scheduled runs, two minutes apart, all tasks successful).
- **Person 3:** Complete. EDA interpretation (dataset overview, target distribution, feature distribution, correlation, bivariate analysis) is documented in `docs/report/REPORT.md` Section 3. An optional Random Forest vs. Logistic Regression model comparison is also implemented and evaluated, including feature importance and class-level metrics.
- **Person 4:** Pending. Dashboard, API testing, and final demonstration remain.

## Project structure

```text
src/diabetes_risk/
  api/          FastAPI application and OpenAPI endpoints
  dashboard/    FastAPI dashboard entry point
  pipeline/     Ingestion, data quality, preprocessing, EDA, runner, and logging
tests/          Focused unit/integration tests
data/           Raw, processed, and generated pipeline artifacts
dags/           Airflow DAG for Cloud Composer and GCS task hand-offs
infra/          Reserved for future infrastructure configuration
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

The two implemented functions are the reference pattern for the remaining service
work -- same configuration and credential handling, with a clean `NotImplementedError`
and HTTP 501 response until each function is complete. `get_latest_run()` and
`get_environment_health()` are intentionally retained as documented service
placeholders for future execution-log and Composer-health views:

| Placeholder | Planned responsibility | API route today |
|---|---|---|
| `local_service.get_latest_run()` | Read `data/outputs/execution/latest_run.json` from Cloud Storage | Not wired yet |
| `gcp_service.get_environment_health()` | Read Composer health metrics from Cloud Monitoring | Not wired yet |

These placeholders define the expected service contract but are not counted as
implemented features until they are connected to an endpoint and covered by tests.

**One-time GCP setup (already done for this project's own `diabetes-risk-group49` project -- repeat for a different project/account):**

1. Install the Google Cloud CLI on Windows if `gcloud` is not already available:
  ```powershell
  winget install --id Google.CloudSDK --exact
  gcloud --version
  ```
  Open a new terminal after installation so the `gcloud` command is available.
2. Confirm the Composer environment is running:
   ```bash
   gcloud composer environments describe diabetes-risk-env --location=us-central1 --project=<your-project-id>
   ```
3. Grant your Google account the three required read-only roles:
   ```bash
   gcloud projects add-iam-policy-binding <your-project-id> \
     --member="user:your-google-account@example.com" \
     --role="roles/composer.viewer"

   gcloud projects add-iam-policy-binding <your-project-id> \
     --member="user:your-google-account@example.com" \
     --role="roles/monitoring.viewer"

   gcloud projects add-iam-policy-binding <your-project-id> \
     --member="user:your-google-account@example.com" \
     --role="roles/storage.objectViewer"
   ```
4. Configure Application Default Credentials locally:
   ```bash
   gcloud auth application-default login
   ```
5. Install the GCP client libraries into the project virtualenv: `pip install -e ".[gcp]"`.
6. Copy `.env.example` to `.env` (it's gitignored) and fill in:
   ```
   GCP_PROJECT_ID=<your-project-id>
   GCP_LOCATION=us-central1
   GCP_COMPOSER_ENVIRONMENT=diabetes-risk-env
   DIABETES_GCS_BUCKET=diabetes-risk-group49-pipeline
   ```
    `GCP_LOCATION` and `GCP_COMPOSER_ENVIRONMENT` are already filled in `.env.example` for this team's environment. `DIABETES_GCS_BUCKET` is `diabetes-risk-group49-pipeline` -- this is a bucket created directly inside the `diabetes-risk-group49` project (its DAG-code default in `dags/diabetes_risk_pipeline.py`, and the Composer environment's own `DIABETES_GCS_BUCKET` Airflow environment variable, are both set to this value). An earlier bucket, `apicloudsolutions49-diabetes-pipeline`, was used briefly but turned out to belong to a *different* GCP project (`apicloudsolutions49`), where the team's account could not be granted IAM access -- do not use that bucket name. The application uses the ADC credentials created by `gcloud auth application-default login`; no credential-file path is required in `.env`.
7. Run the API (see "Run the API" above) and check `/api/v1/schedule` and `/api/v1/model` return real data, not a 501.

**Giving another teammate access:** grant their Google/BITS account the same three roles, then have them run `gcloud auth application-default login` locally:
```bash
gcloud projects add-iam-policy-binding <your-project-id> \
  --member="user:teammate@example.com" --role="roles/composer.viewer"
gcloud projects add-iam-policy-binding <your-project-id> \
  --member="user:teammate@example.com" --role="roles/monitoring.viewer"
gcloud projects add-iam-policy-binding <your-project-id> \
  --member="user:teammate@example.com" --role="roles/storage.objectViewer"
```

**Airflow REST authentication:** the DAG run history and task status calls require an IAP-authenticated token for Cloud Composer 2. This is separate from the ADC-based Google authentication used for the Composer, Monitoring, and Storage APIs. Each remaining function's docstring in `gcp_service.py`/`local_service.py` names the exact API call, required IAM role, and suggested return shape.

## GCP CI/CD deployment

The repository includes a keyless GitHub Actions deployment workflow at the
repository-root path [`.github/workflows/deploy-gcp.yml`](../.github/workflows/deploy-gcp.yml).
It must be at the repository root, not under `Assignment-1/.github/`, because
GitHub only discovers workflows from the root `.github/workflows/` directory.

Every push runs the CI job, which installs the development dependencies, runs
the tests, and compiles the Python sources. Only a successful push to `main`
continues to the build job. The build creates the Docker image and pushes it to
Artifact Registry. Deployment waits for that successful image build before
deploying two Cloud Run services:

- `diabetes-risk-api` on port 8080
- `diabetes-risk-dashboard` on port 8080, configured to call the deployed API

Cloud Composer remains responsible for the scheduled Airflow DAG. Cloud Run hosts
the API and dashboard. The workflow uses GitHub OIDC and Workload Identity
Federation; no service-account JSON key is stored in GitHub. API CORS remains `*`
for the public read-only demonstration because Cloud Run can expose a service
through more than one valid hostname; this prevents alternate dashboard URLs from
being blocked by the browser.

The workflow jobs are intentionally gated:

```text
every branch push -> ci
successful main push -> ci -> build -> deploy
failed ci -> build and deploy skipped
failed build -> deploy skipped
```

**Current GCP setup verified for this repository:**

- Project: `diabetes-risk-group49`
- Region: `us-central1`
- Cloud Composer environment: `diabetes-risk-env` (`RUNNING`)
- Artifact Registry repository: `diabetes-risk`
- Registry URI: `us-central1-docker.pkg.dev/diabetes-risk-group49/diabetes-risk`
- GitHub Workload Identity Provider:
  `projects/573458509120/locations/global/workloadIdentityPools/github/providers/github`
- GitHub deployer has `roles/artifactregistry.writer` and `roles/run.admin`.

The Artifact Registry vulnerability-scanning notice is optional and does not block
image pushes or Cloud Run deployment.

### One-time GCP CI/CD bootstrap

Run the following from PowerShell after selecting the correct GCP project. The
commands create the Artifact Registry repository, deployment identities, and the
GitHub OIDC trust for this repository. Skip resource-creation commands if the
resource already exists.

```powershell
$PROJECT_ID = "diabetes-risk-group49"
$REGION = "us-central1"
$GITHUB_REPOSITORY = "sanjaykumarpushadapu/Assignment-APIDrivenCloudNativeSolutions-AIMLCZG549"
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"

gcloud services enable run.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com sts.googleapis.com --project=$PROJECT_ID
gcloud artifacts repositories create diabetes-risk --repository-format=docker --location=$REGION --project=$PROJECT_ID

gcloud iam service-accounts create github-deployer --project=$PROJECT_ID --display-name="GitHub Actions deployer"
gcloud iam service-accounts create diabetes-risk-runtime --project=$PROJECT_ID --display-name="Diabetes Risk Cloud Run runtime"

$DEPLOYER = "github-deployer@$PROJECT_ID.iam.gserviceaccount.com"
$RUNTIME = "diabetes-risk-runtime@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$DEPLOYER" --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$DEPLOYER" --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$DEPLOYER" --role="roles/serviceusage.serviceUsageConsumer"
gcloud iam service-accounts add-iam-policy-binding $RUNTIME --member="serviceAccount:$DEPLOYER" --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$RUNTIME" --role="roles/storage.objectViewer"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$RUNTIME" --role="roles/composer.viewer"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$RUNTIME" --role="roles/monitoring.viewer"

gcloud iam workload-identity-pools create github --project=$PROJECT_ID --location=global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc github --project=$PROJECT_ID --location=global --workload-identity-pool=github --issuer-uri="https://token.actions.githubusercontent.com" --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" --attribute-condition="assertion.repository == '$GITHUB_REPOSITORY' && assertion.ref == 'refs/heads/main'"

$WIF_PROVIDER = gcloud iam workload-identity-pools providers describe github --project=$PROJECT_ID --location=global --workload-identity-pool=github --format="value(name)"
gcloud iam service-accounts add-iam-policy-binding $DEPLOYER --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$GITHUB_REPOSITORY"

Write-Output "WIF provider: $WIF_PROVIDER"
Write-Output "Deployer service account: $DEPLOYER"
Write-Output "Runtime service account: $RUNTIME"
```

Create these **GitHub repository variables** under:

```text
Settings -> Secrets and variables -> Actions -> Variables
```

They are identifiers, not secrets:

| Variable | Value |
|---|---|
| `GCP_PROJECT_ID` | `diabetes-risk-group49` |
| `GCP_REGION` | `us-central1` |
| `GCP_ARTIFACT_REPOSITORY` | `diabetes-risk` |
| `GCP_DEPLOYER_SERVICE_ACCOUNT` | `github-deployer@diabetes-risk-group49.iam.gserviceaccount.com` |
| `GCP_RUNTIME_SERVICE_ACCOUNT` | `diabetes-risk-runtime@diabetes-risk-group49.iam.gserviceaccount.com` |
| `GCP_WIF_PROVIDER` | Output of `$WIF_PROVIDER` above |
| `GCP_COMPOSER_ENVIRONMENT` | `diabetes-risk-env` |
| `DIABETES_GCS_BUCKET` | `diabetes-risk-group49-pipeline` |

To verify the provider before adding it to GitHub, run:

```powershell
gcloud iam workload-identity-pools providers describe github `
  --project=$PROJECT_ID `
  --location=global `
  --workload-identity-pool=github `
  --format="yaml(name,attributeCondition,attributeMapping,state)"
```

The `attributeCondition` must contain the exact repository name and
`refs/heads/main`. Copy the complete value from `$WIF_PROVIDER` into the
`GCP_WIF_PROVIDER` **repository variable**. Do not add it only under GitHub
Environments or use `credentials_json`; this workflow uses OIDC.

After pushing the workflow to `main`, open **Actions -> Deploy to GCP**. The
expected jobs are `ci`, `build`, and `deploy`. GitHub Actions will publish the
Cloud Run URLs in the deploy log. The dashboard URL is the public demonstration
URL and the API URL has Swagger at `/docs`.

If the build fails with `workflow must specify exactly one of
workload_identity_provider or credentials_json`, `GCP_WIF_PROVIDER` is missing,
empty, or stored in the wrong GitHub location. Add it under **Settings ->
Secrets and variables -> Actions -> Variables**, then rerun the failed workflow.

When copying PowerShell commands, copy only the command text. Do not copy the
`PS C:\...>` prompt, the `>>` continuation prompt, or command output.

For local Docker development, start both services with Compose. It builds one
shared image and runs separate API and dashboard containers. Run these commands
from the repository directory after creating `.env` from `.env.example`:

```powershell
docker compose up --build -d
docker compose ps
```

The Compose ports are `8082` for the API and `8083` for the dashboard because
port `8080` may already be used by another local container. The API container
listens internally on `8080`; Compose publishes it as host port `8082`. The
dashboard uses the same internal port and is published as host port `8083`.

### Friendly local host names

The friendly names below are local aliases only. They do not create public DNS
records and do not require a registered domain. Add both lines to the operating
system hosts file before opening the friendly URLs.

**Windows:** open Notepad or another text editor **as Administrator**, open
`C:\Windows\System32\drivers\etc\hosts` (select **All Files** if needed), and
append:

```text
127.0.0.1 diabetes-risk-group49
127.0.0.1 diabetes-risk-group49-api
```

Then flush the Windows DNS cache in an Administrator terminal:

```powershell
ipconfig /flushdns
```

**macOS:** open Terminal and edit the hosts file with administrator permission:

```bash
sudo nano /etc/hosts
```

Append the same two lines, save with `Ctrl+O`, press `Enter`, and exit with
`Ctrl+X`. Then flush the macOS DNS cache:

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Open these friendly local URLs:

- Dashboard: `http://diabetes-risk-group49:8083/`
- Swagger: `http://diabetes-risk-group49-api:8082/docs`
- API health: `http://diabetes-risk-group49-api:8082/health`

If the hosts aliases are not configured, use the equivalent localhost URLs:

- Dashboard: `http://localhost:8083/`
- Swagger: `http://localhost:8082/docs`
- API health: `http://localhost:8082/health`

To inspect startup errors:

```powershell
docker compose logs -f api dashboard
```

Stop both containers with:

```powershell
docker compose down
```

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

Open `http://127.0.0.1:8000/` in a browser. If port 8000 is unavailable, start the dashboard with `--port 8001` and open `http://127.0.0.1:8001/`. If you run the API on a different host/port, set `DIABETES_API_BASE_URL` in `.env` to match. The Schedule panel and the Model Comparison chart are backed by real GCP calls (see "GCP setup for the API layer" above) and show real data once `.env` is configured; the remaining panels correctly show "Not implemented yet" (a 501 from the API) until `gcp_service.get_dag_run_history()`/`get_task_instance_status()` and `local_service.get_dataset_quality()` are implemented.

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

The Python pipeline modules are platform-neutral. The DAG in
`dags/diabetes_risk_pipeline.py` is the Cloud Composer deployment DAG: it schedules
the complete Person-2 pipeline every two minutes with `max_active_runs=1` and uses
Cloud Storage for task-to-task dataset and artifact hand-offs. The underlying
pipeline runner can still be executed locally without Composer.

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

Cloud Logging/Monitoring can consume execution and task information for the dashboard. The Composer deployment checklist is:

1. Create a Composer environment in the approved project and region.
2. Install the project dependencies required by the pipeline.
3. Deploy `dags/diabetes_risk_pipeline.py` to the Composer DAGs folder.
4. Provide dataset and output locations through runtime configuration rather than hard-coding GCS details in the DAG.
5. Confirm the DAG appears in Airflow and is enabled.
6. Verify two consecutive scheduled runs approximately two minutes apart.
7. Capture Airflow task and log evidence for the final report.

The repository does not assume a GCP account, billing project, region, or bucket name. No credentials or GCP project identifiers are committed.

Do not commit credentials, service-account keys, or environment-specific secrets.
