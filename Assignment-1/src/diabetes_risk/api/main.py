from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(
    title="Diabetes Risk Screening API",
    version="0.1.0",
    description="Non-diagnostic risk-screening pipeline endpoints.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/runs/latest", tags=["pipeline"])
def latest_run() -> dict[str, str | None]:
    return {
        "status": "not_started",
        "completed_at": None,
        "message": "Connect this endpoint to the selected cloud run history.",
    }


@app.get("/api/v1/metadata", tags=["pipeline"])
def metadata() -> dict[str, str]:
    return {
        "project": "Diabetes Risk Prediction Using Health and Lifestyle Indicators",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "For risk screening only; not a medical diagnosis.",
    }