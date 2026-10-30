# Diabetes Care Support Assistant

A staff-facing prototype for routing diabetes support requests, preparing handoff summaries, and answering general questions from an approved document collection. It is not a clinical decision system, and staff must review outputs.

## Install development tools

Use Python 3.10 or newer. Choose one package manager for this checkout; `uv` and Poetry use separate lockfiles, so avoid switching between them during the same work.

```powershell
uv sync --extra dev
```

Poetry 2.x can use the same PEP 621 project metadata:

```powershell
poetry install -E dev
```

## Start locally

Start the API from the project root using the package manager you chose:

```powershell
uv run uvicorn diabetes_support.main:app --app-dir backend/src --reload --port 8001
```

Or with Poetry:

```powershell
poetry run uvicorn diabetes_support.main:app --app-dir backend/src --reload --port 8001
```

In a second terminal, install and start the React frontend:

```powershell
Set-Location frontend
npm ci
npm run dev
```

The frontend is available at `http://127.0.0.1:5173`. Vite proxies `/api` requests to the FastAPI service on port `8001`. API documentation is available at `http://127.0.0.1:8001/docs`.

## Tests and checks

Build the frontend with `npm run build` from `frontend/`. Install Playwright's Chromium browser once with `uv run playwright install chromium` or `poetry run playwright install chromium` if Google Chrome is not installed. The browser smoke test uses installed Google Chrome by default. To choose another channel in PowerShell, set `$env:PLAYWRIGHT_CHANNEL = 'msedge'` or `$env:PLAYWRIGHT_CHANNEL = 'chromium'`.

Run API tests with `uv run pytest` or `poetry run pytest`. The browser smoke test is opt-in and expects the React app to be running at `http://127.0.0.1:5173`; run it from the project root with `uv run pytest -m e2e` or `poetry run pytest -m e2e`.

Run static checks with `uv run ruff check .` and `uv run black --check .`, or prefix those commands with `poetry run` when using Poetry.

## Backend layout

- `backend/src/diabetes_support/domain`: application-independent errors and status types.
- `backend/src/diabetes_support/application`: use cases and ports for model/retrieval capabilities.
- `backend/src/diabetes_support/infrastructure`: replaceable adapters; currently reports unconfigured components.
- `backend/src/diabetes_support/presentation`: FastAPI routes and HTTP schemas.
- `backend/src/diabetes_support/main.py`: composition root that wires the layers.
- `backend/tests`: backend API tests. `frontend` contains the React + TypeScript client, and `tests/e2e` checks the browser workflow.

## Current status

The API and React UI are wired, but classifier, summarizer, and document-grounded answer generation are intentionally unconfigured. Analysis and chat requests return HTTP 503 until those components and artifacts are implemented. A synthetic classification/routing pilot is included under `data/pilot/`: 35 labelled messages in `classification_pilot.jsonl`, AI-reviewed and approved by Codex on 30 October 2026 for training/reload feasibility, plus 10 development-only routing checks in the existing label guide. This is pilot-content approval, not team-member review or measured model performance. See [the pilot label guide](data/pilot/label_guide.md) for the review record and permitted use. The full training/evaluation datasets, model weights and knowledge documents are not yet included.
