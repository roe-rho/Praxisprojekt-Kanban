import json
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright is required for frontend browser tests.")
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_INDEX = PROJECT_ROOT / "Frontend" / "index.html"


@pytest.fixture
def page():
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except PlaywrightError as exc:
            pytest.skip(f"Playwright Chromium browser is not installed: {exc}")

        page = browser.new_page()
        yield page
        browser.close()


@pytest.fixture
def api_calls(page):
    calls = []
    board_payload = {
        "column_0": [
            {
                "id": 1,
                "created_at": "Day: 1, Time: 9.0",
                "status": None,
                "worker_task": 0,
                "progress_percent": 0,
            }
        ],
        "column_1": [],
        "column_2": [],
        "column_3": [],
        "column_4": [],
        "column_5": [],
        "_metrics": {"completed_tasks": 0},
    }

    def handle_api(route):
        request = route.request
        calls.append((request.method, request.url))

        if request.url.endswith("/board"):
            route.fulfill(status=200, content_type="application/json", body=json.dumps(board_payload))
            return

        if request.url.endswith("/clock-and-day"):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"clock": 9.1, "day": 1}))
            return

        if request.url.endswith("/update-config"):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"status": "Config updated successfully"}))
            return

        if request.url.endswith(("/start", "/stop", "/reset")):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"status": "ok"}))
            return

        route.fulfill(status=404, content_type="application/json", body=json.dumps({"error": "unknown endpoint"}))

    page.route("http://localhost:5000/**", handle_api)
    return calls


def open_frontend(page):
    page.goto(FRONTEND_INDEX.as_uri(), wait_until="domcontentloaded")


def test_intro_screen_is_visible_before_simulator(api_calls, page):
    open_frontend(page)

    expect(page.locator("#intro-screen")).to_be_visible()
    expect(page.locator("#simulator-screen")).to_be_hidden()
    expect(page.locator("#kanban-board")).to_be_hidden()

    page.locator("#intro-start-btn").click()

    expect(page.locator("#intro-screen")).to_be_hidden()
    expect(page.locator("#simulator-screen")).to_be_visible()
    expect(page.locator("#kanban-board")).to_be_visible()


def test_static_learning_board_has_dummy_cards_and_tooltips(api_calls, page):
    open_frontend(page)

    expect(page.locator(".learning-board")).to_be_visible()
    expect(page.locator(".learning-column")).to_have_count(6)
    expect(page.locator(".dummy-card")).to_have_count(8)
    expect(page.locator("#intro-screen [data-bs-toggle='tooltip']")).to_have_count(16)
    expect(page.locator(".learning-board[data-bs-toggle='tooltip']")).to_be_visible()
    expect(page.locator(".dummy-card[data-bs-toggle='tooltip']").first).to_be_visible()
    expect(page.locator(".dummy-progress[data-bs-toggle='tooltip']").first).to_be_visible()


def test_real_simulator_keeps_tooltips_only_on_main_controls(api_calls, page):
    open_frontend(page)
    page.locator("#intro-start-btn").click()

    expect(page.locator(".kanban-column")).to_have_count(6)
    expect(page.locator(".kanban-column[data-bs-toggle='tooltip']")).to_have_count(0)
    expect(page.locator("#column_0[data-bs-toggle='tooltip']")).to_have_count(0)
    expect(page.locator("#workers_1[data-bs-toggle='tooltip']")).to_have_count(0)
    expect(page.locator("#metrics[data-bs-toggle='tooltip']")).to_have_count(0)
    expect(page.locator("#start-btn[data-bs-toggle='tooltip']")).to_be_visible()
    expect(page.locator("#stop-btn[data-bs-toggle='tooltip']")).to_be_visible()
    expect(page.locator("#reset-btn[data-bs-toggle='tooltip']")).to_be_visible()
    expect(page.locator("#update-btn[data-bs-toggle='tooltip']")).to_be_visible()

    expect(page.locator(".task-card")).to_have_count(1)
    expect(page.locator(".task-card[data-bs-toggle='tooltip']")).to_have_count(0)
    expect(page.locator(".progress-track[data-bs-toggle='tooltip']")).to_have_count(0)


def test_simulator_buttons_still_call_existing_api_endpoints(api_calls, page):
    open_frontend(page)
    page.locator("#intro-start-btn").click()

    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#start-btn").click()
    expect(page.locator("#start-btn")).to_be_disabled()
    expect(page.locator("#stop-btn")).to_be_enabled()

    page.locator("#stop-btn").click()
    expect(page.locator("#start-btn")).to_be_enabled()
    expect(page.locator("#stop-btn")).to_be_disabled()

    page.locator("#reset-btn").dispatch_event("mousedown")
    page.wait_for_timeout(3100)
    page.locator("#reset-btn").dispatch_event("mouseup")

    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#update-btn").click()

    called_paths = {url.replace("http://localhost:5000", "") for _, url in api_calls}
    assert "/board" in called_paths
    assert "/start" in called_paths
    assert "/stop" in called_paths
    assert "/reset" in called_paths
    assert "/update-config" in called_paths

    post_paths = {url.replace("http://localhost:5000", "") for method, url in api_calls if method == "POST"}
    assert {"/start", "/stop", "/reset", "/update-config"}.issubset(post_paths)
