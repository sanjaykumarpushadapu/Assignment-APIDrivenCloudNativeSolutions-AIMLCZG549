#!/usr/bin/env python3
"""Record your own narration for the demo video, one scene at a time.

Works on Windows, macOS and Linux. One person reads every scene, in order:

    python demo_video/record_voice.py

It shows each scene's script; press Enter to start, read it, press Enter to
stop, then keep it, play it back, or redo it. You can stop at any time
(Ctrl+C) and run the same command later: scenes already recorded are skipped.

Recordings are saved as demo_video/voice/<scene_id>.wav. Then build the video:

    python demo_video/record_demo.py --tts files --burn-subtitles

Other options: --scene <id> ... (redo specific scenes, with --rerecord),
--part 1..4|intro|closing (only one section), --list, --devices / --device.

Needs only: pip install sounddevice numpy
(Linux also needs PortAudio: sudo apt install libportaudio2)
"""
from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True  # no __pycache__ folders left behind
import record_demo as R  # noqa: E402  (stdlib-only at import time; no browser needed)
import scenes as S  # noqa: E402

PARTS = ["intro", "1", "2", "3", "4", "closing"]


def audio_libs():
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        sys.exit("Recording needs two small packages. Run:  pip install sounddevice numpy")
    except OSError:
        sys.exit("The PortAudio audio library is missing. On Linux run:  sudo apt install libportaudio2")
    return np, sd


def record_take(np, sd, device, rate: int):
    frames = []

    def callback(indata, _frames, _time, _status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=rate, channels=1, dtype="int16", device=device, callback=callback):
        input("  ● Recording... press Enter to STOP ")
    return np.concatenate(frames) if frames else np.zeros((0, 1), dtype="int16")


def save_wav(path: Path, data, rate: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data.tobytes())


def scenes_for(part: str) -> list[dict]:
    return [sc for sc in S.SCENES if R.speaker_for(sc["id"]) == part]


def show_plan() -> None:
    print("Scenes in order (saved as demo_video/voice/<scene id>.wav):\n")
    for part in PARTS:
        print(f"  {R.speaker_label(part).replace(' (any member)', '')}  (--part {part})")
        for sc in scenes_for(part):
            mark = "recorded" if R.find_take(sc["id"]) else "missing"
            print(f"      {sc['id']:22s} {mark}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", choices=PARTS, help="only the scenes of one section (default: all scenes)")
    ap.add_argument("--scene", nargs="*", help="record only these scene ids")
    ap.add_argument("--rerecord", action="store_true", help="redo scenes that already have a recording")
    ap.add_argument("--list", action="store_true", help="show every scene, its speaker, and what is recorded")
    ap.add_argument("--devices", action="store_true", help="list microphones and exit")
    ap.add_argument("--device", default=None, help="microphone number or name from --devices (default: system mic)")
    args = ap.parse_args()

    if args.list:
        show_plan()
        return
    np, sd = audio_libs()
    if args.devices:
        print(sd.query_devices())
        return

    device = int(args.device) if args.device and args.device.isdigit() else args.device
    try:
        info = sd.query_devices(device, "input")
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"No usable microphone found ({exc}). Check the mic, or pick one with --devices / --device.")
    rate = int(info["default_samplerate"]) or 48000

    todo = scenes_for(args.part) if args.part else list(S.SCENES)
    if args.scene:
        wanted = set(args.scene)
        todo = [sc for sc in S.SCENES if sc["id"] in wanted] or sys.exit(f"Unknown scene ids: {args.scene}")

    R.VOICE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nMicrophone: {info['name']}  ({rate} Hz)")
    print(f"{len(todo)} scene(s) to go through. Read each script in a natural, relaxed voice.")
    print("Small wording changes are fine; the captions use this text, so stay close to it.")
    print("Stop any time with Ctrl+C; run the same command again to continue.\n")

    for i, sc in enumerate(todo, 1):
        text = S.SELF_SCRIPTS.get(sc["id"], sc["say"])
        print("=" * 78)
        print(f"[{i}/{len(todo)}]  {sc['id']}   ·   {R.speaker_label(R.speaker_for(sc['id'])).replace(' (any member)', '')}")
        print("-" * 78)
        print(R.caption_text(text))
        print("=" * 78)
        existing = R.find_take(sc["id"])
        if existing and not args.rerecord:
            print(f"Already recorded ({existing.name}); skipping. Use --rerecord to redo.\n")
            continue
        while True:
            input("Press Enter to START recording... ")
            data = record_take(np, sd, device, rate)
            seconds = len(data) / rate
            peak = int(abs(data).max()) if len(data) else 0
            if seconds < 1.0 or peak < 300:
                print(f"  That take is {'too short' if seconds < 1.0 else 'almost silent'}; "
                      "check the microphone and its permission for this terminal, then try again.")
                continue
            answer = input(f"  Got {seconds:.1f}s. Enter = keep, p = play back, r = redo: ").strip().lower()
            if answer == "p":
                sd.play(data, rate)
                sd.wait()
                answer = input("  Enter = keep, r = redo: ").strip().lower()
            if answer != "r":
                out = R.VOICE_DIR / f"{sc['id']}.wav"
                for ext in R.VOICE_EXTS:  # one take per scene
                    old = R.VOICE_DIR / f"{sc['id']}{ext}"
                    if ext != ".wav" and old.exists():
                        old.rename(old.with_suffix(old.suffix + ".old"))
                save_wav(out, data, rate)
                print(f"  Saved {out.relative_to(HERE.parent)}\n")
                break

    missing = [sc["id"] for sc in S.SCENES if not R.find_take(sc["id"])]
    if missing:
        print(f"Still missing for the full video ({len(missing)}): {', '.join(missing)}")
        print("Run  python demo_video/record_voice.py  again to record them.")
    else:
        print("All scenes are recorded. Build the video with:")
        print("  python demo_video/record_demo.py --tts files --burn-subtitles")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Recorded scenes are saved; run the same command again to continue.")
