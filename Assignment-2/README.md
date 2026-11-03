# Diabetes Care Support Assistant

A staff-facing application for classifying diabetes-support messages, preparing handoff summaries, and answering general diabetes questions from a curated WHO source. Staff review generated summaries and answers.

The assessment report is in [docs/report/report.md](docs/report/report.md).

## Run the application

### Requirements

- macOS with Python 3.10 or newer
- Node.js 20.19 or newer
- `uv` and `npm`

From the `Assignment-2` directory, install the Python dependencies and create local settings:

```bash
uv sync --extra inference --extra dev
cp .env.example .env
```

Start the API:

```bash
.venv/bin/python -m uvicorn diabetes_support.main:app --app-dir backend/src --reload --port 8001
```

In a second terminal, start the web interface:

```bash
cd frontend
npm ci
npm run dev
```

Open the application at <http://127.0.0.1:5173>. The API documentation is at <http://127.0.0.1:8001/docs>.

The first model load may download weights from Hugging Face. Set `MODEL_LOCAL_FILES_ONLY=true` in `.env` to use only cached or local model files.

The classifier checkpoint is stored locally and is not included in Git. Before testing `POST /analyze`, obtain the team checkpoint or create one using the Classifier instructions below. Without it, the classifier component will not be ready.

## Application workflow

| API route | Purpose |
|---|---|
| `GET /health` | Check whether the API is running |
| `GET /metadata` | Inspect model and knowledge-index readiness |
| `POST /analyze` | Classify a support message and return a handoff summary |
| `POST /retrieve` | Return ranked passages from the local knowledge index |
| `POST /chat` | Answer a general question from retrieved passages or return a staff referral |

The React and TypeScript frontend calls the FastAPI service. Classification uses the fine-tuned `clinic-support` checkpoint. Summarisation and answer generation use the configured FLAN-T5 model. Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` and the local WHO passage index.

## Configure models and retrieval

Edit `.env` to choose model IDs or local checkpoint directories, model revisions, and devices. `.env` is local and excluded from Git. Environment variables override values in the file; restart the API after changing settings.

| Setting | Purpose |
|---|---|
| `CLASSIFIER_MODEL_NAME` | Classifier model ID or local checkpoint; defaults to `./artifacts/models/clinic-support` |
| `SUMMARIZER_MODEL_NAME` | Model used for summary inference; defaults to `google/flan-t5-base` |
| `SUMMARIZER_BASE_MODEL_NAME` | Starting checkpoint used when fine-tuning the summariser |
| `MODEL_DEVICE` | Inference device: `cpu`, `mps`, `cuda`, or `auto` |
| `MODEL_REVISION` | Optional pinned Hugging Face model revision |
| `MODEL_LOCAL_FILES_ONLY` | Require local or cached model files when set to `true` |
| `RETRIEVAL_MODEL_NAME` | Embedding model used to rank passages |
| `KNOWLEDGE_CHUNKS_PATH` | Path to the local retrieval corpus |

See `.env.example` for the full list, including token limits, retrieval thresholds, and task-specific overrides. Checkpoint paths are resolved from the `Assignment-2` directory.

## Model training and evaluation

Training data, validation data, and held-out evaluation data are stored separately under `data/`. Evaluation scripts use the test partitions for measurement; do not use them to select prompts, thresholds, or checkpoints.

### Classifier

The fine-tuned classifier checkpoint is stored under `artifacts/models/clinic-support/`. Model weights and downloaded caches are excluded from Git. To create a separate candidate checkpoint from the tracked training data:

```bash
.venv/bin/python scripts/train_classifier.py --epochs 1 --output-dir artifacts/models/clinic-support-candidate
```

The evaluation script uses the classifier selected by `CLASSIFIER_MODEL_NAME`. Run it without `--final-test` for validation results. After model and prompt choices are frozen, run the held-out test once:

```bash
.venv/bin/python scripts/evaluate_classifier.py --final-test
```

To use or share a checkpoint, set `CLASSIFIER_MODEL_NAME` to its directory in `.env`, or transfer the complete model directory through team-approved storage. Each team member keeps their own `.env` and model files locally.

### Summariser

The application currently uses the model set by `SUMMARIZER_MODEL_NAME`. To fine-tune a candidate checkpoint and save it to a separate directory:

```bash
.venv/bin/python scripts/train_summarizer.py --output-dir artifacts/models/clinic-summary-candidate
```

To run the one-example smoke check without saving a checkpoint:

```bash
.venv/bin/python scripts/train_summarizer.py --smoke
```

Evaluate summary outputs with:

```bash
.venv/bin/python scripts/evaluate_summarizer.py --model google/flan-t5-base
```

The held-out summary cases are in `data/test/summarization_evaluation_candidate.jsonl`; they are for evaluation, not model tuning. To use a reviewed summariser checkpoint in the application, set `SUMMARIZER_MODEL_NAME` to its directory in `.env` and restart the API.

### Knowledge source

The retrieval corpus is built from reviewed local notes in `data/knowledge/`. The source URL, source details, and content checks are recorded in `data/knowledge/manifest.json`. To rebuild the chunks after editing the notes:

```bash
.venv/bin/python scripts/prepare_knowledge.py
```

If the reviewed WHO snapshot is not present locally, use `--download` to retrieve and verify it:

```bash
.venv/bin/python scripts/prepare_knowledge.py --download
```

The script checks the source content before writing `data/knowledge/chunks.jsonl`. Review changes to the source and notes before rebuilding the corpus.

## Checks

Run backend tests:

```bash
.venv/bin/python -m pytest
```

Build the frontend:

```bash
cd frontend
npm run build
```

The browser workflow test is optional. Install its browser once with `uv run playwright install chromium`, then start the API and frontend before running:

```bash
.venv/bin/python -m pytest -m e2e
```

## Record the demonstration video

Install the video dependencies in the project environment with `pip install -r demo_video/requirements.txt`. Activate `.venv` with `source .venv/bin/activate` on macOS/Linux or `.venv\\Scripts\\activate` on Windows. Use the same Edge neural voice on either platform:

```bash
python demo_video/record_demo.py --tts edge --voice en-IN-PrabhatNeural --burn-subtitles
```

The command starts the API and frontend if they are not already running, loads the configured model components, and records without per-scene prompts. It requires `ffmpeg` and Google Chrome. On macOS, install `ffmpeg` with `brew install ffmpeg`; on Windows, install it with `winget install Gyan.FFmpeg`. Services started by the recorder are stopped after it finishes. The MP4, captions, and recording report are saved under `demo_video/output/`.

## Project structure

```text
backend/src/diabetes_support/   FastAPI application and model adapters
backend/tests/                 API, model-configuration, and summariser tests
frontend/                      React and TypeScript user interface
data/training/                 Training datasets
data/validation/               Validation datasets
data/test/                     Held-out evaluation datasets
data/knowledge/                Reviewed source notes and retrieval chunks
scripts/                       Training, evaluation, and corpus preparation
docs/report/                   Assessment report and supporting evidence
artifacts/                     Local model weights and evaluation outputs; ignored by Git
```
