"""Preprocessing-stage runner: reads an input CSV, preprocesses it, and
writes the cleaned output plus a run summary.

Only the ``run()`` function lives here -- command-line wiring is
handled centrally by ``cli.py`` so every pipeline stage is invoked the
same way (see that module's docstring).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .preprocessing import preprocess


def run(input_path: Path, output_dir: Path, target_column: str | None = None) -> dict[str, object]:
    """Run preprocessing on ``input_path`` and write the cleaned CSV plus a summary.

    ``preprocess()`` returns ``(cleaned_dataframe, report)`` -- the report
    already contains missing-value and dtype information, so this just
    writes both outputs and folds a couple of run-level facts (row counts)
    into the same summary rather than recomputing anything.
    """
    frame = pd.read_csv(input_path)
    processed, report = preprocess(frame, target_column=target_column)

    output_dir.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_dir / "processed.csv", index=False)

    summary: dict[str, object] = {
        "input_rows": len(frame),
        "output_rows": len(processed),
        **report,
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
