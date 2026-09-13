# API Layer: Calling Composer's Built-in APIs

`src/diabetes_risk/api/gcp_service.py` calls Google Cloud's own built-in
APIs (activity 3.1 of the assessment) instead of reading local files, for
the workflow/schedule/deployment endpoints. Setup needed once that
module's skeleton functions are implemented:

1. Composer environment must be running (see `../composer/README.md`).
2. Create a service account with:
   - `roles/composer.viewer` (Cloud Composer Environments API)
   - `roles/monitoring.viewer` (Cloud Monitoring API)
3. Download its key JSON and point `GOOGLE_APPLICATION_CREDENTIALS` at it
   locally (never commit the key file itself).
4. Set `GCP_PROJECT_ID`, `GCP_LOCATION`, `GCP_COMPOSER_ENVIRONMENT` in
   `.env` (see `.env.example`).
5. For the Airflow REST API calls (DAG run history, task status), follow
   Google's "Accessing the Airflow REST API" guide for Cloud Composer 2 --
   requests need an IAP-authenticated token, not just the service-account
   key used for the Composer/Monitoring APIs above.

No credentials or GCP project identifiers are committed to this
repository -- same policy as `../README.md`.
