# Diabetes Risk Prediction

Group 49 project for **Diabetes Risk Prediction Using Health and Lifestyle Indicators**. The repository contains a Python data pipeline, a Cloud Composer DAG, a FastAPI service, and a dashboard that reads live application data from the API.

## Project Status

- Pipeline, EDA, and optional model comparison are implemented.
- The Cloud Composer DAG is deployed on a two-minute schedule; current evidence is recorded in the report.
- The API and dashboard are deployed to Cloud Run. API and dashboard evidence is recorded in the report.
- The final demonstration video, member confirmation of the contribution summary, report export, team review, and portal submission remain outstanding. The deadline was originally 18 September 2026; the team has confirmed 28 September 2026 as the last working day for submission.

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

## Demonstration Video

The PDF requires one video demonstrating the entire project, uploaded to a shared Google Drive link (no required length or format). Target 5-7 minutes: long enough to cover every required activity, short enough to stay watchable.

### Recording setup

Pick whichever is easier for the team -- both produce one acceptable video file.

**Option A -- one Zoom/Google Meet call (recommended, no editing needed)**

1. Start a call with all four members.
2. One member starts local recording (Zoom: **Record** -> **Record on this Computer**).
3. Each member shares their screen in turn for their own section below, then hands off to the next person.
4. Stop recording after the closing sentence. This produces a single `.mp4` file -- no clips to merge.

**Option B -- record each section separately, then combine**

1. Each person records their own screen with OBS Studio (free, Windows/Mac/Linux), the Windows Game Bar (`Win+G`), or QuickTime Player's screen recording (Mac).
2. Combine the four clips in order with a simple free editor -- Clipchamp (Windows, built-in), iMovie (Mac, built-in), or OpenShot (cross-platform, free).

### Before recording

1. Re-verify all 4 required live endpoints return 200 the same day you record (`/api/v1/workflow`, `/api/v1/runs/latest`, `/api/v1/dataset`, `/api/v1/schedule` on the deployed API URL above) -- screenshots and old checks go stale.
2. Agree on speaking order (Person 1 -> 2 -> 3 -> 4) and who hosts/records.
3. Each person pre-opens their own tabs/windows before recording starts, so there's no dead time searching for a page on camera:
   - Person 1: the Kaggle dataset page, and a terminal/screenshot showing the ingestion run.
   - Person 2: `data_quality.py`/`preprocessing.py` in an editor, and the Cloud Composer console DAG view.
   - Person 3: the EDA charts (target distribution, correlation, one bivariate) and the model-comparison chart.
   - Person 4: the live dashboard URL, and Swagger (`/docs`) on the live API URL.
4. Close notifications (Slack, email, OS banners) and unrelated tabs. Set browser zoom to ~110% so text is readable on the recording.
5. Do one full silent run-through (no recording) to check timing and hand-offs between people.

### Recording script

1. **Introduction (30s)** -- title, "Group 49", all four members introduce themselves by name, one sentence on the business problem (early diabetes-risk screening from health and lifestyle data).
2. **Person 1 -- dataset and ingestion (45-60s)**
   - Show the Kaggle dataset page (or `docs/report/imgs/dataset.png`). Say: source, 253,680 rows, 22 columns, target column `Diabetes_012`.
   - Switch to the terminal/screenshot showing the ingestion run and passing tests. Say: the raw file is never modified -- each run appends a timestamped SHA-256 record to the manifest, so a swapped file would be detected.
3. **Person 2 -- preprocessing and scheduling (60-90s)**
   - Briefly scroll (don't read line-by-line) through `data_quality.py` / `preprocessing.py`.
   - Switch to the live Cloud Composer console DAG view. Point at two consecutive scheduled runs roughly two minutes apart to prove the `*/2 * * * *` schedule is real, not just configured.
   - Briefly show one execution-log JSON file.
4. **Person 3 -- EDA and optional model (60-90s)**
   - Show the target-distribution chart and state the imbalance out loud (82.71% / 2.01% / 15.27%).
   - Show the correlation chart and one bivariate chart, naming the strongest association (general health).
   - Show the model-comparison chart. Say clearly: this model is a bonus, not a grading requirement, and flag the honest finding -- Random Forest has higher accuracy but never predicts the minority class.
5. **Person 4 -- dashboard and APIs (90-120s)**
   - Show the live dashboard loading real metrics.
   - Switch to Swagger (`/docs`) on the live API URL and actually click **Try it out -> Execute** on all 4 required endpoints live (not a pre-made screenshot). Read one HTTP `200` response out loud.
6. **Closing (15-20s)** -- one sentence: all required work is implemented, deployed on GCP, and verified live; thank the viewer.

### After recording

1. If using Option B, add each person's name as a title card/caption at the start of their section, so individual contribution is visible on the video itself, separate from the report's contribution table.
2. Watch the full video once against the PDF's required list (dataset, quality checks, preprocessing, EDA, schedule, logs, dashboard, 4 APIs) to confirm nothing was skipped.
3. Rename the file to something identifiable, e.g. `Group49_AIMLCZG549_Assignment1_Demo.mp4`.
4. Upload it to a shared Google Drive folder, set sharing to "Anyone with the link -- Viewer," and test the link in a private/incognito browser window (logged out) before calling it done.
5. Add the working Drive link to the final submission document.

## Final Submission Checklist

Confirmed complete (see the report for evidence):

- [x] Business problem, dataset source, target column, and row/column counts documented.
- [x] Raw dataset ingested and validated (SHA-256 manifest).
- [x] Summary statistics, data types, and missing-value checks completed.
- [x] Preprocessing (deduplication, standardization) automated.
- [x] Correlation, univariate, bivariate, and binning analysis completed.
- [x] EDA generation automated and refreshed on schedule.
- [x] Workflow deployed to Cloud Composer, running every two minutes.
- [x] Execution logs generated.
- [x] Cloud dashboard deployed and showing live activity details.
- [x] Four required application details retrieved through APIs and tested via Swagger/OpenAPI.
- [x] API responses and HTTP status codes documented with screenshots.

Still open before submission:

- [ ] Record and upload the end-to-end demonstration video (see above).
- [ ] Verify the Google Drive sharing link works in a private/incognito window.
- [ ] Each member confirms their entry in the report's contribution summary (Section 4.3).
- [ ] Export the report as `49.pdf` (or `49.docx`) from `docs/report/REPORT.md`.
- [ ] All members complete a final read-through of the report against this checklist.
- [ ] Upload to the assignment portal before 28 September 2026.

## Assignment Documents

- [Assignment report and evidence](docs/report/REPORT.md)
- [Final submission checklist](#final-submission-checklist) (this file, above)
