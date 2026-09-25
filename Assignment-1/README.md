# Diabetes Risk Prediction

Group 49 project for **Diabetes Risk Prediction Using Health and Lifestyle Indicators**. The repository contains a Python data pipeline, a Cloud Composer DAG, a FastAPI service, and a dashboard that reads live application data from the API.

## Project Status

- Pipeline, EDA, and optional model comparison are implemented.
- The repository DAG is configured for a two-minute schedule and currently runs data quality/preprocessing/EDA followed by Random Forest and model evaluation. A documented end-to-end run takes about 2 minutes 41 seconds; the configured schedule, observed run history, and task runtime are reported separately.
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

## Build the Assignment in Assessment Order

Use these steps to produce the deliverables listed in the assessment. Capture the
evidence as each step is completed and include it with the final written report.

### 1. Define the business problem and select the data

1. State the business problem, intended users, and how the output will be used.
   Describe this project as population-level risk screening, not diagnosis.
2. Select a public dataset that fits the problem and record its source and license.
3. Identify the target, feature columns, number of rows and columns, data types,
   value meanings, and dataset limitations. For this project, the dataset is the
   BRFSS Diabetes Health Indicators CSV and the target is `Diabetes_012`.

### 2. Ingest and profile the dataset

1. Keep the source file unchanged in `data/raw/`.
2. Run ingestion and validation:

   ```powershell
   python -m diabetes_risk.pipeline ingest
   python scripts/validate_dataset.py
   ```

3. Record the source, schema, row/column counts, target values, and ingestion
   manifest (including the file hash) in the report.

### 3. Validate and preprocess

1. Display summary statistics and data types, and check missing values.
2. Handle missing values where present; remove exact duplicate rows and record
   the number removed.
3. Encode categorical values where needed and normalize/standardize numeric data
   as appropriate for the analysis.
4. Run the pipeline and record its quality and preprocessing outputs:

   ```powershell
   python -m diabetes_risk.pipeline run data/raw/diabetes_012_health_indicators_BRFSS2015.csv --target-column Diabetes_012
   ```

5. Explain any transformations that were not needed for this dataset (for
   example, imputation when no missing values are present).

### 4. Perform and interpret EDA

Include the assessment's EDA activities in the report and show the generated
tables or charts:

1. Calculate and interpret correlations between relevant numeric and categorical
   features and the target.
2. Create univariate distributions and bivariate comparisons.
3. Bin relevant features, explain the bin boundaries, and encode the resulting
   categories where appropriate.
4. Assess and visualize feature importance. The Random Forest feature-importance
   analysis supports this requirement; the model comparison is optional.
5. State what the results mean and their limitations. Do not present this survey
   analysis as individual medical diagnosis.

### 5. Automate the pipeline and show activity on a cloud dashboard

1. Put the required preprocessing and EDA steps in the Airflow DAG in
   `dags/diabetes_risk_pipeline.py` and configure the requested two-minute
   schedule (`*/2 * * * *`).
2. Log each run's ID, timestamps, duration, status, records, errors, and warnings.
3. Deploy the workflow to Cloud Composer and verify actual consecutive runs in
   the Composer run history; a cron expression alone does not prove the cadence.
4. Show run status, timestamps/history, records processed, quality outcome, and
   errors or warnings on the cloud dashboard.
5. Record the configured two-minute schedule, the Composer run history, and the
   measured end-to-end runtime as separate execution details. In this project,
   the selected three-task run took about 2:41; optional model tasks account for
   most of that runtime.

### 6. Expose and test application details through APIs

1. Use GCP built-in APIs for real application information, such as Cloud Storage
   for pipeline artifacts and Composer for deployment/schedule details.
2. Display at least four useful application details in the dashboard. This
   project exposes them through:

   | Detail | Endpoint |
   |---|---|
   | Recent workflow history | `GET /api/v1/workflow` |
   | Latest run status and metrics | `GET /api/v1/runs/latest` |
   | Dataset and quality results | `GET /api/v1/dataset` |
   | Composer deployment and version | `GET /api/v1/schedule` |

3. Open Swagger at `/docs`, execute each request against the deployed API, and
   record the request, response, and HTTP status code. Include readable
   screenshots in the report. An endpoint listing by itself is not test evidence.

### 7. Prepare the written submission and demonstration

1. Prepare the report as a Word document with project details, explanations,
   screenshots, results, references, and each member's contribution.
2. Have all members review and confirm the contribution entries.
3. Record one video demonstrating the complete project. Upload it to a shared
   Google Drive folder, test that its viewer link works, and include the link in
   the written submission. The team plans to complete this step later.
4. Export the final report as `49.pdf` or `49.docx`, review it against the
   assessment, and submit the document and video link through the assignment
   portal.

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

The `.env.example` file contains the GCP configuration keys. Copy it once, then set the project ID and bucket to the resources you are accessing:

```powershell
cp .env.example .env
```

Use these values for the deployed project:

```dotenv
GCP_PROJECT_ID=diabetes-risk-group49
GCP_LOCATION=us-central1
GCP_COMPOSER_ENVIRONMENT=diabetes-risk-env
DIABETES_GCS_BUCKET=diabetes-risk-group49-pipeline
```

The project ID, location, Composer environment, and bucket must match the GCP resources you are accessing. The local ADC identity needs read access to the bucket and Composer environment, including the `roles/composer.user` role and Airflow permissions to read DAG runs and task instances. Composer web server access control must also allow the request. Ask the project administrator to grant these permissions if a GCP-backed endpoint returns an authorization error.

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

`/api/v1/workflow` reads the 10 most recent DAG runs from the Cloud Composer Airflow REST API. Expand a dashboard run's **Tasks** button to read its Airflow task instances. Grant the API's Cloud Run runtime service account the `roles/composer.user` role and Airflow read access; Composer web server access control must allow requests from the API service. `/api/v1/pipeline/history` separately reads recent GCS pipeline manifests (`data/outputs/execution/run_*.json`). The deploy workflow checks that `/api/v1/workflow` returns 10 DAG runs. A successful `/health` response alone does not confirm history access.

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

The assessment requires one video demonstrating the complete project, uploaded to a shared Google Drive folder. It does not specify a duration; about 5-6 minutes is a practical target for covering the required work clearly.

### Automated recording (recommended)

The `demo_video/` scripts record the whole walkthrough automatically, in about 5-6 minutes, with captions. They cover the dataset, ingestion and tests, the quality and preprocessing code, the two-minute Composer schedule, the execution log, the EDA charts, the live dashboard, and a live Swagger call on all four required routes. They work on Windows, macOS and Linux; setup details are in [demo_video/README.md](demo_video/README.md).

Quick reference, in the order you run them:

| Command | What it does |
|---|---|
| `pip install -r demo_video/requirements.txt` | One-time install of what the recorder needs: browser automation (Playwright), code highlighting, caption drawing, and microphone recording. |
| `python demo_video/record_demo.py --tts none --burn-subtitles` | Records a **fresh** full video with no voice and captions drawn on screen. |
| `python demo_video/record_voice.py` | Shows each scene's script and **records your voice** with the microphone, one scene at a time. Files are saved in `demo_video/voice/`. |
| `python demo_video/record_demo.py --tts files --burn-subtitles` | Records a fresh full video using **your recorded voice** as the narration. |
| `python demo_video/record_demo.py --clean` | **Cleans up** leftover temporary files and caches. Keeps the finished videos and your voice recordings. |
| `python demo_video/record_demo.py --clean-all` | **Last step only**, after the videos are uploaded and submitted: deletes everything generated, including the videos and voice recordings. It asks you to type `yes` first. The scripts are kept. |

The options mean:

- `--tts none`: no narration voice; captions only.
- `--tts files`: use your recordings from `demo_video/voice/`.
- `--burn-subtitles`: draw the captions on the picture, so they show everywhere, including Google Drive.
- Every recording runs fresh ingestion, tests, and the pipeline.

#### Cloud Composer: with or without Google login

Cloud Composer can appear in the video in two ways.

**Without login (default).** The Cloud Composer part shows the run-history screenshots from the report. Live Composer data still appears through the live dashboard and the Swagger `/api/v1/workflow` and `/api/v1/schedule` calls. Nothing extra is needed:

```bash
python demo_video/record_demo.py --tts none --burn-subtitles    # no voice
python demo_video/record_demo.py --tts files --burn-subtitles   # your voice
```

**With login (live Cloud Composer console).** The video opens the real Google Cloud console page, with its `console.cloud.google.com` address visible.

1. Sign in once:

   ```bash
   python demo_video/record_demo.py --login-composer
   ```

   A browser window opens. Sign in to your Google account there yourself. When the Cloud Composer page shows `diabetes-risk-env`, press Enter in the terminal. The sign-in is saved in `demo_video/output/chrome-profile/`, which is git-ignored; don't share it.

2. Record with `--composer-live` added:

   ```bash
   python demo_video/record_demo.py --tts none --burn-subtitles --composer-live    # no voice
   python demo_video/record_demo.py --tts files --burn-subtitles --composer-live   # your voice
   ```

If Google blocks the sign-in ("This browser may not be secure"), use the default commands without login; the screenshots are used instead. `--clean-all` also deletes the saved sign-in.

One-time setup, after the project setup above:

```bash
pip install -r demo_video/requirements.txt
python -m playwright install chromium
```

You also need ffmpeg: `brew install ffmpeg` on macOS, `winget install Gyan.FFmpeg` on Windows, or `sudo apt install ffmpeg libportaudio2` on Linux.

**1. Video with captions, no voice:**

```bash
python demo_video/record_demo.py --tts none --burn-subtitles
```

This produces `demo_video/output/Group49_AIMLCZG549_Assignment1_Demo_NoVoice.mp4`. Each run refreshes the ingestion, tests, and pipeline output.

**2. Record your own narration.** One person reads every scene, in order:

```bash
python demo_video/record_voice.py
```

For each scene: press Enter to start, read the script shown, and press Enter to stop. Then press Enter to keep the take, `p` to play it back, or `r` to redo it. Ctrl+C stops; running the same command again continues where you left off.

**3. Build the video with your voice:**

```bash
python demo_video/record_demo.py --tts files --burn-subtitles
```

This produces `demo_video/output/Group49_AIMLCZG549_Assignment1_Demo_TeamVoice.mp4`. The no-voice video from step 1 is kept as a separate file.

The manual recording guide below is an alternative if you prefer to present live.

### Recording setup

One person can present and record the complete walkthrough; the other members do not need to join. In OBS Studio, add a display capture and microphone source, check that both screen and microphone levels are active, then start recording. Windows Game Bar (`Win+G`) or QuickTime Player on Mac are alternatives. Save one video file with clear narration.

### Before recording

1. Open the deployed dashboard and API links in the [Deployment](#deployment) section. In Swagger, confirm the four dashboard detail routes respond successfully: `/api/v1/workflow`, `/api/v1/runs/latest`, `/api/v1/dataset`, and `/api/v1/schedule`.
2. Pre-open the pages and evidence in this order so the walkthrough flows without searching on camera:
   - Kaggle dataset page and report's dataset profile/ingestion evidence.
   - Cloud Composer DAG schedule and run history.
   - Cloud Console GCS quality, preprocessing, and execution records.
   - EDA target-distribution, feature-importance, correlation, and one bivariate chart. Keep the optional model-comparison chart ready if time allows.
   - Public dashboard and Swagger (`/docs`) on the public API URL.
3. Close notifications (Slack, email, OS banners) and unrelated tabs. Set browser zoom to ~110% so text is readable on the recording.
4. Do one full silent run-through (no recording) to check timing and page transitions.

### Recording script

1. **Introduction (20-30s)** -- give the project title, identify Group 49 and yourself as the presenter, and summarize the project as population-level analysis of diabetes indicators.
2. **Dataset and ingestion (45-60s)**
   - Show the Kaggle dataset page (or `docs/report/imgs/dataset.png`). Say: source, 253,680 rows, 22 columns, target column `Diabetes_012`.
   - Show the report's ingestion evidence. Explain that ingestion validates the source schema and row count and records a SHA-256 hash in the manifest; the raw dataset is preserved.
3. **Data quality, preprocessing, and scheduling (60-90s)**
   - Show the Cloud Composer DAG's `*/2 * * * *` schedule and recent run history. Explain the schedule interval separately from each run's end-to-end runtime.
   - Show the GCS quality and preprocessing records, then the execution record and the dashboard's quality, record, error, and warning details.
4. **EDA and optional model (60-90s)**
   - Show the target-distribution chart and state the imbalance (82.71% / 2.01% / 15.27%).
   - Show the feature-importance and correlation charts, then one bivariate chart. Explain that general health has the strongest linear correlation with the target.
   - If time allows, show the model-comparison chart and explain its limitation: Random Forest has higher accuracy but does not correctly identify the minority prediabetes class in this evaluation.
5. **Dashboard and APIs (90-120s)**
   - Show the live dashboard loading real metrics.
   - Switch to Swagger (`/docs`) on the public API URL and execute all four dashboard detail routes. Show each request, response, and HTTP status; point out that workflow history is read from Composer while processing records come from GCS.
6. **Closing (15-20s)** -- summarize the pipeline, dashboard, APIs, configured schedule, and observed runtime. Mention that team member contributions are listed in the report.

### After recording

1. Watch the full video once against the assessment topics (dataset, quality checks, preprocessing, EDA, schedule, logs, dashboard, and API requests) to confirm nothing was skipped.
2. Rename the file to something identifiable, e.g. `Group49_AIMLCZG549_Assignment1_Demo.mp4`.
3. Upload it to a shared Google Drive folder, give the assessors viewer access, and test that the link opens for a viewer who is not signed in to the recording account.
4. Add the working Drive link to the final submission document.

## Final Submission Checklist

Confirmed complete (see the report for evidence):

- [x] Business problem, dataset source, target column, and row/column counts documented.
- [x] Raw dataset ingested and validated (SHA-256 manifest).
- [x] Summary statistics, data types, and missing-value checks completed.
- [x] Preprocessing (deduplication, standardization) automated.
- [x] Correlation, univariate, bivariate, and binning analysis completed.
- [x] EDA generation automated in the revised scheduled pipeline source.
- [x] Execution logs generated.
- [x] Cloud dashboard deployed and showing live activity details.
- [x] Four required application details retrieved through APIs and tested via Swagger/OpenAPI.
- [x] API responses and HTTP status codes documented with screenshots.

Still open before submission:

- [ ] Record and upload the end-to-end demonstration video (see above).
- [ ] Verify the Google Drive sharing link works in a private/incognito window.
- [ ] Each member confirms their entry in the report's Team Contribution section.
- [ ] Export the report as `49.pdf` (or `49.docx`) from `docs/report/REPORT.md`.
- [ ] All members complete a final read-through of the report against this checklist.
- [ ] Upload to the assignment portal before 28 September 2026.

## Assignment Documents

- [Assignment report and evidence](docs/report/REPORT.md)
- [Final submission checklist](#final-submission-checklist) (this file, above)
