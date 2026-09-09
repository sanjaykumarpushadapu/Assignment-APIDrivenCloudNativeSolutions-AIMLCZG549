"""Structured, platform-neutral execution logging."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_run_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%S%fZ")


def write_execution_log(summary: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"run_{summary['run_id']}.json"
    path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return path


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
