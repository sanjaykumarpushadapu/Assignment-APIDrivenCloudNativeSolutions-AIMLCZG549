# Diabetes Care Support Assistant

A staff-facing prototype for routing diabetes support requests, preparing handoff summaries, and answering general questions from an approved document collection. It is not a clinical decision system, and staff must review outputs.

The evolving assessment report is [docs/report/report.md](docs/report/report.md).
Update it with verified results and screenshots as each step is completed; export
the reviewed report to PDF at the end, following Assignment I's workflow.

## Install development tools

Use Python 3.10 or newer. Choose one package manager for this checkout; `uv` and Poetry use separate lockfiles, so avoid switching between them during the same work.

```powershell
uv sync --extra dev
```

Poetry 2.x can use the same PEP 621 project metadata:

```powershell
poetry install -E dev
```

## Part I: classifier in the application skeleton

The `Seq2SeqClassifier` adapter implements the existing `Classifier` interface
and is wired into `main.py`. The same configurable sequence-to-sequence model
serves classification and summarisation. By default it uses the original
`google/flan-t5-base` weights without training on the pilot dataset. The loading approach follows the [official model card](https://huggingface.co/google/flan-t5-base).

From `Assignment-2`, using uv and an isolated Python 3.11 environment:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[inference,dev]"
.venv/bin/python -m diabetes_support.infrastructure.seq2seq_classifier
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.
If you already use Poetry, keep that environment and install the `inference`
extra there instead of creating a second environment.

The first run downloads the tokenizer and model to the git-ignored
`artifacts/huggingface/` folder by default. Inference runs locally on CPU by default; it makes no paid
inference API call. The model download requires internet access.

The adapter has three main prediction steps: **tokenize** (convert text to numerical tokens),
**generate** (run the original model without changing its weights), and **decode**
(convert its output tokens back to text). The terminal command prints the actual
output, category validity and model revision. An unrecognised output produces a
null category and a nonzero exit status; it is never replaced with an expected label.

The default message is “Please move my appointment to Friday.” The expected label
is `appointment_support`. Compare that expectation with the actual output:
`valid_category` only confirms the output is one of our labels, not its accuracy.
A single successful example is a feasibility check, not an evaluation score.

Verified locally on 31 October 2026: the default message returned
`appointment_support` on CPU using Python 3.11.5, PyTorch 2.15.0 and Transformers
5.22.1. The adapter pins model/tokenizer revision
`7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`. These are observed runtime versions;
the optional dependency ranges do not lock every future installation to them.

## Configure the classifier

Create your local settings file once, from `Assignment-2`:

```bash
cp .env.example .env
```

Edit `.env` to choose the shared model and runtime. One compatible model is used for both classification and summarisation. The API and terminal command use the
same settings; restart the process after editing. Environment variables override
the file. The `.env` file and downloaded model artifacts are excluded from Git.

| Setting | Default | Purpose |
|---|---|---|
| `MODEL_NAME` | `google/flan-t5-base` | Hub ID or complete local seq2seq checkpoint folder |
| `MODEL_REVISION` | blank | Automatically pins our baseline; specify a SHA for another Hub model |
| `MODEL_DEVICE` | `cpu` | `cpu`, `cuda`, `mps`, or `auto` |
| `MODEL_CACHE_DIR` | `artifacts/huggingface` | Download/cache folder relative to Assignment-2 |
| `MODEL_MAX_INPUT_TOKENS` | `512` | Full prompt limit, including task instructions |
| `CLASSIFICATION_MAX_NEW_TOKENS` | `32` | Category generation limit |
| `SUMMARY_MAX_NEW_TOKENS` | `128` | Summary generation limit |
| `MODEL_LOCAL_FILES_ONLY` | `false` | Set `true` to require cached/local files without downloading |

For example, changing `MODEL_NAME=google/flan-t5-small` and leaving the
revision blank selects that model without inheriting the default checkpoint's revision.
This model switch is supported by configuration; its output quality still needs
evaluation. The shared runtime supports compatible Hugging Face encoder-decoder models
that work with `AutoModelForSeq2SeqLM`, safetensors weights and the matching
tokenizer.
It does not support every model family: decoder-only chat models, hosted API
providers and adapter-only LoRA checkpoints need a different loading implementation.

For a future fine-tuned model, use `MODEL_NAME=./artifacts/models/clinic-support`
after saving a complete compatible model and tokenizer there. Relative paths
resolve from Assignment-2. Selecting a checkpoint does not verify its training
history; output reports `weights_updated_during_inference: false` because this
operation only predicts. The previous hard-coded `fine_tuned_by_us` field has
been removed to avoid mislabelling a selected checkpoint.

`auto` selects CUDA when available, then Apple MPS, then CPU. An explicitly
requested unavailable device fails with an explanation. Choose the device before
loading: both input tensors and model weights are placed on that device.

Configuration parsing and validation live in
`backend/src/diabetes_support/infrastructure/model_settings.py`; inference
logic stays in the existing classifier adapter. The constructor also accepts a
`ModelSettings` object for tests or programmatic configuration.

To try a different synthetic message:

```bash
.venv/bin/python -m diabetes_support.infrastructure.seq2seq_classifier --message "The clinic portal will not let me sign in."
```

The adapter loads lazily on its first prediction and reuses that model object
for later predictions in the same process. Each separate terminal invocation
starts a new process and loads its own copy. A new application process initially
reports both model tasks as not ready until the shared model is loaded.

To exercise the integrated route after starting the API, use the same request you tested:

```bash
curl -X POST http://127.0.0.1:8001/analyze \
  -H 'Content-Type: application/json' \
  -d '{"message":"Please move my appointment to Friday. I also cannot download the education leaflet from the portal."}'
```

`/analyze` now returns both a generated handoff summary and the main-request
category. The classifier and summarizer share one lazily loaded FLAN-T5 model
and tokenizer. A source-coverage check now appends any original sentence whose meaningful words
are missing from the generated summary. This prevents the tested second request
from disappearing, though it can produce repetition when the model paraphrases.
Review summaries for accuracy and unsupported additions. The standalone `scripts/check_classifier.py`
experiment has been removed; the module command above exercises the actual
application classifier adapter.

## Start locally

Start the API from `Assignment-2` with the inference extra installed. With the
virtual environment above, run:

```bash
.venv/bin/python -m uvicorn diabetes_support.main:app --reload --port 8001
```

Or use your selected package manager (include the inference extra in that environment):

```powershell
uv run --extra inference uvicorn diabetes_support.main:app --app-dir backend/src --reload --port 8001
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
- `backend/src/diabetes_support/infrastructure`: shared sequence-to-sequence classifier/summarizer adapters and a placeholder for document-grounded answers.
- `backend/src/diabetes_support/presentation`: FastAPI routes and HTTP schemas.
- `backend/src/diabetes_support/main.py`: composition root that wires the layers.
- `backend/tests`: backend API tests. `frontend` contains the React + TypeScript client, and `tests/e2e` checks the browser workflow.

## Current status

The API and React UI are wired. The sequence-to-sequence classifier and message summarizer share one lazy model runtime. Document-grounded answer generation remains unconfigured, so chat returns HTTP 503 for the missing knowledge component. Summaries and categories are model outputs and require staff review. The 35-message pilot in `data/pilot/` and the 280-message training draft in `data/training/classification_train.jsonl` (56 per category) have `review_status: approved`, `reviewer: Sanjay`, and `reviewed_on: 2026-10-31` at the user’s direction. Their AI-drafted provenance and historical AI-assisted review notes are retained; approval metadata does not make these datasets clinical guidance or a held-out benchmark. The 10 routing checks remain development-only. Separate validation/test candidate files now contain 60 synthetic examples each (12 per category); their review metadata is approved at the user’s direction. A one-epoch fine-tuned checkpoint is saved locally under `artifacts/models/clinic-support` and has been reload-verified; the knowledge documents remain to be prepared. See [the pilot label guide](data/pilot/label_guide.md) for data status and use. Downloaded model weights stay in the ignored artifacts directory.
