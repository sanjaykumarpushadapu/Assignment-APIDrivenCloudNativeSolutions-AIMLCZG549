"""Scene list for the Group 49 demonstration video.

Each scene is one shot: what the viewer sees (``kind`` + its options) and what
the narrator says (``say``). The recorder turns every scene into one clip whose
length follows the narration, then joins them in order.

Narration placeholders such as ``{pytest_summary}`` are filled from facts
collected during the preflight step (live test results, the execution log
written moments before recording), so the narration always matches what
the video shows.

Edit any ``say`` text freely. Keep it in the third person: the narrator is a
synthesized voice, not a team member.
"""

# ---------------------------------------------------------------- live URLs
DASHBOARD_URL = "https://diabetes-risk-dashboard-573458509120.us-central1.run.app/"
API_URL = "https://diabetes-risk-api-573458509120.us-central1.run.app"
COMPOSER_URL = (
    "https://console.cloud.google.com/composer/environments/detail/"
    "us-central1/diabetes-risk-env/dags?project=diabetes-risk-group49"
)
REQUIRED_ENDPOINTS = [
    "/api/v1/workflow",
    "/api/v1/runs/latest",
    "/api/v1/dataset",
    "/api/v1/schedule",
]

# ------------------------------------------------------------------- team
MEMBERS = [
    "Pushadapu Sanjay Kumar",
    "Sathish Krishnan V",
    "Chezrla Raga Suma",
    "Bhuvnesh Mishra",
]

# Commands run live on this machine during preflight; their real output is
# shown in the terminal scenes. "{py}" is the project's virtual-env Python.
TERMINAL_COMMANDS = {
    "ingest": {
        "argv": ["{py}", "-m", "diabetes_risk.pipeline", "ingest"],
        "shown_as": "python -m diabetes_risk.pipeline ingest",
    },
    "pytest": {
        "argv": ["{py}", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:warnings"],
        "shown_as": "pytest -q",
    },
    "run": {
        "argv": [
            "{py}", "-m", "diabetes_risk.pipeline", "run",
            "data/raw/diabetes_012_health_indicators_BRFSS2015.csv",
            "--target-column", "Diabetes_012",
        ],
        "shown_as": "python -m diabetes_risk.pipeline run data/raw/diabetes_012_health_indicators_BRFSS2015.csv --target-column Diabetes_012",
    },
}
EXECUTION_LOG = "data/outputs/execution/latest_run.json"
IMAGES_DIR = "docs/report/imgs"


def part_card(number, title, member, say):
    return {
        "id": f"part{number}_card",
        "kind": "card",
        "eyebrow": f"Part {number} of 4",
        "title": title,
        "subtitle": member,
        "say": say,
    }


# Narration is kept short so the whole video runs about 5 to 6 minutes.
SCENES = [
    {
        "id": "title",
        "kind": "card",
        "eyebrow": "AIMLCZG549 · API-Driven Cloud-Native Solutions · Assignment I",
        "title": "Diabetes Risk Prediction Using Health and Lifestyle Indicators",
        "subtitle": "Group 49",
        "lines": MEMBERS,
        "footnote": "Automated screen recording · synthesized narration",
        "say": (
            "Group 49 presents Diabetes Risk Prediction Using Health and Lifestyle Indicators, "
            "for A.I.M.L. C.Z.G. 5 4 9, Assignment One. The team: Pushadapu Sanjay Kumar, "
            "Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra."
        ),
    },
    {
        "id": "architecture",
        "kind": "image",
        "images": ["architecture.png"],
        "caption": "Architecture: Cloud Composer → Cloud Storage → FastAPI → Dashboard",
        "say": (
            "The architecture: a Python pipeline runs on Cloud Composer, Google Cloud's managed Airflow, "
            "every two minutes. Results go to Cloud Storage, a FastAPI service on Cloud Run exposes them "
            "as APIs, and the dashboard reads from those APIs."
        ),
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1, "Business Understanding, Dataset & Ingestion", MEMBERS[0],
        "Part one, by Pushadapu Sanjay Kumar: the business problem. Reviewing health records by hand "
        "doesn't scale, so people at risk of diabetes are flagged late. This pipeline turns health and "
        "lifestyle data into an automated risk-screening signal.",
    ),
    {
        "id": "dataset",
        "kind": "image",
        "images": ["dataset.png"],
        "caption": "Kaggle — Diabetes Health Indicators Dataset (CDC BRFSS 2015)",
        "say": (
            "The dataset is the Kaggle Diabetes Health Indicators dataset, based on the C.D.C.'s 2015 "
            "B.R.F.S.S. survey: 253,680 records and 22 columns, with the target Diabetes 0 1 2 for no "
            "diabetes, prediabetes, and diabetes."
        ),
    },
    {
        "id": "ingest_terminal",
        "kind": "terminal",
        "commands": ["ingest", "pytest"],
        "say": (
            "Ingestion checks the schema and row count and records a SHA-256 hash in a manifest, so the "
            "raw file is never modified and any swap would be detected. Test results: {pytest_summary}."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2, "Data Quality, Preprocessing & Scheduling", MEMBERS[1],
        "Part two, by Sathish Krishnan V: data quality, preprocessing, and the two-minute schedule.",
    ),
    {
        "id": "quality_code",
        "kind": "code",
        "file": "src/diabetes_risk/pipeline/data_quality.py",
        "functions": ["run_data_quality", "validate_numeric_ranges"],
        "caption": "data_quality.py — automated quality checks",
        "say": (
            "On every run, the data-quality module checks the schema, target values, numeric ranges, and "
            "binary columns, and reports data types, summary statistics, and missing values. There are no "
            "missing values, but 23,899 duplicate rows."
        ),
    },
    {
        "id": "preprocess_code",
        "kind": "code",
        "file": "src/diabetes_risk/pipeline/preprocessing.py",
        "functions": ["impute_missing", "remove_exact_duplicates", "standardize_numeric"],
        "caption": "preprocessing.py — imputation, deduplication, standardization",
        "say": (
            "Preprocessing imputes missing numbers with the median, removes duplicates, leaving 229,781 "
            "records, and standardizes the continuous columns."
        ),
    },
    {
        "id": "dag_code",
        "kind": "code",
        "file": "dags/diabetes_risk_pipeline.py",
        "regex": r'schedule="\*/2',
        "window": [-13, 45],
        "highlight": r"schedule=|max_active_runs|catchup|>>",
        "caption": "Cloud Composer DAG — schedule=\"*/2 * * * *\"",
        "say": (
            "An Airflow DAG automates this. The schedule is every two minutes, with catch-up off and one "
            "active run at a time, so runs never overlap. It runs three tasks: quality, preprocessing and "
            "E.D.A., then the Random Forest, then model evaluation."
        ),
    },
    {
        "id": "composer",
        "kind": "composer",
        "url": COMPOSER_URL,
        "images": ["DAG-img-1.png", "DAG-List-IMG-2.png"],
        "caption": "Cloud Composer (console.cloud.google.com) — scheduled run history, diabetes-risk-env",
        "say": (
            "In Cloud Composer, scheduled runs appear about two minutes apart. If training overruns, the "
            "next slot is skipped rather than overlapped, as noted in the report."
        ),
    },
    {
        "id": "execution_log",
        "kind": "json",
        "file": EXECUTION_LOG,
        "caption": "Execution log written by the run moments ago",
        "say": (
            "Every run writes an execution log. This one, from just before recording: status {run_status}, "
            "{input_rows} rows in, {output_rows} out, {duplicates} duplicates removed, in {duration} seconds."
        ),
    },
    # ------------------------------------------------------------- Part 3
    part_card(
        3, "Exploratory Data Analysis & Optional Model", MEMBERS[2],
        "Part three, by Chezrla Raga Suma: exploratory data analysis and the optional model.",
    ),
    {
        "id": "target_distribution",
        "kind": "image",
        "images": ["p3-target-distribution-refreshed.png"],
        "caption": "Target distribution — 82.71% / 2.01% / 15.27%",
        "say": (
            "The target is very imbalanced: 82.71 percent no diabetes, 2.01 percent prediabetes, and 15.27 "
            "percent diabetes. So accuracy alone isn't a fair measure."
        ),
    },
    {
        "id": "correlation",
        "kind": "image",
        "images": ["p3-correlation-analysis.png", "p3-bivariate-analysis.png", "p3-feature-distribution.png"],
        "caption": "Correlation, bivariate and univariate analysis",
        "say": (
            "General health has the strongest correlation with diabetes, at 0.285, followed by high blood "
            "pressure, B.M.I., and cholesterol, while physical activity is negative. Age and B.M.I. are also "
            "binned and one-hot encoded on every run."
        ),
    },
    {
        "id": "feature_importance",
        "kind": "image",
        "images": ["p3-feature-importance.png"],
        "caption": "Random Forest feature importance",
        "say": (
            "The Random Forest ranks B.M.I., age, and income as most important. This measure favours "
            "wide-range features, so it differs from the correlation ranking."
        ),
    },
    {
        "id": "model_comparison",
        "kind": "image",
        "images": ["p3-model-comparison.png"],
        "caption": "Optional: Random Forest vs. Logistic Regression",
        "say": (
            "As an optional extra, it is compared with a balanced Logistic Regression. The Random Forest "
            "reaches 82.5 percent accuracy but never correctly predicts prediabetes; Logistic Regression "
            "catches about 30 percent, with low precision. Neither is ready for real screening."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4, "Cloud Dashboard & APIs", MEMBERS[3],
        "Part four, by Bhuvnesh Mishra: the cloud dashboard and APIs.",
    ),
    {
        "id": "live_links",
        "kind": "links",
        "title": "Live on Google Cloud",
        "links": [
            ("Dashboard (Cloud Run)", DASHBOARD_URL),
            ("API + Swagger docs (Cloud Run)", API_URL + "/docs"),
            ("Cloud Composer environment", "console.cloud.google.com/composer · diabetes-risk-env · us-central1"),
            ("Cloud Storage bucket", "gs://diabetes-risk-group49-pipeline"),
            ("GCP project", "diabetes-risk-group49"),
        ],
        "caption": "Deployed resources — every URL in this part is the live deployment",
        "say": (
            "Everything is deployed on Google Cloud: the dashboard and the API run on Cloud Run at these "
            "public URLs, the pipeline runs in the Cloud Composer environment, and its outputs are stored "
            "in this Cloud Storage bucket."
        ),
    },
    {
        "id": "dashboard",
        "kind": "url",
        "url": DASHBOARD_URL,
        "scroll": True,
        "caption": "Live Cloud Run dashboard",
        "say": (
            "The live dashboard on Cloud Run shows pipeline status and runtime, records processed, "
            "duplicates removed, quality status, errors, warnings, and run history. All values come live "
            "from the API."
        ),
    },
    {
        "id": "swagger_intro",
        "kind": "url",
        "url": API_URL + "/docs",
        "wait_for": ".opblock",
        "caption": "Swagger / OpenAPI — live API",
        "say": "The API is documented in Swagger. The four required endpoints are now tested live.",
    },
    {
        "id": "api_workflow",
        "kind": "swagger",
        "path": "/api/v1/workflow",
        "say": (
            "First, the workflow endpoint: recent pipeline runs with status and timing. "
            "HTTP {status_/api/v1/workflow}."
        ),
    },
    {
        "id": "api_runs_latest",
        "kind": "swagger",
        "path": "/api/v1/runs/latest",
        "say": (
            "Second, the latest run: status, duration, record counts, errors, and warnings. "
            "HTTP {status_/api/v1/runs/latest}."
        ),
    },
    {
        "id": "api_dataset",
        "kind": "swagger",
        "path": "/api/v1/dataset",
        "say": (
            "Third, dataset details: row counts, duplicates removed, missing values, and quality status. "
            "HTTP {status_/api/v1/dataset}."
        ),
    },
    {
        "id": "api_schedule",
        "kind": "swagger",
        "path": "/api/v1/schedule",
        "say": (
            "Fourth, schedule and deployment details from Cloud Composer: environment state and Airflow "
            "version. HTTP {status_/api/v1/schedule}."
        ),
    },
    {
        "id": "closing",
        "kind": "card",
        "eyebrow": "Group 49 · AIMLCZG549 Assignment I",
        "title": "Implemented, deployed on Google Cloud, and verified live",
        "lines": MEMBERS,
        "say": (
            "To summarise: the pipeline runs every two minutes on Cloud Composer, is logged and shown on a "
            "cloud dashboard, and its key details are available through tested APIs. Thank you for watching."
        ),
    },
]

# ---------------------------------------------------------------------------
# Student-style script for your own voice (record_voice.py, --tts files).
# One person reads every scene, crediting each member's part. The synthesized
# narrator never uses these. No {placeholders}: record on any computer.
# ---------------------------------------------------------------------------
SELF_SCRIPTS = {
    "title": (
        "Hello everyone! We're Group 49, and this is our project for AIMLCZG549, Assignment One: "
        "Diabetes Risk Prediction Using Health and Lifestyle Indicators. Our team is Pushadapu Sanjay Kumar, "
        "Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra."
    ),
    "architecture": (
        "Here's our architecture. A Python pipeline runs on Cloud Composer, Google Cloud's managed Airflow, "
        "every two minutes. Results go to Cloud Storage, a FastAPI service on Cloud Run exposes them as APIs, "
        "and our dashboard reads from those APIs."
    ),
    "part1_card": (
        "Part one, by Sanjay, is the business problem. Reviewing health records by hand doesn't scale, so "
        "people at risk of diabetes are flagged late. Our pipeline turns health and lifestyle data into an "
        "automated risk-screening signal."
    ),
    "dataset": (
        "We used the Diabetes Health Indicators dataset from Kaggle, based on the CDC's 2015 BRFSS survey: "
        "253,680 records and 22 columns, with the target Diabetes_012 for no diabetes, prediabetes, "
        "and diabetes."
    ),
    "ingest_terminal": (
        "Ingestion checks the schema and row count and logs a SHA-256 hash in a manifest, so the raw file is "
        "never modified and any swap would be detected. And here are our automated test results."
    ),
    "part2_card": (
        "Part two, by Sathish, covers data quality, preprocessing, and the two-minute schedule."
    ),
    "quality_code": (
        "On every run, our data-quality module checks the schema, target values, numeric ranges, and binary "
        "columns, and reports data types, summary statistics, and missing values. There are no missing values, "
        "but 23,899 duplicate rows."
    ),
    "preprocess_code": (
        "Preprocessing imputes missing numbers with the median, removes duplicates, leaving 229,781 records, "
        "and standardizes the continuous columns."
    ),
    "dag_code": (
        "To automate this, we built an Airflow DAG. The schedule is every two minutes, with catch-up off and "
        "one active run at a time, so runs never overlap. It runs three tasks: quality, preprocessing and EDA, "
        "then the Random Forest, then model evaluation."
    ),
    "composer": (
        "Here it is in Cloud Composer, with scheduled runs about two minutes apart. If training overruns, the "
        "next slot is skipped rather than overlapped, as noted in our report."
    ),
    "execution_log": (
        "Every run writes an execution log like this one, with the status, row counts, duplicates removed, "
        "and run time."
    ),
    "part3_card": (
        "Part three, by Raga Suma, is exploratory data analysis and the optional model."
    ),
    "target_distribution": (
        "The target is very imbalanced: 82.71 percent no diabetes, 2.01 percent prediabetes, and 15.27 "
        "percent diabetes. So accuracy alone isn't a fair measure."
    ),
    "correlation": (
        "General health has the strongest correlation with diabetes, at 0.285, followed by high blood "
        "pressure, BMI, and cholesterol, while physical activity is negative. We also bin and one-hot encode "
        "age and BMI on every run."
    ),
    "feature_importance": (
        "Our Random Forest ranks BMI, age, and income as most important. This measure favours wide-range "
        "features, so it differs from the correlation ranking."
    ),
    "model_comparison": (
        "As an optional extra, we compared it with a balanced Logistic Regression. The Random Forest reaches "
        "82.5 percent accuracy but never correctly predicts prediabetes; Logistic Regression catches about "
        "30 percent, with low precision. So neither is ready for real screening."
    ),
    "part4_card": (
        "Part four, by Bhuvnesh, is the cloud dashboard and APIs."
    ),
    "live_links": (
        "Everything is deployed on Google Cloud. The dashboard and the API run on Cloud Run at these public "
        "URLs, the pipeline runs in our Cloud Composer environment, and the outputs are stored in this "
        "Cloud Storage bucket."
    ),
    "dashboard": (
        "This is our live dashboard on Cloud Run: pipeline status and runtime, records processed, duplicates "
        "removed, quality status, errors, warnings, and run history. All values come live from our API."
    ),
    "swagger_intro": (
        "The API is documented in Swagger. Let's test the four required endpoints live."
    ),
    "api_workflow": (
        "First, the workflow endpoint: recent pipeline runs with status and timing. HTTP 200."
    ),
    "api_runs_latest": (
        "Second, the latest run: status, duration, record counts, errors, and warnings. 200."
    ),
    "api_dataset": (
        "Third, dataset details: row counts, duplicates removed, missing values, and quality status. 200 again."
    ),
    "api_schedule": (
        "And fourth, the schedule and deployment details from Cloud Composer: environment state and Airflow "
        "version. Also 200."
    ),
    "closing": (
        "To wrap up: our pipeline runs every two minutes on Cloud Composer, it's logged and shown on a cloud "
        "dashboard, and its key details are available through tested APIs. Thank you!"
    ),
}
