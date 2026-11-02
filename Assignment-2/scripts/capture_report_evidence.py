#!/usr/bin/env python3
"""Refresh the report's application and API screenshots from a live run.

Start the configured API and React app first. Screenshots are staged and replace
the report evidence only after every request and browser check succeeds.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "report" / "evidence"
REPORT = ROOT / "docs" / "report" / "report.md"
ANALYSIS_MESSAGE = (
    "My diabetes education appointment conflicts with work. Move it to Friday "
    "after 2 pm; check availability. The new booking is unconfirmed."
)
SYMPTOMS_QUESTION = "What symptoms might someone with diabetes experience?"
MEDICATION_QUESTION = "Should I change my diabetes medication?"

CAPTURED_IMAGES = {
    "swagger-analyze.png",
    "02-request-analysis.png",
    "swagger-retrieve.png",
    "swagger-chat.png",
    "03-source-grounded-answer.png",
    "04-staff-referral.png",
}


def json_request(url: str) -> tuple[int, object]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"Cannot reach {url}: {error}") from error


def verify_services(api_url: str, app_url: str) -> None:
    status, health = json_request(f"{api_url}/health")
    if status != 200:
        raise RuntimeError(f"API health check returned HTTP {status}.")
    status, metadata = json_request(f"{api_url}/metadata")
    if status != 200 or not isinstance(metadata, dict):
        raise RuntimeError(f"API metadata check returned HTTP {status}.")
    not_ready = [
        name
        for name in ("classifier", "summarizer", "knowledge_index")
        if not isinstance(metadata.get(name), dict)
        or metadata[name].get("ready") is not True
    ]
    if not_ready:
        raise RuntimeError("Required components are not ready: " + ", ".join(not_ready))
    request = urllib.request.Request(app_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"React app returned HTTP {response.status}.")
    except urllib.error.URLError as error:
        raise RuntimeError(f"Cannot reach React app at {app_url}: {error}") from error


def open_operation(page: Page, path: str):
    method = "GET" if path in {"/health", "/metadata"} else "POST"
    summary = page.get_by_role("button", name=f"{method} {path}")
    operation = summary.locator(
        "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), "
        "' opblock ')][1]"
    )
    expect(operation).to_be_visible(timeout=15_000)
    if "is-open" not in (operation.get_attribute("class") or ""):
        operation.locator(".opblock-summary").click()
    return operation


def capture_swagger(
    page: Page, path: str, body: dict | None, marker: str, target: Path
):
    operation = open_operation(page, path)
    if body is not None:
        operation.get_by_role("button", name="Try it out").click()
        editor = operation.locator("textarea.body-param__text")
        editor.fill(json.dumps(body, indent=2))
    editor.evaluate("element => element.setAttribute('wrap', 'soft')")
    execute = operation.get_by_role("button", name="Execute")
    execute.click()
    expect(execute).to_be_enabled(timeout=180_000)
    response = operation.locator(".live-responses-table tr.response")
    expect(response).to_be_visible(timeout=10_000)
    status = (
        response.locator(".response-col_status")
        .first.inner_text(timeout=180_000)
        .strip()
    )
    if status != "200":
        body_text = response.locator(".response-col_description").inner_text()
        raise RuntimeError(f"Swagger {path} returned HTTP {status}: {body_text[:500]}")
    expect(response).to_contain_text(marker, timeout=180_000)
    operation.locator(
        ".responses-inner .responses-table:not(.live-responses-table)"
    ).evaluate_all("tables => tables.forEach(table => table.remove())")
    operation.locator(".curl-command").evaluate_all(
        "blocks => blocks.forEach(block => block.remove())"
    )
    page.add_style_tag(
        content=(
            ".body-param__text { height: 120px !important; "
            "min-height: 120px !important; }"
            ".live-responses-table *, .body-param__text { "
            "white-space: pre-wrap !important; overflow-wrap: anywhere !important; }"
        )
    )
    operation.screenshot(path=str(target), animations="disabled")


def capture_analysis(page: Page, app_url: str, target: Path) -> None:
    page.goto(app_url, wait_until="networkidle")
    expect(page.get_by_role("heading", name="Diabetes support")).to_be_visible()
    page.get_by_role("textbox", name="Incoming message").fill(ANALYSIS_MESSAGE)
    page.get_by_role("button", name="Analyze request").click()
    result = page.locator(".analysis-result")
    expect(result).to_be_visible(timeout=180_000)
    expect(result).not_to_contain_text("Unable to connect")
    expect(page.locator(".error-message")).to_have_count(0)
    if "confirm" not in result.inner_text().lower():
        raise RuntimeError(
            "The current appointment summary no longer mentions booking confirmation. "
            "Review the report wording before refreshing its screenshots."
        )
    page.locator(".support-panel").screenshot(path=str(target), animations="disabled")


def submit_question(page: Page, question: str) -> None:
    page.get_by_role("textbox", name="Ask a question").fill(question)
    page.get_by_role("button", name="Send question").click()
    expect(page.locator(".exchange .chat-entry--assistant")).to_be_visible(
        timeout=180_000
    )


def capture_grounded_answer(page: Page, app_url: str, target: Path) -> None:
    page.goto(app_url, wait_until="networkidle")
    submit_question(page, SYMPTOMS_QUESTION)
    answer = page.locator(".exchange .chat-entry--assistant")
    expect(answer).to_contain_text("symptoms")
    expect(answer.locator(".source-chip").first).to_be_visible()
    page.locator(".knowledge-panel").screenshot(path=str(target), animations="disabled")


def capture_referral(page: Page, app_url: str, target: Path) -> None:
    page.goto(app_url, wait_until="networkidle")
    submit_question(page, MEDICATION_QUESTION)
    answer = page.locator(".exchange .chat-entry--assistant")
    expect(answer).to_contain_text("contact your clinic team")
    expect(answer.locator(".source-chip")).to_have_count(0)
    page.locator(".knowledge-panel").screenshot(path=str(target), animations="disabled")


def verify_report_image_references(staged: Path) -> None:
    report = REPORT.read_text(encoding="utf-8")
    image_refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", report)
    missing = []
    for ref in image_refs:
        if ref.startswith(("http://", "https://", "data:")):
            continue
        path = (REPORT.parent / ref).resolve()
        if not path.exists() and not (staged / Path(ref).name).exists():
            missing.append(ref)
    if missing:
        raise RuntimeError("Report has missing embedded images: " + ", ".join(missing))
    json_links = re.findall(r"\[[^\]]+\]\([^)]*\.json(?:#[^)]*)?\)", report)
    if json_links:
        raise RuntimeError("Report still contains clickable JSON evidence links.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument("--app-url", default="http://127.0.0.1:5173")
    parser.add_argument("--browser-channel", default="chrome")
    args = parser.parse_args()
    api_url = args.api_url.rstrip("/")
    app_url = args.app_url.rstrip("/")

    verify_services(api_url, app_url)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="report-evidence-") as temp_dir:
        staged = Path(temp_dir)
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel=args.browser_channel)
            except Exception as error:
                raise RuntimeError(
                    f"Could not launch browser channel {args.browser_channel!r}. "
                    "Install Chrome or pass --browser-channel chromium after "
                    "installing "
                    "Playwright Chromium."
                ) from error
            try:
                page = browser.new_page(
                    viewport={"width": 1600, "height": 1000}, device_scale_factor=1
                )
                page.goto(f"{api_url}/docs", wait_until="networkidle")
                expect(page.locator(".swagger-ui")).to_be_visible(timeout=20_000)
                capture_swagger(
                    page,
                    "/analyze",
                    {"message": ANALYSIS_MESSAGE},
                    "appointment_support",
                    staged / "swagger-analyze.png",
                )
                capture_swagger(
                    page,
                    "/retrieve",
                    {"question": SYMPTOMS_QUESTION},
                    "WHO01-003",
                    staged / "swagger-retrieve.png",
                )
                capture_swagger(
                    page,
                    "/chat",
                    {"question": MEDICATION_QUESTION},
                    "contact your clinic team",
                    staged / "swagger-chat.png",
                )
                page.set_viewport_size({"width": 1600, "height": 1100})
                capture_analysis(page, app_url, staged / "02-request-analysis.png")
                capture_grounded_answer(
                    page, app_url, staged / "03-source-grounded-answer.png"
                )
                capture_referral(page, app_url, staged / "04-staff-referral.png")
            finally:
                browser.close()

        if {path.name for path in staged.glob("*.png")} != CAPTURED_IMAGES:
            raise RuntimeError(
                "Screenshot capture set is incomplete; existing evidence kept."
            )
        verify_report_image_references(staged)
        for name in sorted(CAPTURED_IMAGES):
            shutil.copy2(staged / name, EVIDENCE / name)

    print(f"Refreshed {len(CAPTURED_IMAGES)} report screenshots in {EVIDENCE}")
    print("Report figure filenames stay stable; embedded images are updated in place.")


if __name__ == "__main__":
    main()
