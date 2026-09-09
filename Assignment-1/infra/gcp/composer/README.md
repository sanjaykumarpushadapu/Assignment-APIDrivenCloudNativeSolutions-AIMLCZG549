# Cloud Composer Deployment Notes

1. Create a Composer environment in the approved project/region.
2. Install the project dependencies required by the pipeline.
3. Deploy `dags/diabetes_risk_pipeline.py` to the Composer DAGs folder.
4. Provide dataset/output locations through environment/runtime configuration rather than hard-coding GCS details in the DAG.
5. Confirm the DAG appears in Airflow and is enabled.
6. Verify two consecutive scheduled runs approximately two minutes apart.
7. Capture Airflow task/log evidence for the final assignment report.

The current repository does not assume a GCP account, billing project, region or bucket name.
