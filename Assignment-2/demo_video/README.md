# Demo video: automated recording

These scripts record the Group 49 Assignment II demonstration video: Playwright
records each scene in Chromium, and ffmpeg joins the clips with narration and captions.
Use Microsoft Edge TTS (`edge-tts`) with `en-IN-PrabhatNeural` for the same narrated
voice on macOS, Windows, and Linux.
The video covers the NLP workflow and labels, fine-tuning and summary evaluation, the
RAG pipeline, team responsibilities, the live React app (analysis, source-backed chat,
clinical referral, and the urgent-care response), Swagger API examples, and workplace
application. Every video has captions (CC).

Run these commands from the `Assignment-2` folder. Use the interpreter path for your operating system so the project virtual environment is used.

## Quick reference

| Task | macOS/Linux | Windows PowerShell |
|---|---|---|
| Record with Prabhat voice and captions | `.venv/bin/python demo_video/record_demo.py --tts edge --voice en-IN-PrabhatNeural --burn-subtitles` | `.\.venv\Scripts\python.exe demo_video/record_demo.py --tts edge --voice en-IN-PrabhatNeural --burn-subtitles` |
| Install video and voice dependencies | `uv pip install --python .venv/bin/python -r demo_video/requirements.txt` | `uv pip install --python .venv\Scripts\python.exe -r demo_video/requirements.txt` |
| Record without voice | `.venv/bin/python demo_video/record_demo.py --tts none --burn-subtitles` | `.\.venv\Scripts\python.exe demo_video/record_demo.py --tts none --burn-subtitles` |
| List scenes | `.venv/bin/python demo_video/record_demo.py --list` | `.\.venv\Scripts\python.exe demo_video/record_demo.py --list` |
| Refresh report screenshots | `.venv/bin/python scripts/capture_report_evidence.py` | `.\.venv\Scripts\python.exe scripts/capture_report_evidence.py` |
| Remove generated videos and voice recordings | `.venv/bin/python demo_video/record_demo.py --clean-all` | `.\.venv\Scripts\python.exe demo_video/record_demo.py --clean-all` |

## Before recording

The recorder starts the API and React frontend on their default local addresses when they are not already available. It also sends sample requests to load lazy model components before checking readiness. Its full video uses real results and recording proceeds only when:

1. The local model checkpoints and data required by `.env` are available; `/metadata` reports the classifier, summariser and knowledge index as ready.
2. The tracked report evaluation records exist. The video reads them directly, rather than a separate stale results file:

   | Record | Values used |
   |---|---|
   | `classifier-run-record.json` | Base and fine-tuned classifier macro-F1 and held-out test size |
   | `summarizer-evaluation-record.json` | Reviewed essential-fact retention count |
   | `rag-evaluation-record.json` | Retrieval, answer-support, and referral results from the explicitly labelled pre-fix baseline |

3. The report screenshots exist in `docs/report/evidence/`. The video reuses the classifier-results,
   request-analysis, source-grounded-answer, and staff-referral images. Its architecture scene renders the
   Mermaid source from `report.md`, so the report and video show the same flowchart.

The report and its screenshot names are kept in sync by using stable embedded filenames. Refresh the screenshots
after a final successful API/UI run; the script checks that all requests succeeded before replacing any image.
If an implementation result or evaluation changes, update the report text and tracked record together. The RAG
evaluation currently available is a pre-fix baseline, and the report/video do not claim a post-fix score or a
measured workplace time saving.

Missing evidence stops the build instead of producing a video with invented numbers. To try the
recorder before the models are ready, record only scenes that need no results, for example:

```bash
.venv/bin/python demo_video/record_demo.py --tts none --allow-not-ready --only title label_guide swagger_intro
```

On Windows PowerShell, use `.\.venv\Scripts\python.exe` in place of `.venv/bin/python` in that example.

## One-time setup

Install ffmpeg (`winget install Gyan.FFmpeg` on Windows, `brew install ffmpeg` on macOS,
`sudo apt install ffmpeg` on Linux), then create and sync the project virtual environment:

```bash
uv sync --extra inference --extra dev
```

Then install `demo_video/requirements.txt` using the operating-system command in the table above.

The `inference` extra installs PyTorch, Transformers, and SentencePiece needed by
the API. The recorder starts the API automatically, but it does not install
application dependencies.

The recorder uses installed Google Chrome by default. Use `--channel msedge`, or install Playwright's Chromium using the project's virtual-environment Python and use `--channel chromium`.

Services started by the recorder are stopped when the recording command exits. Any API or frontend that was already running is left untouched.

## Other options

| Option | Effect |
|---|---|
| `--tts say` / `--tts edge --voice en-IN-PrabhatNeural` | Select macOS system speech or the shared Edge neural voice. |
| `--burn-subtitles` | Draw captions on the picture; Google Drive's player ignores embedded caption tracks. |
| `--only <scene ids>` | Record only some scenes. |
| `--skip-commands` | Reuse the previous run's terminal output. |
| `--finish` | Rebuild captions for a video recorded with `--keep-work`. |
| `--headed` | Show the browser while recording. |
| `--allow-non-200`, `--allow-not-ready` | Test runs only; do not use for the submitted video. |

## Before uploading

1. Watch the video once. In `*_report.json`, every `swagger_status` entry should be `"200"`.
2. Upload the MP4 to the shared Google Drive folder, set sharing to "Anyone with the link: Viewer",
   and test the link in a private window.
