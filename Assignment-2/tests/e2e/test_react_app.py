import json
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

        page.route(
            "**/api/analyze",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "classification": {
                            "category": "appointment_support",
                            "valid_category": True,
                        },
                        "summary": (
                            "Requests a Friday appointment change and help finding "
                            "the education leaflet."
                        ),
                    }
                ),
            ),
        )
        urgent_response = (
            "This may need urgent medical attention. Contact local emergency services "
            "or follow your clinic’s urgent-care instructions now."
        )

        def mock_chat(route) -> None:
            question = json.loads(route.request.post_data or "{}").get("question")
            if question == "My father is unconscious, what is the next step?":
                result = {
                    "answer": urgent_response,
                    "abstained": True,
                    "sources": [],
                }
            else:
                result = {
                    "answer": (
                        "The WHO says possible symptoms include frequent "
                        "urination and blurred vision."
                    ),
                    "abstained": False,
                    "sources": [
                        {
                            "chunk_id": "WHO01-003",
                            "source_title": "Diabetes: Questions and Answers",
                            "source_url": (
                                "https://www.who.int/news-room/questions-and-answers/item/diabetes"
                            ),
                            "section": "Common symptoms",
                            "text": (
                                "Possible symptoms include frequent urination "
                                "and blurred vision."
                            ),
                            "score": 0.81,
                        }
                    ],
                }
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(result),
            )

        page.route("**/api/chat", mock_chat)
        page.goto(app_url, wait_until="domcontentloaded")

        expect(page.get_by_role("heading", name="Diabetes support")).to_be_visible(
            timeout=15_000
        )
        expect(
            page.get_by_role("textbox", name="Incoming message")
        ).to_be_visible()
        expect(page.get_by_role("textbox", name="Ask a question")).to_be_visible()
        expect(page.get_by_role("button", name="Analyze request")).to_be_visible()
        expect(page.get_by_role("button", name="Send question")).to_be_visible()

        page.get_by_role("textbox", name="Incoming message").fill(
            "Please move my appointment to Friday and help me find "
            "the education leaflet."
        )
        page.get_by_role("button", name="Analyze request").click()
        expect(page.get_by_text("appointment support", exact=True)).to_be_visible()
        expect(
            page.get_by_text(
                "Requests a Friday appointment change and help finding "
                "the education leaflet.",
                exact=True,
            )
        ).to_be_visible()

        page.get_by_role("textbox", name="Ask a question").fill(
            "What symptoms does the source list?"
        )
        page.get_by_role("button", name="Send question").click()
        expect(
            page.get_by_text(
                "The WHO says possible symptoms include frequent urination "
                "and blurred vision.",
                exact=True,
            )
        ).to_be_visible()
        page.get_by_role("button", name="Common symptoms").click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(
            page.get_by_text(
                "Possible symptoms include frequent urination and blurred vision.",
                exact=True,
            )
        ).to_be_visible()
        page.get_by_role("button", name="Close source").click()

        page.get_by_role("textbox", name="Ask a question").fill(
            "My father is unconscious, what is the next step?"
        )
        page.get_by_role("button", name="Send question").click()
        expect(page.get_by_text("Staff referral", exact=True)).to_be_visible()
        expect(page.get_by_text(urgent_response, exact=True)).to_be_visible()

        browser.close()
