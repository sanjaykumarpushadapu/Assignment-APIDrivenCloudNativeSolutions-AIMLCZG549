import json

import pandas as pd
import pytest

from diabetes_risk.pipeline.ingestion import EXPECTED_COLUMNS, IngestionError, ingest


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame({column: [0.0, 1.0] for column in EXPECTED_COLUMNS})


def test_ingest_accepts_a_valid_file_and_writes_manifest(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    _valid_frame().to_csv(source, index=False)
    manifest_path = tmp_path / "ingestion_manifest.json"

    report = ingest(source, manifest_path)

    assert report.target_present is True
    assert report.columns_match_expected is True
    assert report.row_count == 2
    assert manifest_path.exists()

    history = json.loads(manifest_path.read_text())
    assert len(history) == 1
    assert history[0]["sha256"] == report.sha256


def test_ingest_appends_to_existing_manifest(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    _valid_frame().to_csv(source, index=False)
    manifest_path = tmp_path / "ingestion_manifest.json"

    ingest(source, manifest_path)
    ingest(source, manifest_path)

    history = json.loads(manifest_path.read_text())
    assert len(history) == 2


def test_ingest_rejects_missing_target_column(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    frame = _valid_frame().drop(columns=["Diabetes_012"])
    frame.to_csv(source, index=False)

    with pytest.raises(IngestionError, match="Target column"):
        ingest(source, tmp_path / "manifest.json")


def test_ingest_rejects_missing_feature_column(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    frame = _valid_frame().drop(columns=["BMI"])
    frame.to_csv(source, index=False)

    with pytest.raises(IngestionError, match="Missing expected columns"):
        ingest(source, tmp_path / "manifest.json")


def test_ingest_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(IngestionError, match="not found"):
        ingest(tmp_path / "does_not_exist.csv", tmp_path / "manifest.json")
