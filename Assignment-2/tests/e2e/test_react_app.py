import os

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.mark.e2e
def test_react_frontend_shows_analysis_and_document_qa() -> None:
    app_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    browser_channel = os.getenv("PLAYWRIGHT_CHANNEL", "chrome")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=browser_channel)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(app_url, wait_until="domcontentloaded")

        expect(page.get_by_role("heading", name="Diabetes support desk")).to_be_visible(
            timeout=15_000
        )
        expect(
            page.get_by_role("textbox", name="Incoming support message")
        ).to_be_visible()
        expect(page.get_by_role("textbox", name="Question")).to_be_visible()
        expect(page.get_by_role("button", name="Analyze request")).to_be_visible()
        expect(page.get_by_role("button", name="Send question")).to_be_visible()

        browser.close()
