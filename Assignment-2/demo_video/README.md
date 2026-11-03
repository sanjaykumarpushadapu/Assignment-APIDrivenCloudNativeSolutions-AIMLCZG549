# Demo video: automated recording

These scripts record the Group 49 Assignment II demonstration video: Playwright
records each scene in Chromium, and ffmpeg joins the clips with narration and captions.
Use Microsoft Edge TTS (`edge-tts`) with `en-IN-PrabhatNeural` for the same narrated
voice on macOS, Windows, and Linux.
The video covers the workplace
problem and labels, fine-tuning and summaries, the RAG pipeline, the tests, the live
React app (analysis, source-backed chat, clinical referral, and the limited urgent-care
response), Swagger "Try it out → Execute" on the API, and the workplace results. Every
video has captions (CC).

Run everything from the `Assignment-2` folder. The scripts work on Windows, macOS and Linux.

## Quick reference

| Command | What it does |
|---|---|
| `python demo_video/record_demo.py --tts edge --voice en-IN-PrabhatNeural --burn-subtitles` | Records and assembles the full video with the same narrated voice across operating systems; no per-scene prompts. |
| `pip install -r demo_video/requirements.txt` | One-time install of video, caption, and voice dependencies in the active project environment. |
| `python demo_video/record_demo.py --tts none --burn-subtitles` | Records the full video with no voice and captions drawn on screen. |
| `python demo_video/record_demo.py --list` | Lists the scenes and who narrates each part. |
| `.venv/bin/python scripts/capture_report_evidence.py` | Refreshes the report's Swagger and React screenshots after the API and app are running. |
| `python demo_video/record_demo.py --clean-all` | Last step only, after upload: deletes generated videos and voice recordings (asks first). |

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
python demo_video/record_demo.py --tts none --allow-not-ready --only title label_guide tests_terminal swagger_intro
```

## One-time setup

Install ffmpeg (`winget install Gyan.FFmpeg` on Windows, `brew install ffmpeg` on macOS,
`sudo apt install ffmpeg` on Linux), then activate the project virtual environment
(`source .venv/bin/activate` on macOS/Linux or `.venv\\Scripts\\activate` on Windows):

```bash
uv sync --extra inference --extra dev
pip install -r demo_video/requirements.txt
```

The `inference` extra installs PyTorch, Transformers, and SentencePiece needed by
the API. The recorder starts the API automatically, but it does not install
application dependencies.

The recorder uses installed Google Chrome by default. Use `--channel msedge`, or run
`python -m playwright install chromium` and use `--channel chromium`.

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
