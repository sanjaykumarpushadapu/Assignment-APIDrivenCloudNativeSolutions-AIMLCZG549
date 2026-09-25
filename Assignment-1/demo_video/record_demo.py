#!/usr/bin/env python3
"""Automated demonstration-video recorder for Group 49 (AIMLCZG549 Assignment I).

One command produces the finished MP4:

    python demo_video/record_demo.py

What it does, in order:

1. Preflight: checks that the live dashboard, Swagger page and the four
   required API endpoints answer HTTP 200; runs ingestion, the test suite and
   a full pipeline run on this machine so the video shows real, current output.
2. Narration: fills the narration in ``scenes.py`` with the facts gathered in
   step 1 and turns each scene's text into speech (macOS ``say`` by default).
3. Recording: drives Chromium with Playwright, one clip per scene: title cards,
   report figures, source code, live terminal output, the live dashboard, and
   Swagger "Try it out -> Execute" on each required endpoint.
4. Assembly: trims each clip, lays the narration over it, and joins everything
   with ffmpeg into ``Group49_AIMLCZG549_Assignment1_Demo.mp4`` plus a
   matching ``.srt`` subtitle file and a ``run_report.json``.

See ``demo_video/README.md`` for setup and options.
"""
from __future__ import annotations

import argparse
import ast
import base64
import html
import json
import mimetypes
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True  # no __pycache__ folders left behind
import scenes as S  # noqa: E402

VIEWPORT = {"width": 1600, "height": 900}
OUT_W, OUT_H = 1920, 1080
LEAD_IN = 0.35      # seconds of picture before the narrator starts
TAIL = 0.75         # seconds of picture after the narrator stops
DEFAULT_OUT = "Group49_AIMLCZG549_Assignment1_Demo.mp4"
HOLD_MS = 2800      # minimum time a live result stays on screen after it appears


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")  # never crash on a console that can't show "●" or "·"
    except Exception:  # noqa: BLE001
        pass


def log(msg: str) -> None:
    print(f"[demo] {msg}", flush=True)


def fail(msg: str) -> None:
    print(f"\n[demo] ERROR: {msg}\n", file=sys.stderr, flush=True)
    sys.exit(1)


def ffmpeg_install_hint() -> str:
    """Return the install command appropriate for the current platform."""
    system = platform.system()
    if system == "Windows":
        return " Install it with: winget install Gyan.FFmpeg, then open a new terminal"
    if system == "Darwin":
        return " Install it with: brew install ffmpeg"
    if system == "Linux":
        return " Install it with: sudo apt install ffmpeg"
    return " Install ffmpeg with your operating system's package manager"


def refresh_windows_path() -> None:
    """Include the latest Windows user PATH in this process."""
    if platform.system() != "Windows":
        return
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            user_path = winreg.QueryValueEx(key, "Path")[0]
    except (FileNotFoundError, OSError):
        return
    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join(part for part in (user_path, current_path) if part)


# ======================================================================
# Preflight
# ======================================================================

def _ssl_context():
    """Use the operating system trust store when available.

    This handles enterprise certificates installed in Windows, macOS, or
    Linux system stores. Fall back to certifi for minimal Python installs.
    """
    import ssl
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def http_status(url: str, timeout: int = 45):
    req = urllib.request.Request(url, headers={"User-Agent": "group49-demo-recorder"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except urllib.error.URLError as exc:
        return f"unreachable ({exc.reason})"
    except Exception as exc:  # noqa: BLE001
        return f"unreachable ({exc.__class__.__name__}: {exc})"


def repo_python() -> str:
    for candidate in (REPO / ".venv/bin/python", REPO / ".venv/Scripts/python.exe"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def run_capture(argv: list[str], timeout: int = 900) -> tuple[int, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("MPLBACKEND", "Agg")
    proc = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).rstrip()


def pytest_summary(output: str) -> str:
    parts = []
    for word in ("passed", "failed", "skipped", "error", "errors"):
        m = re.search(rf"(\d+) {word}\b", output)
        if m:
            parts.append(f"{m.group(1)} {word}")
    if not parts:
        return "the test run did not report a result"
    return ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1]


def preflight(args, work: Path) -> dict:
    facts: dict[str, str] = {}

    # ---- 1. live URLs --------------------------------------------------
    log("Preflight 1/2: checking live URLs")
    urls = {"dashboard": args.dashboard_url, "docs": args.api_url + "/docs",
            "health": args.api_url + "/health"}
    for path in S.REQUIRED_ENDPOINTS:
        urls[path] = args.api_url + path
    bad = []
    for key, url in urls.items():
        status = http_status(url)
        log(f"    {status}  {url}")
        if key.startswith("/"):
            facts[f"status_{key}"] = str(status)
        if status != 200:
            bad.append(f"{url} -> {status}")
    if bad and not args.allow_non_200:
        fail("these live URLs did not return HTTP 200:\n  " + "\n  ".join(bad) +
             "\nThe narration states each endpoint's status, so recording stops here. "
             "Fix or redeploy the service, or pass --allow-non-200 to record anyway.")

    # ---- 2. live commands ----------------------------------------------
    cache = HERE / "output" / "terminal_outputs.json"
    legacy = HERE / "output" / "work" / "terminal_outputs.json"
    if args.skip_commands and not cache.exists() and legacy.exists():
        cache.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
    if args.skip_commands:
        if not cache.exists():
            fail("--skip-commands needs output from a previous full run. Run once without --skip-commands.")
        outputs = json.loads(cache.read_text())
        log("Preflight 2/2: reusing cached command output (--skip-commands)")
    else:
        log("Preflight 2/2: running ingestion, tests and the pipeline on this machine")
        py = repo_python()
        outputs = {}
        for key, spec in S.TERMINAL_COMMANDS.items():
            argv = [py if a == "{py}" else a for a in spec["argv"]]
            log(f"    $ {spec['shown_as']}")
            started = time.time()
            code, text = run_capture(argv)
            log(f"      exit {code} in {time.time() - started:.1f}s")
            outputs[key] = {"shown_as": spec["shown_as"], "exit_code": code, "output": text}
            if code != 0 and key != "pytest":
                fail(f"'{spec['shown_as']}' failed (exit {code}). Last lines:\n" +
                     "\n".join(text.splitlines()[-15:]))
        cache.write_text(json.dumps(outputs, indent=2))
    facts["pytest_summary"] = pytest_summary(outputs["pytest"]["output"])
    if outputs["pytest"]["exit_code"] != 0:
        log(f"    WARNING: tests did not all pass ({facts['pytest_summary']}); "
            "the narration will say so.")

    # ---- execution log facts --------------------------------------------
    log_path = REPO / S.EXECUTION_LOG
    if log_path.exists():
        data = json.loads(log_path.read_text())
        facts.update({
            "run_status": str(data.get("status", "unknown")),
            "input_rows": f"{data.get('input_rows', 0):,}",
            "output_rows": f"{data.get('output_rows', 0):,}",
            "duplicates": f"{data.get('duplicates_detected', 0):,}",
            "duration": f"{float(data.get('duration_seconds', 0)):.1f}",
        })
    return {"facts": facts, "terminal": outputs}


# ======================================================================
# Narration (text-to-speech)
# ======================================================================

def fill(text: str, facts: dict, scene_id: str) -> str:
    try:
        return text.format_map(facts)
    except KeyError as exc:
        fail(f"scene '{scene_id}' narration needs {exc}, which preflight did not produce.")
    return text


def media_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def synthesize(text: str, dest: Path, args) -> Path:
    if args.tts == "say":
        out = dest.with_suffix(".aiff")
        cmd = ["say", "-r", str(args.rate), "-o", str(out)]
        if args.voice:
            cmd[1:1] = ["-v", args.voice]
        cmd.append(text)
        if subprocess.run(cmd, capture_output=True).returncode != 0 and args.voice:
            log(f"    voice '{args.voice}' unavailable; using the system default voice")
            subprocess.run(["say", "-r", str(args.rate), "-o", str(out), text], check=True)
        return out
    if args.tts == "edge":
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            fail("edge-tts is not installed in this Python environment. Run: pip install edge-tts")
        out = dest.with_suffix(".mp3")
        proc = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", args.voice or "en-US-AriaNeural",
                               "--text", text, "--write-media", str(out)], capture_output=True, text=True)
        if proc.returncode != 0:
            fail("edge-tts could not create the narration:\n" + "\n".join((proc.stderr or proc.stdout).splitlines()[-8:]))
        return out
    # "none": silent track sized to a natural reading pace, for a later voice-over
    out = dest.with_suffix(".wav")
    seconds = max(1.8, len(text.split()) / 2.4 + 0.4)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=48000:cl=stereo", "-t", f"{seconds:.2f}", str(out)], check=True)
    return out


# ======================================================================
# HTML scene builders
# ======================================================================

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#0f172a;color:#e2e8f0;
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.caption{position:fixed;left:0;right:0;bottom:0;padding:14px 32px;font-size:22px;
 background:rgba(15,23,42,.88);color:#f8fafc;border-top:2px solid #38bdf8;letter-spacing:.2px}
@keyframes fadein{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
"""


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def page_html(body: str, extra_css: str = "", script: str = "") -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}{extra_css}</style>"
            f"</head><body>{body}<script>{script}</script></body></html>")


def card_html(scene: dict, dur: float) -> str:
    e = html.escape
    lines = "".join(f"<li>{e(x)}</li>" for x in scene.get("lines", []))
    css = """
body{display:flex;align-items:center;justify-content:center;
 background:radial-gradient(circle at 30% 20%,#1e3a8a 0%,#0f172a 60%)}
.card{max-width:1250px;text-align:center;animation:fadein .8s ease both}
.eyebrow{font-size:22px;letter-spacing:3px;text-transform:uppercase;color:#7dd3fc;margin-bottom:28px}
h1{font-size:60px;line-height:1.15;font-weight:750;color:#fff}
h2{font-size:34px;font-weight:500;color:#bae6fd;margin-top:26px}
ul{list-style:none;margin-top:40px;display:flex;flex-wrap:wrap;justify-content:center;gap:14px 34px}
li{font-size:27px;color:#e2e8f0;animation:fadein .8s ease both}
li:nth-child(1){animation-delay:.4s}li:nth-child(2){animation-delay:.6s}
li:nth-child(3){animation-delay:.8s}li:nth-child(4){animation-delay:1s}
.foot{position:fixed;bottom:26px;left:0;right:0;text-align:center;font-size:17px;color:#94a3b8}
"""
    body = (f"<div class='card'><div class='eyebrow'>{e(scene.get('eyebrow', ''))}</div>"
            f"<h1>{e(scene['title'])}</h1>"
            + (f"<h2>{e(scene['subtitle'])}</h2>" if scene.get("subtitle") else "")
            + (f"<ul>{lines}</ul>" if lines else "") + "</div>"
            + (f"<div class='foot'>{e(scene['footnote'])}</div>" if scene.get("footnote") else ""))
    return page_html(body, css)


def images_html(scene: dict, dur: float, images_dir: Path) -> str:
    files = [images_dir / name for name in scene["images"]]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        fail(f"scene '{scene['id']}' image(s) not found: {missing}")
    slot = dur / len(files)
    imgs = "".join(f"<img src='{data_uri(f)}' class='{'on' if i == 0 else ''}'>" for i, f in enumerate(files))
    css = f"""
body{{background:#f8fafc}}
.stage{{position:fixed;inset:0 0 64px 0;display:flex;align-items:center;justify-content:center}}
.stage img{{position:absolute;max-width:94%;max-height:92%;object-fit:contain;opacity:0;
 transition:opacity .7s ease;box-shadow:0 10px 40px rgba(15,23,42,.25);border-radius:6px;background:#fff}}
.stage img.on{{opacity:1;animation:zoom {slot:.2f}s linear both}}
@keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(1.035)}}}}
"""
    script = f"""
const imgs=[...document.querySelectorAll('.stage img')];let i=0;
setInterval(()=>{{if(i<imgs.length-1){{imgs[i].classList.remove('on');i++;imgs[i].classList.add('on');}}}},{slot * 1000:.0f});
"""
    body = f"<div class='stage'>{imgs}</div><div class='caption'>{html.escape(scene.get('caption', ''))}</div>"
    return page_html(body, css, script)


SCROLL_JS = """
function autoScroll(el,durMs,delayMs){
 const max=el.scrollHeight-el.clientHeight; if(max<=0) return;
 const t0=performance.now()+delayMs;
 function step(t){const k=Math.max(0,Math.min(1,(t-t0)/durMs));
  el.scrollTop=max*(k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2); if(k<1) requestAnimationFrame(step);}
 requestAnimationFrame(step);}
"""


def code_blocks(scene: dict) -> list[tuple[int, list[str]]]:
    path = REPO / scene["file"]
    if not path.exists():
        fail(f"scene '{scene['id']}': source file not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = []
    if scene.get("functions"):
        tree = ast.parse("\n".join(lines))
        wanted = {n.name: n for n in ast.walk(tree)
                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in scene["functions"]}
        for name in scene["functions"]:
            node = wanted.get(name)
            if node is None:
                log(f"    note: function {name}() not found in {scene['file']}; skipped")
                continue
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            blocks.append((start, lines[start - 1:node.end_lineno]))
    if scene.get("regex"):
        idx = next((i for i, line in enumerate(lines) if re.search(scene["regex"], line)), None)
        if idx is not None:
            lo, hi = scene.get("window", [-10, 20])
            a, b = max(0, idx + lo), min(len(lines), idx + hi)
            blocks.append((a + 1, lines[a:b]))
    return blocks or [(1, lines[:80])]


def code_html(scene: dict, dur: float) -> str:
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import PythonLexer
    except ImportError:
        highlight = None
    hl_re = re.compile(scene["highlight"]) if scene.get("highlight") else None
    parts = []
    for start, block in code_blocks(scene):
        src = "\n".join(block)
        hl = [i + 1 for i, line in enumerate(block) if hl_re and hl_re.search(line)]
        if highlight:
            fmt = HtmlFormatter(style="monokai", linenos="inline", linenostart=start, hl_lines=hl, nowrap=False)
            parts.append(highlight(src, PythonLexer(), fmt))
        else:
            parts.append("<pre>" + "\n".join(f"{start + i:4d}  {html.escape(line)}"
                                             for i, line in enumerate(block)) + "</pre>")
    css = ""
    if highlight:
        from pygments.formatters import HtmlFormatter
        css = HtmlFormatter(style="monokai").get_style_defs(".highlight")
    css += """
body{background:#272822}
.head{position:fixed;top:0;left:0;right:0;height:52px;background:#1e1f1c;display:flex;align-items:center;
 padding:0 22px;gap:9px;border-bottom:1px solid #3e3d32;z-index:2}
.dot{width:13px;height:13px;border-radius:50%}.file{margin-left:14px;color:#cfcfc2;font:16px Menlo,Consolas,monospace}
#scroller{position:fixed;top:52px;bottom:64px;left:0;right:0;overflow:hidden;padding:18px 34px}
.highlight,.highlight pre,pre{background:#272822!important;font:21px/1.5 Menlo,Consolas,"DejaVu Sans Mono",monospace;color:#f8f8f2}
.highlight .hll{background:#49483e!important;display:block}
.highlight .linenos{color:#75715e;padding-right:16px}
.sep{color:#75715e;font:20px Menlo,monospace;margin:14px 0 14px 8px}
"""
    sep = "<div class='sep'>⋮</div>"
    body = (f"<div class='head'><span class='dot' style='background:#ff5f56'></span>"
            f"<span class='dot' style='background:#ffbd2e'></span><span class='dot' style='background:#27c93f'></span>"
            f"<span class='file'>{html.escape(scene['file'])}</span></div>"
            f"<div id='scroller'>{sep.join(parts)}</div>"
            f"<div class='caption'>{html.escape(scene.get('caption', ''))}</div>")
    script = SCROLL_JS + f"autoScroll(document.getElementById('scroller'),{max(1.0, dur - 2.2) * 1000:.0f},1200);"
    return page_html(body, css, script)


def terminal_html(scene: dict, dur: float, terminal: dict) -> str:
    items = []
    for key in scene["commands"]:
        entry = terminal[key]
        out = entry["output"].splitlines()
        if len(out) > 22:
            out = out[:3] + ["…"] + out[-18:]
        items.append({"cmd": entry["shown_as"], "out": out})
    css = """
body{background:#0b1020;display:flex;align-items:flex-start;justify-content:center;padding-top:34px}
.win{width:1480px;height:760px;background:#0d1117;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.6);
 overflow:hidden;border:1px solid #30363d}
.bar{height:40px;background:#161b22;display:flex;align-items:center;padding:0 16px;gap:8px;color:#8b949e;font:14px Menlo,monospace}
.dot{width:12px;height:12px;border-radius:50%}
#term{padding:18px 24px;height:720px;overflow:hidden;font:19px/1.45 Menlo,Consolas,"DejaVu Sans Mono",monospace;
 color:#c9d1d9;white-space:pre-wrap;word-break:break-all}
.p{color:#7ee787}.c{color:#fff}.pass{color:#3fb950}.fail{color:#f85149}
"""
    body = ("<div class='win'><div class='bar'><span class='dot' style='background:#ff5f56'></span>"
            "<span class='dot' style='background:#ffbd2e'></span><span class='dot' style='background:#27c93f'></span>"
            "&nbsp;&nbsp;Assignment-1 — live run</div><div id='term'></div></div>"
            "<div class='caption'>" + html.escape(scene.get("caption", "Live terminal output from this machine")) + "</div>")
    script = f"""
const ITEMS={json.dumps(items)};const DUR={dur * 1000:.0f};
const term=document.getElementById('term');
const esc=s=>s.replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
const colour=s=>esc(s).replace(/\\b(\\d+ passed)/g,'<span class="pass">$1</span>').replace(/\\b(\\d+ failed)/g,'<span class="fail">$1</span>');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{{
 const totalLines=ITEMS.reduce((n,it)=>n+it.out.length+1,0);
 const perLine=Math.max(25,Math.min(220,(DUR*0.62)/Math.max(1,totalLines)));
 await sleep(500);
 for(const it of ITEMS){{
  const line=document.createElement('div');line.innerHTML='<span class="p">$ </span><span class="c"></span>';
  term.appendChild(line);const c=line.querySelector('.c');
  for(const ch of it.cmd){{c.textContent+=ch;await sleep(16);}}
  await sleep(450);
  for(const o of it.out){{const d=document.createElement('div');d.innerHTML=colour(o)||'&nbsp;';term.appendChild(d);
   term.scrollTop=term.scrollHeight;await sleep(perLine);}}
  const gap=document.createElement('div');gap.innerHTML='&nbsp;';term.appendChild(gap);await sleep(500);
 }}
 const l=document.createElement('div');l.innerHTML='<span class="p">$ </span>▍';term.appendChild(l);term.scrollTop=term.scrollHeight;
}})();
"""
    return page_html(body, css, script)


URLBAR_JS = r"""
(() => {
  const H = 46;
  const install = () => {
    if (!document.body || document.getElementById('__demo_urlbar')) return;
    const bar = document.createElement('div');
    bar.id = '__demo_urlbar';
    Object.assign(bar.style, {position:'fixed', top:'0', left:'0', right:'0', height:H+'px', zIndex:'2147483645',
      background:'#dee1e6', display:'flex', alignItems:'center', gap:'10px', padding:'0 16px',
      boxShadow:'0 1px 0 #c4c7cc', font:'15px -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif'});
    bar.innerHTML = '<span style="display:flex;gap:7px;margin-right:8px">' +
      ['#ff5f56','#ffbd2e','#27c93f'].map(c => '<i style="width:12px;height:12px;border-radius:50%;background:'+c+'"></i>').join('') +
      '</span><div style="flex:1;height:32px;border-radius:16px;background:#fff;display:flex;align-items:center;' +
      'padding:0 14px;gap:8px;color:#202124;overflow:hidden;white-space:nowrap">' +
      '<svg width="14" height="14" viewBox="0 0 24 24"><path fill="#188038" d="M12 1a5 5 0 0 0-5 5v4H5v13h14V10h-2V6a5 5 0 0 0-5-5zm-3 9V6a3 3 0 0 1 6 0v4z"/></svg>' +
      '<span id="__demo_url"></span></div>';
    document.documentElement.appendChild(bar);
    document.body.style.marginTop = H + 'px';
    const update = () => { const u = document.getElementById('__demo_url'); if (u) u.textContent = location.href; };
    update();
    window.addEventListener('hashchange', update);
    setInterval(update, 400);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install); else install();
})();
"""


def typing_html(url: str) -> str:
    """A blank browser tab whose address bar types the URL about to be opened."""
    script = f"""
const target = {json.dumps(url)};
window.__typed = '';
const t = setInterval(() => {{
  window.__typed = target.slice(0, window.__typed.length + 2);
  const u = document.getElementById('__demo_url');
  if (u) u.textContent = window.__typed;
  if (window.__typed.length >= target.length) clearInterval(t);
}}, 1100 / Math.max(1, target.length / 2));
"""
    return page_html("", "html,body{background:#fff}",
                     URLBAR_JS.replace("location.href", "(window.__typed || '')") + script)


def links_html(scene: dict, dur: float) -> str:
    e = html.escape
    rows = "".join(
        f"<div class='row' style='animation-delay:{0.25 + i * 0.35:.2f}s'><div class='label'>{e(label)}</div>"
        f"<div class='url'>{e(url)}</div></div>"
        for i, (label, url) in enumerate(scene["links"]))
    css = """
body{display:flex;align-items:flex-start;justify-content:center;padding-top:60px;
 background:radial-gradient(circle at 70% 20%,#0f3d63 0%,#0f172a 60%)}
.box{width:1400px;animation:fadein .7s ease both}
h1{font-size:44px;color:#fff;margin-bottom:26px}
.row{display:flex;gap:28px;align-items:baseline;padding:16px 22px;margin:10px 0;border-radius:10px;
 background:rgba(255,255,255,.06);border:1px solid rgba(125,211,252,.25);animation:fadein .6s ease both}
.label{width:330px;flex:none;color:#7dd3fc;font-size:21px}
.url{color:#f8fafc;font:21px Menlo,Consolas,"DejaVu Sans Mono",monospace;word-break:break-all}
"""
    body = (f"<div class='box'><h1>{e(scene.get('title', 'Live links'))}</h1>{rows}</div>"
            f"<div class='caption'>{e(scene.get('caption', ''))}</div>")
    return page_html(body, css)


def json_html(scene: dict, dur: float) -> str:
    path = REPO / scene["file"]
    if not path.exists():
        fail(f"scene '{scene['id']}': {path} not found (the pipeline run should have written it).")
    data = json.loads(path.read_text())
    shown = {}
    for key, value in data.items():
        if key == "data_quality" and isinstance(value, dict):
            shown[key] = {k: value[k] for k in ("rows", "columns", "quality_status") if k in value}
            shown[key]["…"] = "schema, dtypes, summary statistics, missing values"
        elif key == "eda_outputs" and isinstance(value, dict):
            shown[key] = {k: value[k] for k in ("rows", "columns", "correlation_matrix", "binned_features",
                                                "binned_features_encoded") if k in value}
            shown[key]["…"] = "charts, bivariate outputs, encoding report"
        else:
            shown[key] = value
    text = json.dumps(shown, indent=2)
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import JsonLexer
        rendered = highlight(text, JsonLexer(), HtmlFormatter(style="monokai"))
        css = HtmlFormatter(style="monokai").get_style_defs(".highlight")
    except ImportError:
        rendered, css = f"<pre>{html.escape(text)}</pre>", ""
    css += """
body{background:#272822}
.head{position:fixed;top:0;left:0;right:0;height:52px;background:#1e1f1c;display:flex;align-items:center;
 padding:0 24px;color:#cfcfc2;font:16px Menlo,Consolas,monospace;border-bottom:1px solid #3e3d32}
#scroller{position:fixed;top:52px;bottom:64px;left:0;right:0;overflow:hidden;padding:18px 40px}
.highlight,.highlight pre,pre{background:#272822!important;font:21px/1.5 Menlo,Consolas,monospace;color:#f8f8f2}
"""
    body = (f"<div class='head'>{html.escape(scene['file'])}</div><div id='scroller'>{rendered}</div>"
            f"<div class='caption'>{html.escape(scene.get('caption', ''))}</div>")
    script = SCROLL_JS + f"autoScroll(document.getElementById('scroller'),{max(1.0, dur - 2.5) * 1000:.0f},1500);"
    return page_html(body, css, script)


# ======================================================================
# Browser helpers (live pages)
# ======================================================================

CURSOR_JS = r"""
(() => {
  const install = () => {
    if (document.getElementById('__demo_cursor') || !document.documentElement) return;
    const c = document.createElement('div'); c.id = '__demo_cursor';
    c.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 2l16 9-7 2-3 7z" fill="#111" stroke="#fff" stroke-width="1.6"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'0', top:'0', zIndex:'2147483647', pointerEvents:'none',
      transform:'translate(800px,450px)', transition:'transform .6s ease'});
    document.documentElement.appendChild(c);
  };
  window.__moveCursor = (x, y, ms) => { install(); const c = document.getElementById('__demo_cursor');
    c.style.transition = `transform ${ms}ms ease`; c.style.transform = `translate(${x}px,${y}px)`; };
  window.__pulse = (x, y) => { const r = document.createElement('div');
    Object.assign(r.style, {position:'fixed', left:(x-18)+'px', top:(y-18)+'px', width:'36px', height:'36px',
      borderRadius:'50%', border:'3px solid #f97316', zIndex:'2147483646', pointerEvents:'none',
      transition:'transform .45s ease, opacity .45s ease'});
    document.documentElement.appendChild(r);
    requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 600); };
  document.addEventListener('DOMContentLoaded', install);
})();
"""

SMOOTH_TO_JS = """
([to, ms]) => new Promise(done => {
  const from = window.scrollY, t0 = performance.now();
  const step = t => { const k = Math.min(1, (t - t0) / ms);
    window.scrollTo(0, from + (to - from) * (k < .5 ? 2*k*k : 1 - Math.pow(-2*k + 2, 2) / 2));
    k < 1 ? requestAnimationFrame(step) : done(); };
  requestAnimationFrame(step); })
"""


def smooth_scroll(page, to: float, ms: int) -> None:
    page.evaluate(SMOOTH_TO_JS, [to, ms])


def scroll_to_locator(page, locator, offset: int = 110, ms: int = 900) -> None:
    top = locator.evaluate("(el) => el.getBoundingClientRect().top + window.scrollY")
    smooth_scroll(page, max(0, top - offset), ms)


def cursor_click(page, locator) -> None:
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    if box:
        x, y = box["x"] + min(box["width"] / 2, 60), box["y"] + box["height"] / 2
        page.evaluate("([x, y]) => window.__moveCursor && window.__moveCursor(x, y, 650)", [x, y])
        page.wait_for_timeout(700)
        page.evaluate("([x, y]) => window.__pulse && window.__pulse(x, y)", [x, y])
    locator.click()


def settle(page, timeout_ms: int = 20000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:  # noqa: BLE001 - pages that poll never go idle; carry on
        page.wait_for_timeout(1500)


def swagger_execute(page, path: str) -> str:
    summary = page.locator(f'.opblock-summary-path[data-path="{path}"]')
    if summary.count() == 0:
        summary = page.locator(".opblock-summary-path", has_text=re.compile(rf"^{re.escape(path)}$"))
    summary = summary.first
    block = page.locator(".opblock").filter(has=summary).first
    scroll_to_locator(page, summary, offset=140)
    page.wait_for_timeout(300)
    cursor_click(page, summary)
    page.wait_for_timeout(700)
    cursor_click(page, block.locator("button.try-out__btn"))
    page.wait_for_timeout(500)
    cursor_click(page, block.locator("button.execute"))
    status_cell = block.locator(".live-responses-table tr.response .response-col_status").first
    status_cell.wait_for(state="visible", timeout=90000)
    page.wait_for_timeout(600)
    scroll_to_locator(page, block.locator(".live-responses-table").first, offset=190, ms=1100)
    return status_cell.inner_text().strip().split()[0]


# ======================================================================
# Recording
# ======================================================================

def launch_signed_in(pw, profile_dir: Path, headless: bool, **opts):
    """Browser that keeps your Google sign-in between runs (used only for the live Cloud console).

    Uses your installed Google Chrome when available (Google accepts sign-in there more
    readily), otherwise Playwright's Chromium. The automation banner is switched off.
    """
    kwargs = dict(headless=headless, chromium_sandbox=True,
                  ignore_default_args=["--enable-automation"], **opts)
    try:
        return pw.chromium.launch_persistent_context(str(profile_dir), channel="chrome", **kwargs)
    except Exception:  # noqa: BLE001 - Google Chrome not installed
        return pw.chromium.launch_persistent_context(str(profile_dir), **kwargs)


def resolve_url(url: str, args) -> str:
    """Apply --api-url / --dashboard-url overrides to URLs written in scenes.py."""
    if url.startswith(S.API_URL):
        return args.api_url + url[len(S.API_URL):]
    if url.rstrip("/") == S.DASHBOARD_URL.rstrip("/"):
        return args.dashboard_url
    return url


def record_scene(browser_factory, scene: dict, target: float, ctx_info: dict, args, images_dir: Path,
                 clip_dir: Path, terminal: dict, report: dict):
    kind = scene["kind"]
    live = kind in ("url", "swagger") or (kind == "composer" and args.composer_live)
    context = browser_factory(live_composer=(kind == "composer" and args.composer_live))
    page = context.pages[0] if context.pages else context.new_page()
    t_page = time.monotonic()
    if live:
        page.add_init_script(CURSOR_JS)
        page.add_init_script(URLBAR_JS)  # show the real address of every live page

    if kind == "card":
        page.set_content(card_html(scene, target), wait_until="load")
    elif kind == "image" or (kind == "composer" and not args.composer_live):
        page.set_content(images_html(scene, target, images_dir), wait_until="load")
    elif kind == "code":
        page.set_content(code_html(scene, target), wait_until="load")
    elif kind == "terminal":
        page.set_content(terminal_html(scene, target, terminal), wait_until="load")
    elif kind == "json":
        page.set_content(json_html(scene, target), wait_until="load")
    elif kind == "links":
        page.set_content(links_html(scene, target), wait_until="load")
    elif kind == "url":
        # Start on an empty tab and type the address, so the viewer sees the site being opened.
        page.set_content(typing_html(resolve_url(scene["url"], args)), wait_until="load")
    elif kind == "composer":
        page.goto(resolve_url(scene["url"], args), wait_until="domcontentloaded", timeout=90000)
        settle(page)
    elif kind == "swagger":
        page.goto(args.api_url + "/docs", wait_until="domcontentloaded", timeout=90000)
        page.locator(".opblock").first.wait_for(timeout=60000)
        page.wait_for_timeout(400)
    else:
        fail(f"unknown scene kind '{kind}' in scene '{scene['id']}'")

    page.wait_for_timeout(250)
    t_ready = time.monotonic()

    # ---- actions -------------------------------------------------------
    if kind == "url":
        page.wait_for_timeout(1500)  # address being typed
        page.goto(resolve_url(scene["url"], args), wait_until="domcontentloaded", timeout=90000)
        if scene.get("wait_for"):
            page.locator(scene["wait_for"]).first.wait_for(timeout=60000)
        settle(page)
    if kind == "url" and scene.get("scroll"):
        page.wait_for_timeout(1500)
        height = page.evaluate("document.documentElement.scrollHeight - window.innerHeight")
        if height > 20:
            smooth_scroll(page, height, int(max(2.0, target * 0.55) * 1000))
            page.wait_for_timeout(900)
            smooth_scroll(page, 0, 1600)
            page.wait_for_timeout(HOLD_MS)
    elif kind == "composer" and args.composer_live:
        page.wait_for_timeout(1500)
        height = page.evaluate("document.documentElement.scrollHeight - window.innerHeight")
        if height > 20:
            smooth_scroll(page, min(height, 700), 2500)
    elif kind == "swagger":
        observed = swagger_execute(page, scene["path"])
        report.setdefault("swagger_status", {})[scene["path"]] = observed
        log(f"    Swagger {scene['path']} -> HTTP {observed}")
        page.wait_for_timeout(HOLD_MS)  # keep the response on screen

    remaining = target - (time.monotonic() - t_ready)
    if remaining > 0:
        page.wait_for_timeout(remaining * 1000)
    visible = time.monotonic() - t_ready
    video = page.video
    context.close()
    src = Path(video.path())
    clip = clip_dir / f"{scene['id']}.webm"
    shutil.move(str(src), clip)
    return clip, max(0.0, t_ready - t_page), visible


# ======================================================================
# Assembly
# ======================================================================

def build_segment(clip: Path, start: float, span: float, speed: float, duration: float,
                  audio: Path, out: Path) -> None:
    """Cut [start, start+span] from the clip, retime it by `speed`, and lay the narration over it."""
    vf = (f"[0:v]setpts=PTS-STARTPTS,trim=start={start:.3f}:duration={span:.3f},"
          f"setpts=(PTS-STARTPTS)/{speed:.5f},"
          f"fps=30,scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
          f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
          f"tpad=stop_mode=clone:stop_duration=6,format=yuv420p[v];"
          f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
          f"adelay={int(LEAD_IN * 1000)}|{int(LEAD_IN * 1000)},apad[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-i", str(audio),
                    "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.3f}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(out)], check=True)


SPOKEN_TO_WRITTEN = [
    ("A.I.M.L. C.Z.G. 5 4 9", "AIMLCZG549"),
    ("Diabetes 0 1 2", "Diabetes_012"),
]


def caption_text(text: str) -> str:
    """Turn narration written for the speech engine back into normal text."""
    for spoken, written in SPOKEN_TO_WRITTEN:
        text = text.replace(spoken, written)
    # "B.M.I." -> "BMI", "C.D.C.'s" -> "CDC's", "E.D.A." -> "EDA"
    return re.sub(r"\b((?:[A-Z]\.){2,})", lambda m: m.group(1).replace(".", ""), text)


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def speech_chunks(text: str) -> list[str]:
    """Split narration into short phrases at natural pauses.

    Each phrase is spoken separately, so its caption can be timed from the
    real audio instead of being estimated.
    """
    chunks, cur = [], []
    for word in text.split():
        cur.append(word)
        line = " ".join(cur)
        acronym = re.fullmatch(r"(?:[A-Z]\.)+", word) is not None
        sentence_end = word.endswith((".", "?", "!")) and not acronym and len(line) >= 20
        clause_end = word.endswith((",", ";", ":")) and len(line) >= 55
        if sentence_end or clause_end or len(line) >= 110:
            chunks.append(line)
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def narrate_scene(text: str, dest: Path, args) -> tuple[Path, float, list[tuple[float, float, str]]]:
    """Speak each phrase separately, join them, and return exact caption timings."""
    parts, cues, t = [], [], 0.0
    for k, chunk in enumerate(speech_chunks(text)):
        clip = synthesize(chunk, dest.parent / f"{dest.name}_{k:02d}", args)
        d = media_duration(clip)
        parts.append(clip)
        cues.append((t, t + d, caption_text(chunk)))
        t += d
    out = dest.with_suffix(".wav")
    inputs = [x for part in parts for x in ("-i", str(part))]
    labels = "".join(f"[a{i}]" for i in range(len(parts)))
    graph = ";".join(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]" for i in range(len(parts)))
    graph += f";{labels}concat=n={len(parts)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", "[out]", str(out)],
                   check=True)
    return out, media_duration(out), cues


# ----------------------------------------------------------------------
# Team members' own voices (--record-voice, --tts files)
# ----------------------------------------------------------------------

VOICE_DIR = HERE / "voice"
VOICE_EXTS = (".wav", ".m4a", ".mp3", ".aiff", ".aac", ".caf")


def speaker_for(scene_id: str) -> str:
    """Who should read this scene: the member who owns that part of the project."""
    owner = "intro"
    for sc in S.SCENES:
        m = re.fullmatch(r"part(\d)_card", sc["id"])
        if m:
            owner = m.group(1)
        if sc["id"] == "closing":
            owner = "closing"
        if sc["id"] == scene_id:
            return owner
    return owner


def speaker_label(key: str) -> str:
    if key in ("intro", "closing"):
        return f"{key.title()} (any member)"
    return f"Part {key}: {S.MEMBERS[int(key) - 1]}"


def find_take(scene_id: str) -> Path | None:
    for ext in VOICE_EXTS:
        f = VOICE_DIR / f"{scene_id}{ext}"
        if f.exists():
            return f
    return None


def script_for(sc: dict, args) -> str:
    """First-person script when a team member speaks; third-person text for the synthesized narrator."""
    if args.tts == "files":
        return getattr(S, "SELF_SCRIPTS", {}).get(sc["id"], sc["say"])
    return sc["say"]


def human_scene_audio(scene_id: str, text: str, work: Path) -> tuple[Path, float, list[tuple[float, float, str]]]:
    take = find_take(scene_id)
    if take is None:
        fail(f"no voice recording for scene '{scene_id}'. Expected {VOICE_DIR}/{scene_id}.wav (or .m4a/.mp3). "
             "Record it with: python demo_video/record_voice.py --part <1-4|intro|closing>")
    out = work / "audio" / f"{scene_id}.wav"
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse,"
            "aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(take), "-af", trim, str(out)], check=True)
    dur = media_duration(out)
    # One take per scene: spread its phrases over the take in proportion to their length.
    chunks = speech_chunks(text)
    total = sum(len(c) for c in chunks) or 1
    cues, t = [], 0.0
    for c in chunks:
        d = dur * len(c) / total
        cues.append((t, t + d, caption_text(c)))
        t += d
    return out, dur, cues


def srt_entries(text: str, start: float, length: float) -> list[tuple[float, float, str]]:
    words = text.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) > 64 or w.endswith((".", "?", "!")) and len(cur) > 5:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    total = sum(len(c) for c in chunks) or 1
    out, t = [], start
    for c in chunks:
        d = length * len(c) / total
        out.append((t, t + d, c))
        t += d
    return out


# ----------------------------------------------------------------------
# Captions burned into the picture (no libass needed)
# ----------------------------------------------------------------------

CAPTION_FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    def secs(stamp: str) -> float:
        h, m, rest = stamp.strip().split(":")
        s_, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s_) + int(ms) / 1000
    entries = []
    for block in path.read_text(encoding="utf-8").strip().split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = lines[1].split("-->")
            entries.append((secs(a), secs(b), " ".join(lines[2:])))
    return entries


def _caption_png(text: str, dest: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        fail("Burning captions needs Pillow: pip install pillow")
    size = 40
    font = None
    for candidate in CAPTION_FONTS:
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, size)
            break
    if font is None:
        try:
            font = ImageFont.load_default(size=size)
        except TypeError:
            font = ImageFont.load_default()
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    max_w, lines, cur = OUT_W - 240, [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if probe.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    line_h, pad_x, pad_y = int(size * 1.3), 28, 14
    text_w = int(max(probe.textlength(line, font=font) for line in lines))
    img = Image.new("RGBA", (text_w + 2 * pad_x, line_h * len(lines) + 2 * pad_y), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=12, fill=(0, 0, 0, 175))
    for i, line in enumerate(lines):
        w = probe.textlength(line, font=font)
        draw.text(((img.width - w) / 2, pad_y + i * line_h), line, font=font, fill=(255, 255, 255, 255))
    img.save(dest)


def burn_captions(video: Path, entries: list[tuple[float, float, str]], out: Path, work: Path) -> None:
    """Overlay one caption image per subtitle entry, using only core ffmpeg filters."""
    cap_dir = work / "captions"
    cap_dir.mkdir(parents=True, exist_ok=True)
    inputs, chain, prev = ["-i", str(video)], [], "0:v"
    bottom = OUT_H - int(OUT_H * 64 / VIEWPORT["height"]) - 22   # sit just above each scene's caption bar
    for n, (a, b, text) in enumerate(entries, 1):
        png = cap_dir / f"cap_{n:03d}.png"
        _caption_png(text, png)
        inputs += ["-i", str(png)]
        label = f"v{n}"
        chain.append(f"[{prev}][{n}:v]overlay=x=(W-w)/2:y={bottom}-h:"
                     f"enable=between(t\\,{a:.3f}\\,{b:.3f})[{label}]")
        prev = label
    graph = ";".join(chain) if chain else "[0:v]null[v0]"
    last = prev if chain else "v0"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph,
                    "-map", f"[{last}]", "-map", "0:a", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)], check=True)


def finalize(joined: Path, entries, srt_path: Path, out_path: Path, burn: bool, work: Path) -> None:
    video_in = joined
    if burn:
        log("Burning captions into the picture")
        burned = work / "burned.mp4"
        burn_captions(joined, entries, burned, work)
        video_in = burned
    # Embedded, switchable closed-caption track (the CC button in QuickTime, VLC, etc.).
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video_in), "-i", str(srt_path),
                    "-map", "0:v", "-map", "0:a", "-map", "1:0", "-c:v", "copy", "-c:a", "copy",
                    "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                    "-metadata:s:s:0", "title=English (CC)", "-disposition:s:0", "default",
                    "-movflags", "+faststart", str(out_path)], check=True)


def _size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def clean(everything: bool = False, quiet: bool = False) -> None:
    """Delete temporary files. With everything=True, also the videos and voice recordings.

    Runs automatically (quiet=True) at the end of every successful build, so no
    separate clean-up command is normally needed.
    """
    out = HERE / "output"
    targets = [out / "work", out / "run_report.json"]
    targets += [out / f"{DEFAULT_OUT[:-4]}{ext}" for ext in (".mp4", ".srt")]  # pre-rename leftovers
    targets += list(HERE.rglob("__pycache__")) + list(HERE.rglob(".DS_Store"))
    if everything:
        print("This deletes ALL generated videos, captions, reports, cached command output and your voice")
        print(f"recordings in {VOICE_DIR}. Source files (scripts, scenes, README) are kept.")
        if input("Type yes to continue: ").strip().lower() != "yes":
            log("Nothing deleted.")
            return
        targets += [out, VOICE_DIR]  # output/ includes the saved Google sign-in (chrome-profile), if any
    freed, removed = 0, []
    for t in dict.fromkeys(targets):  # unique, in order
        if not t.exists():
            continue
        freed += _size(t)
        shutil.rmtree(t) if t.is_dir() else t.unlink()
        removed.append(t.relative_to(HERE))
    if quiet:
        if removed:
            log(f"Cleaned up temporary files ({freed / 1e6:.0f} MB freed).")
        return
    for r in removed:
        log(f"    removed {r}")
    log(f"Clean-up done: {len(removed)} item(s), {freed / 1e6:.0f} MB freed." if removed else "Already clean.")
    if not everything and out.exists():
        kept = sorted(p.name for p in out.iterdir())
        log("Kept in output/: " + (", ".join(kept) if kept else "(empty)"))


# ======================================================================
# Main
# ======================================================================

def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None,
                    help="final MP4 path (default: demo_video/output/Group49_..._Demo_<NoVoice|TeamVoice|AIVoice>.mp4)")
    ap.add_argument("--work", default=None, help="scratch folder for clips and audio")
    ap.add_argument("--tts", choices=["say", "edge", "none", "files"],
                    default="say" if platform.system() == "Darwin" else "edge",
                    help="say = macOS built-in voice (default on Mac); edge = Microsoft neural voice "
                         "(pip install edge-tts, needs internet); files = the team's own recordings in "
                         "demo_video/voice/ (see record_voice.py); none = silent track + subtitles")
    ap.add_argument("--voice", default=None, help="voice name, e.g. 'Samantha' or 'Ava (Premium)' for say, "
                                                  "'en-US-AriaNeural' for edge")
    ap.add_argument("--rate", type=int, default=178, help="say speaking rate in words per minute")
    ap.add_argument("--api-url", default=S.API_URL)
    ap.add_argument("--dashboard-url", default=S.DASHBOARD_URL)
    ap.add_argument("--only", nargs="*", help="record only these scene ids (for testing)")
    ap.add_argument("--list", action="store_true", help="list scene ids and exit")
    ap.add_argument("--headed", action="store_true", help="show the browser while recording")
    ap.add_argument("--allow-non-200", action="store_true", help="record even if a live URL is not HTTP 200")
    ap.add_argument("--skip-commands", action="store_true",
                    help="optional: reuse the previous run's terminal output; omit for a fresh run")
    ap.add_argument("--composer-live", action="store_true",
                    help="record the real Cloud Composer console (run --login-composer once first)")
    ap.add_argument("--login-composer", action="store_true",
                    help="open a browser once so you can sign in to Google Cloud yourself, then exit")
    ap.add_argument("--finish", action="store_true",
                    help="skip recording; rebuild the final MP4 (captions) from a previous run made with --keep-work")
    ap.add_argument("--clean", action="store_true",
                    help="delete temporary files now (this also happens automatically after every successful build)")
    ap.add_argument("--clean-all", action="store_true",
                    help="delete everything generated, including the videos and voice recordings (asks first)")
    ap.add_argument("--keep-work", action="store_true",
                    help="keep the temporary clips and audio (normally deleted after a successful build)")
    ap.add_argument("--burn-subtitles", action="store_true",
                    help="also draw the captions permanently into the picture (use this for Google Drive, "
                         "whose player ignores embedded caption tracks)")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    args.api_url = args.api_url.rstrip("/")
    mode = {"none": "NoVoice", "files": "TeamVoice"}.get(args.tts, "AIVoice")
    args.out = args.out or str(HERE / "output" / DEFAULT_OUT.replace(".mp4", f"_{mode}.mp4"))
    args.work = args.work or str(HERE / "output" / "work" / mode)
    if args.clean or args.clean_all:
        clean(everything=args.clean_all)
        return
    if args.list:
        for sc in S.SCENES:
            print(f"{sc['id']:22s} {sc['kind']:9s} {speaker_label(speaker_for(sc['id']))}")
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("Playwright is not installed. Run: pip install -r demo_video/requirements.txt && "
             "python -m playwright install chromium")
    refresh_windows_path()
    for tool in ("ffmpeg", "ffprobe") + (("say",) if args.tts == "say" else ()):
        if not shutil.which(tool):
            hint = ffmpeg_install_hint() if tool.startswith("ff") else ""
            fail(f"'{tool}' was not found on PATH." + hint)

    if args.finish:
        work, out_path = Path(args.work), Path(args.out)
        joined, srt_path = work / "joined.mp4", Path(args.out).with_suffix(".srt")
        if not joined.exists() or not srt_path.exists():
            fail("--finish needs a previous run made with --keep-work (its temporary files are deleted otherwise).")
        finalize(joined, parse_srt(srt_path), srt_path, out_path, args.burn_subtitles, work)
        log(f"Done: {out_path}")
        log(f"Captions:  embedded CC track{' + burned in' if args.burn_subtitles else ''}; also saved as {srt_path}")
        return

    profile_dir = HERE / "output" / "chrome-profile"
    if args.login_composer:
        with sync_playwright() as pw:
            ctx = launch_signed_in(pw, profile_dir, headless=False, viewport=VIEWPORT)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(S.COMPOSER_URL)
            input("\nSign in to Google Cloud in the browser window that opened (you type your own password),\n"
                  "wait until the Cloud Composer page shows the diabetes-risk-env environment,\n"
                  "then press Enter here to save the sign-in... ")
            ctx.close()
        log(f"Sign-in saved in {profile_dir} (git-ignored). Now add --composer-live to your recording command.")
        return
    if args.composer_live and not profile_dir.exists():
        fail("--composer-live needs a saved sign-in. Run: python demo_video/record_demo.py --login-composer")

    work = Path(args.work)
    (work / "audio").mkdir(parents=True, exist_ok=True)
    (work / "clips").mkdir(parents=True, exist_ok=True)
    (work / "segments").mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    images_dir = REPO / S.IMAGES_DIR

    scenes = [sc for sc in S.SCENES if not args.only or sc["id"] in args.only]
    footnote = {"files": "Automated screen recording · narrated by the team",
                "none": "Automated screen recording · captions only"}.get(args.tts)
    if footnote:
        scenes = [dict(sc, footnote=footnote) if sc.get("footnote") else sc for sc in scenes]
    if not scenes:
        fail("no scenes selected; see --list")

    pre = preflight(args, work)
    facts, terminal = pre["facts"], pre["terminal"]

    # ---- narration --------------------------------------------------------
    log(f"Generating narration ({args.tts})")
    plan = []
    for sc in scenes:
        text = fill(script_for(sc, args), facts, sc["id"])
        if args.tts == "files":
            audio, dur, cues = human_scene_audio(sc["id"], text, work)
        else:
            audio, dur, cues = narrate_scene(text, work / "audio" / sc["id"], args)
        plan.append({"scene": sc, "text": text, "audio": audio, "audio_dur": dur, "cues": cues,
                     "target": LEAD_IN + dur + TAIL})
        log(f"    {sc['id']:22s} {dur:5.1f}s")

    # ---- recording --------------------------------------------------------
    report = {"facts": facts, "scenes": []}
    log("Recording scenes")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)

        def factory(live_composer: bool = False):
            opts = dict(viewport=VIEWPORT, record_video_dir=str(work / "raw"), record_video_size=VIEWPORT,
                        device_scale_factor=1, color_scheme="light")
            if live_composer:
                return launch_signed_in(pw, profile_dir, headless=not args.headed, **opts)
            return browser.new_context(**opts)

        for item in plan:
            sc = item["scene"]
            log(f"  ● {sc['id']}")
            clip, offset, visible = record_scene(factory, sc, item["target"], {}, args, images_dir,
                                                 work / "clips", terminal, report)
            item.update(clip=clip, lead=offset, visible=visible)
        browser.close()

    # ---- assembly ---------------------------------------------------------
    log("Assembling video")
    segments, srt, t = [], [], 0.0
    for i, item in enumerate(plan):
        seg = work / "segments" / f"{i:02d}_{item['scene']['id']}.mp4"
        # Map wall-clock time onto the recording. The browser's video clock can run a little
        # fast or slow under load, so scale by (recorded length / real elapsed time).
        wall = item["lead"] + item["visible"]
        speed = min(2.0, max(0.5, media_duration(item["clip"]) / wall)) if wall > 0 else 1.0
        seg_dur = max(item["visible"], item["target"])
        build_segment(item["clip"], item["lead"] * speed, item["visible"] * speed, speed, seg_dur,
                      item["audio"], seg)
        segments.append(seg)
        srt.extend((t + LEAD_IN + a, t + LEAD_IN + b, cap) for a, b, cap in item["cues"])
        report["scenes"].append({"id": item["scene"]["id"], "start": round(t, 2), "duration": round(seg_dur, 2),
                                 "narration": item["text"]})
        t += seg_dur

    listing = work / "segments.txt"
    listing.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segments), encoding="utf-8")
    joined = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(joined)], check=True)

    srt_path = out_path.with_suffix(".srt")
    srt_path.write_text("\n".join(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n"
                                  for n, (a, b, txt) in enumerate(srt, 1)), encoding="utf-8")
    finalize(joined, srt, srt_path, out_path, args.burn_subtitles, work)

    report["total_seconds"] = round(t, 1)
    report_path = out_path.with_name(out_path.stem + "_report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))

    if not args.keep_work:
        clean(quiet=True)  # automatic tidy-up: temporary clips/audio and caches; finished files are kept
    mismatched = {p: s for p, s in report.get("swagger_status", {}).items() if s != "200"}
    log(f"Done: {out_path}  ({t / 60:.1f} min)")
    log(f"Captions:  embedded CC track{' + burned in' if args.burn_subtitles else ''}; "
        f"also saved as {srt_path}")
    log(f"Report:    {report_path}")
    if mismatched:
        log(f"WARNING: Swagger showed non-200 responses: {mismatched} — review before submitting.")


if __name__ == "__main__":
    main()
