import importlib.util
from pathlib import Path

import pytest


@pytest.mark.skipif(importlib.util.find_spec("airflow") is None, reason="Airflow is optional for local development")
def test_dag_has_two_minute_schedule_and_single_active_run() -> None:
    path = Path(__file__).parents[1] / "dags" / "diabetes_risk_pipeline.py"
    spec = importlib.util.spec_from_file_location("diabetes_risk_pipeline", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.dag.schedule_interval == "*/2 * * * *" or str(module.dag.schedule) == "*/2 * * * *"
    assert module.dag.max_active_runs == 1
