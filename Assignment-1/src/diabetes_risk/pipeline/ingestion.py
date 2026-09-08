"""Raw data ingestion for the approved Kaggle dataset (rubric 1.2 / plan Step 7).

Validates the raw CSV against the dataset profile recorded in
``docs/report/REPORT.md`` (exact columns, target column, expected row
count) *without* mutating or duplicating the raw file, then appends a
timestamped, hash-verified entry to an ingestion manifest so the team has
a durable record of when the file was imported and that it hasn't
silently changed between runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# The exact column order confirmed against the raw CSV (see REPORT.md,
# section 1.5 "Data dictionary"). Used both to check nothing is missing
# and, via ``columns_match_expected`` below, to catch a silently reordered
# or renamed file that still happens to contain every column name.
EXPECTED_COLUMNS = [
    "Diabetes_012",
    "HighBP",
    "HighChol",
    "CholCheck",
    "BMI",
    "Smoker",
    "Stroke",
    "HeartDiseaseorAttack",
    "PhysActivity",
    "Fruits",
    "Veggies",
    "HvyAlcoholConsump",
    "AnyHealthcare",
    "NoDocbcCost",
    "GenHlth",
    "MentHlth",
    "PhysHlth",
    "DiffWalk",
    "Sex",
    "Age",
    "Education",
    "Income",
]
# The prediction target (0 = no diabetes, 1 = prediabetes, 2 = diabetes).
# Checked separately from EXPECTED_COLUMNS so a missing target produces a
# clearer error message than a generic "missing columns" list would.
TARGET_COLUMN = "Diabetes_012"
# Row count verified against the raw file during Person 1's Step 4
# (see REPORT.md, section 1.4). Used only as an informational flag, not a
# hard failure -- see the note in ``ingest()`` below.
EXPECTED_ROW_COUNT = 253_680


class IngestionError(RuntimeError):
    """Raised when the raw dataset fails validation.

    Kept as a single, specific exception type (rather than letting a
    pandas/OS error propagate directly) so callers -- and the CLI's error
    output -- can rely on one consistent, readable failure mode.
    """


@dataclass
class IngestionReport:
    """One ingestion run's result. Serialized to JSON and appended to the
    manifest file, so every field here becomes a permanent evidence record."""

    source_path: str
    imported_at: str
    sha256: str
    row_count: int
    column_count: int
    columns_match_expected: bool
    target_present: bool
    row_count_matches_expected: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256(path: Path) -> str:
    """Hash the file in fixed-size chunks rather than reading it whole,
    so this stays memory-light even though the raw CSV is ~23 MB."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest(source_path: Path, manifest_path: Path) -> IngestionReport:
    """Validate the raw dataset and append an entry to the ingestion manifest.

    Raises ``IngestionError`` if the file is missing, unreadable, missing
    the target column, or missing any expected feature column. A row-count
    mismatch against ``EXPECTED_ROW_COUNT`` is recorded but does not raise,
    since a differently-filtered export of the same source is still usable
    -- the manifest entry makes any such drift visible for review.
    """
    # Fail fast with a clear message rather than letting pandas raise a
    # less obvious "file not found" error further down.
    if not source_path.exists():
        raise IngestionError(f"Raw dataset not found at {source_path}")

    try:
        frame = pd.read_csv(source_path)
    except Exception as exc:  # noqa: BLE001 - surface the real parser error
        # Catches anything from a malformed CSV to a permissions error,
        # and re-raises it as our own error type with the original
        # exception preserved via ``from exc`` for debugging.
        raise IngestionError(f"Failed to read {source_path}: {exc}") from exc

    # The target column is checked on its own (before the general column
    # check) so a missing target produces an unambiguous, specific error
    # rather than being buried in a list of missing feature columns.
    target_present = TARGET_COLUMN in frame.columns
    if not target_present:
        raise IngestionError(f"Target column '{TARGET_COLUMN}' missing from {source_path}")

    # Check every expected feature column is present. This does *not*
    # check for extra/unexpected columns -- an export with additional
    # metadata columns is still usable, just noted via
    # ``columns_match_expected`` in the report below.
    missing = [c for c in EXPECTED_COLUMNS if c not in frame.columns]
    if missing:
        raise IngestionError(f"Missing expected columns in {source_path}: {missing}")

    # Build the full evidence record for this run. Everything here is
    # derived from the file itself (never assumed), so the manifest is a
    # trustworthy audit trail rather than a restatement of expectations.
    report = IngestionReport(
        source_path=str(source_path),
        imported_at=datetime.now(timezone.utc).isoformat(),
        sha256=_sha256(source_path),
        row_count=len(frame),
        column_count=len(frame.columns),
        columns_match_expected=list(frame.columns) == EXPECTED_COLUMNS,
        target_present=target_present,
        row_count_matches_expected=len(frame) == EXPECTED_ROW_COUNT,
    )

    # Append (never overwrite) so the manifest accumulates a full history
    # of every ingestion run -- useful both as "raw data is preserved"
    # evidence and for spotting drift (a changed hash/row count) over time.
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, object]] = []
    if manifest_path.exists():
        history = json.loads(manifest_path.read_text(encoding="utf-8"))
    history.append(report.as_dict())
    manifest_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    return report


def main() -> None:
    """CLI entry point: `python -m diabetes_risk.pipeline.ingestion [--source ...] [--manifest ...]`.

    Defaults read ``DIABETES_DATASET_PATH`` from the environment (see
    `.env.example`) so this can run unconfigured with sensible defaults,
    or be pointed at a different file/manifest for testing. ``load_dotenv()``
    reads a local ``.env`` file (if one exists) into the environment first,
    so a value set there is picked up the same way an exported shell
    variable would be -- without it, ``.env`` would just be an inert text
    file that nothing actually reads.
    """
    load_dotenv()
    parser = argparse.ArgumentParser(description="Validate and log an ingestion of the raw dataset.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(os.environ.get("DIABETES_DATASET_PATH", "data/raw/diabetes_012_health_indicators_BRFSS2015.csv")),
    )
    parser.add_argument("--manifest", type=Path, default=Path("data/raw/ingestion_manifest.json"))
    args = parser.parse_args()

    report = ingest(args.source, args.manifest)
    # Printed as JSON (not a human-readable summary) so this output can be
    # captured directly as evidence or piped into another tool if needed.
    print(json.dumps(report.as_dict(), indent=2))


if __name__ == "__main__":
    main()
