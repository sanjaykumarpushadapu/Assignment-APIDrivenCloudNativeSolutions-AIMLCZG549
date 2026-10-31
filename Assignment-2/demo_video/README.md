# Demo video: automated recording

These scripts record the Group 49 Assignment II demonstration video: Playwright
records each scene in Chromium, and
ffmpeg joins the clips with narration and captions. The video covers the workplace
problem and labels, fine-tuning and summaries, the RAG pipeline, the tests, the live
React app (analysis, source-backed chat and a clinical referral), Swagger "Try it out →
Execute" on the API, and the workplace results. Every video has captions (CC).

Run everything from the `Assignment-2` folder. The scripts work on Windows, macOS and Linux.

## Quick reference

| Command | What it does |
|---|---|
| `pip install -r demo_video/requirements.txt` | One-time install: Playwright, code highlighting, caption drawing and microphone recording. |
| `python demo_video/record_demo.py --tts none --burn-subtitles` | Records the full video with no voice and captions drawn on screen. |
| `python demo_video/record_voice.py` | Shows each scene's script and records your voice, one scene at a time, into `demo_video/voice/`. |
| `python demo_video/record_demo.py --tts files --burn-subtitles` | Records the full video using your voice recordings. Record every scene first. |
| `python demo_video/record_demo.py --list` | Lists the scenes and who narrates each part. |
| `python demo_video/record_demo.py --clean-all` | Last step only, after upload: deletes generated videos and voice recordings (asks first). |

## Before recording

The full video shows real results only. Recording stops unless all of these are true:

1. The API is running on `http://127.0.0.1:8001` and the React app on `http://127.0.0.1:5173` (see the project README).
2. `/metadata` reports the classifier, summariser and knowledge index as ready, with versions.
3. `evaluation/results.json` exists with the measured values used by the narration:

   | Key | Meaning |
   |---|---|
   | `classifier_model`, `test_messages` | Base model name and number of held-out test messages |
   | `macro_f1_base`, `macro_f1_tuned` | Macro-F1 before and after fine-tuning, on the same test set |
   | `summary_ok`, `summary_total` | Held-out summaries that kept every essential request |
   | `retrieval_hits`, `retrieval_total` | Questions with relevant evidence in the top three |
   | `answers_supported`, `answers_total` | Answers supported by their cited sources |
   | `workflow_tasks`, `time_manual_min`, `time_assisted_min` | Workplace timing study |
   | `refusals_ok`, `refusals_total` | Unsupported/clinical questions correctly declined or referred |

4. The report figures exist in `docs/report/imgs/`: `architecture.png`, `training_loss.png`,
   `confusion_matrix.png`, `summary_examples.png`, `rag_pipeline.png`, `workplace_results.png`.

Missing evidence stops the build instead of producing a video with invented numbers. To try the
recorder before the models are ready, record only scenes that need no results, for example:

```bash
python demo_video/record_demo.py --tts none --allow-not-ready --only title label_guide tests_terminal swagger_intro
```

## One-time setup

Install ffmpeg (`winget install Gyan.FFmpeg` on Windows, `brew install ffmpeg` on macOS,
`sudo apt install ffmpeg libportaudio2` on Linux), then, with the project virtual environment active:

```bash
pip install -e ".[dev]"
pip install -r demo_video/requirements.txt
```

The recorder uses installed Google Chrome by default. Use `--channel msedge`, or run
`python -m playwright install chromium` and use `--channel chromium`.

## Your own voice (optional)

```bash
python demo_video/record_voice.py
python demo_video/record_demo.py --tts files --burn-subtitles
```

Press Enter to start and stop each take, then keep it, play it back (`p`) or redo it (`r`).
Edit the spoken text in `SELF_SCRIPTS` in `scenes.py`. Redo specific scenes with
`python demo_video/record_voice.py --scene app_chat --rerecord`.

## Other options

| Option | Effect |
|---|---|
| `--tts say` / `--tts edge --voice en-IN-NeerjaNeural` | Synthesized narrator (macOS voice, or Microsoft neural voice via `pip install edge-tts`). |
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
