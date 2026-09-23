"""GCP configuration for the API layer's Cloud Composer / Cloud Monitoring clients.

This module only reads configuration -- it makes no GCP SDK or HTTP calls
itself. Real values come from environment variables (see `.env.example`);
no project identifiers or credentials are hard-coded here, consistent with
`README.md`'s "no credentials or GCP project identifiers are
committed to this repository" policy.

Used by `gcp_service.py`. Local-file-backed endpoints (`local_service.py`)
do not need this module at all.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GCPConfig:
    """Connection details for one Cloud Composer environment."""

    project_id: str
    location: str
    composer_environment: str
    credentials_path: str | None

    def is_configured(self) -> bool:
        """True once the required identifiers are present.

        Service functions call this before making GCP API requests so
        missing identifiers produce a clear configuration error.
        """
        return bool(self.project_id and self.location and self.composer_environment)


def load_gcp_config() -> GCPConfig:
    """Read GCP connection settings from the environment.

    Environment variables (see `.env.example`):
        GCP_PROJECT_ID            e.g. the team's GCP project id
        GCP_LOCATION              e.g. "us-central1"
        GCP_COMPOSER_ENVIRONMENT  e.g. "diabetes-risk-env"
        Authentication uses Application Default Credentials from
        `gcloud auth application-default login`.
    """
    return GCPConfig(
        project_id=os.environ.get("GCP_PROJECT_ID", ""),
        location=os.environ.get("GCP_LOCATION", ""),
        composer_environment=os.environ.get("GCP_COMPOSER_ENVIRONMENT", ""),
        credentials_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    )
