# Demo video: automated recording

These scripts record the complete Group 49 demonstration video, about 5 to 6
minutes long, following the recording script in the project README. The video covers
the dataset, ingestion and tests, the quality and preprocessing code, the
two-minute Composer schedule, the execution log, the EDA and model charts, the
live deployment links, the live dashboard, and a live Swagger "Try it out →
Execute" on all four required endpoints. Live pages are shown with a browser
address bar, so the real Cloud Run URLs are visible. Every video has captions (CC).

The scripts work on **Windows, macOS and Linux**. Run them from the
`Assignment-1` folder.

## Quick reference

Run these in order from the `Assignment-1` folder:

| Command | What it does |
|---|---|
| `pip install -r demo_video/requirements.txt` | One-time install of what the recorder needs: browser automation (Playwright), code highlighting, caption drawing, and microphone recording. |
| `python demo_video/record_demo.py --tts none --burn-subtitles` | Records a **fresh** full video with no voice and captions drawn on screen. |
| `python demo_video/record_voice.py` | Shows each scene's script and **records your voice** with the microphone, one scene at a time. Files are saved in `demo_video/voice/`. |
| `python demo_video/record_demo.py --tts files --burn-subtitles` | Records a fresh full video using **your recorded voice** as the narration. |
| `python demo_video/record_demo.py --clean` | Optional. Clean-up already happens automatically after every build; use this only after a run you stopped halfway. |
| `python demo_video/record_demo.py --clean-all` | **Last step only**, after the videos are uploaded and submitted: deletes everything generated, including the videos and voice recordings. It asks you to type `yes` first. The scripts are kept. |

The options mean:

- `--tts none`: no narration voice; captions only.
- `--tts files`: use your recordings from `demo_video/voice/`.
- `--burn-subtitles`: draw the captions on the picture, so they show everywhere, including Google Drive.
- Every recording runs fresh ingestion, tests, and the pipeline.

The sections below give the full setup and details.

## 1. One-time setup

Install ffmpeg:

| OS | Command |
|---|---|
| macOS | `brew install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg`, then open a new terminal |
| Linux | `sudo apt install ffmpeg libportaudio2` |

Then set up Python (3.11+). Activate the project's virtual environment first:
`source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\activate` on
Windows.

```bash
pip install -e ".[dev,gcp]"
pip install -r demo_video/requirements.txt
python -m playwright install chromium
```

## 2. Video with captions, no voice

```bash
python demo_video/record_demo.py --tts none --burn-subtitles
```

This produces `demo_video/output/Group49_AIMLCZG549_Assignment1_Demo_NoVoice.mp4`.

The first run also runs ingestion, the tests and the pipeline, so the terminal
scenes show real output (about 15 minutes in total). On later runs, add
Each run refreshes that output.

## 3. Video with your own voice (optional)

**a. Record the narration.** One person reads every scene, in order:

```bash
python demo_video/record_voice.py
```

For each scene the script appears on screen. Press Enter to start, read it,
and press Enter to stop. Then press Enter to keep the take, `p` to play it
back, or `r` to redo it. You can stop at any time with Ctrl+C and run the same
command later; scenes already recorded are skipped. Recordings are saved in
`demo_video/voice/`.

The script is written as a student explaining the project ("we built…", "Part
two, by Sathish, covers…"). You can edit it in `SELF_SCRIPTS` in `scenes.py`.

To redo particular scenes:
`python demo_video/record_voice.py --scene dashboard api_dataset --rerecord`.
To see which scenes are recorded: `python demo_video/record_voice.py --list`.

To use a different microphone: `python demo_video/record_voice.py --devices`,
then add `--device <number>`. The first time you record, macOS asks for
permission to let the terminal use the microphone; allow it.

**b. Build the video with the recorded voice:**

```bash
python demo_video/record_demo.py --tts files --burn-subtitles
```

This produces `demo_video/output/Group49_AIMLCZG549_Assignment1_Demo_TeamVoice.mp4`.
The no-voice video from step 2 stays as a separate file.

## 4. Cloud Composer: with or without Google login (optional)

Cloud Composer can appear in the video in two ways.

**Without login (default).** The Cloud Composer part shows the run-history screenshots from the report. Live Composer data still appears through the live dashboard and the Swagger `/api/v1/workflow` and `/api/v1/schedule` calls. Nothing extra is needed:

```bash
python demo_video/record_demo.py --tts none --burn-subtitles    # no voice
python demo_video/record_demo.py --tts files --burn-subtitles   # your voice
```

**With login (live Cloud Composer console).** The video opens the real Google Cloud console page, with its `console.cloud.google.com` address visible.

1. Sign in once:

   ```bash
   python demo_video/record_demo.py --login-composer
   ```

   A browser window opens. Sign in to your Google account there yourself. When the Cloud Composer page shows `diabetes-risk-env`, press Enter in the terminal. The sign-in is saved in `demo_video/output/chrome-profile/`, which is git-ignored; don't share it.

2. Record with `--composer-live` added:

   ```bash
   python demo_video/record_demo.py --tts none --burn-subtitles --composer-live    # no voice
   python demo_video/record_demo.py --tts files --burn-subtitles --composer-live   # your voice
   ```

If Google blocks the sign-in ("This browser may not be secure"), use the default commands without login; the screenshots are used instead. `--clean-all` also deletes the saved sign-in.

## Other options

| Option | Effect |
|---|---|
| `--tts say` / `--tts edge --voice en-IN-NeerjaNeural` | Synthesized narrator instead: the macOS voice, or a Microsoft neural voice (`pip install edge-tts`). The output file ends in `_AIVoice.mp4`. |
| `--burn-subtitles` | Draw the captions on the picture. Use it for Google Drive, whose player ignores embedded caption tracks. Every video also has a switchable CC track, plus a `.srt` file. |
| `--finish --tts <mode> --burn-subtitles` | Rebuild only the captions of a video already recorded, without recording again. |
| `--only <scene ids>`, `--list` | Record only some scenes (for a quick test), or list them. |
| `--keep-work` | Keep the temporary clips and audio. Normally they are deleted after a successful build, and only the final `.mp4`, `.srt` and `_report.json` are kept. |
| `--headed` | Show the browser while recording. |
| `--allow-non-200` | Record even if a live endpoint doesn't return 200. By default recording stops, because the narration says each endpoint returned 200. |
| `--login-composer`, `--composer-live` | Show the live Cloud Composer console instead of screenshots. See section 4. |

## Clean up

Clean-up is automatic. At the end of every successful build, the script deletes all temporary clips, audio, leftovers from earlier or stopped runs, and cache files, so you don't need to run anything extra. If a run is stopped halfway, you can tidy up without building:

```bash
python demo_video/record_demo.py --clean
```

This keeps the finished videos (`.mp4`, `.srt`, `_report.json`), the saved command output, and your voice recordings.

To start completely fresh, use `--clean-all`. It asks you to type `yes` first, then also deletes every generated video and your voice recordings in `demo_video/voice/`. The scripts themselves are never deleted.

## Before uploading

1. Watch the video once. The `*_report.json` file next to it should show `"200"` for every entry in `swagger_status`.
2. Each fresh run appends one entry to `data/raw/ingestion_manifest.json`, which is what `ingest` does by design.
3. Upload the MP4 to the shared Google Drive folder, set sharing to "Anyone with the link: Viewer", and test the link in a private window.
