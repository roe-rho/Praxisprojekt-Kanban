import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "Backend"
CONFIG_PATH = BACKEND_DIR / "config.json"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(base_url, timeout=30):
    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base_url, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            time.sleep(0.25)

    raise RuntimeError(f"Flask test server did not start in time: {last_error}")


@pytest.fixture(scope="session")
def flask_server():
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    server_code = f"""
import sys
sys.path.insert(0, r"{BACKEND_DIR}")
import Kanban as KB
from app import app

KB.num_columns = 6
KB.generate_columns(KB.num_columns)
app.run(debug=False, use_reloader=False, host="127.0.0.1", port={port})
"""

    process = subprocess.Popen(
        [sys.executable, "-c", server_code],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_server(base_url)
        yield base_url
    finally:
        try:
            urllib.request.urlopen(
                urllib.request.Request(f"{base_url}/stop", data=b"{}", method="POST"),
                timeout=2,
            )
        except Exception:
            pass

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture()
def page(flask_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def _task_card_count(page):
    return page.locator("#kanban-board .cards > .card").count()


@pytest.mark.e2e
def test_smoke_page_loads_core_kanban_ui(page, flask_server):
    page.goto(flask_server)

    assert page.locator("h1").inner_text() == "Kanban Simulator"
    for button_name in ["Start", "Pause", "Stop(Hold)", "Update Configuration", "Export CSV"]:
        assert page.get_by_role("button", name=button_name).is_visible()

    for column_name in ["Backlog", "Analysis", "Development", "Review", "Testing", "Done"]:
        assert page.locator("#kanban-board h2", has_text=column_name).is_visible()

    assert page.locator("#metrics").is_visible()
    assert _task_card_count(page) == 0


@pytest.mark.e2e
def test_configuration_speed_slider_sends_professional_speed_mapping(page, flask_server):
    page.goto(flask_server)

    page.locator("#speed").evaluate(
        """speed => {
            speed.value = "0.1";
            speed.dispatchEvent(new Event("input", { bubbles: true }));
        }"""
    )
    with page.expect_response("**/update-config") as response_info:
        page.get_by_role("button", name="Update Configuration").click()
    assert response_info.value.ok
    assert json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["tick_interval"] == "2.0"
    assert page.locator("#speed-value").text_content() == "0.1x"

    page.locator("#speed").evaluate(
        """speed => {
            speed.value = "2.0";
            speed.dispatchEvent(new Event("input", { bubbles: true }));
        }"""
    )
    with page.expect_response("**/update-config") as response_info:
        page.get_by_role("button", name="Update Configuration").click()
    assert response_info.value.ok
    assert json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["tick_interval"] == "0.1"
    assert page.locator("#speed-value").text_content() == "2.0x"


@pytest.mark.e2e
def test_start_pause_and_hold_stop_reset_user_workflow(page, flask_server):
    page.goto(flask_server)

    page.get_by_role("button", name="Start").click()
    page.wait_for_function(
        "document.querySelectorAll('#kanban-board .cards > .card').length > 0",
        timeout=10000,
    )
    assert "Total WIP:" in page.locator("#total-wip").inner_text()

    page.get_by_role("button", name="Pause").click()
    page.wait_for_timeout(500)

    stop_button = page.get_by_role("button", name="Stop(Hold)")
    box = stop_button.bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(3200)
    page.mouse.up()

    page.wait_for_function(
        "document.querySelectorAll('#kanban-board .cards > .card').length === 0",
        timeout=10000,
    )
    assert page.locator("#clock").inner_text() == "Clock: 9.00"
    assert page.locator("#day").inner_text() == "Day: 1"
    assert page.locator("#completed-tasks").inner_text() == "Completed Tasks: 0"
    assert page.locator("#total-wip").inner_text() == "Total WIP: 0"


@pytest.mark.e2e
def test_frontend_clears_stale_board_when_backend_requests_fail(page, flask_server):
    page.goto(flask_server)
    page.evaluate(
        """() => {
            const card = document.createElement("div");
            card.className = "card";
            card.textContent = "Stale Task";
            document.querySelector("#col-backlog .cards").appendChild(card);
        }"""
    )
    assert _task_card_count(page) == 1

    page.route("**/board", lambda route: route.abort())
    page.evaluate("fetchBoardState()")
    page.wait_for_function(
        "document.querySelectorAll('#kanban-board .cards > .card').length === 0",
        timeout=5000,
    )


@pytest.mark.e2e
def test_export_button_downloads_readable_csv(page, flask_server):
    page.goto(flask_server)

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Export CSV").click()

    download = download_info.value
    assert download.suggested_filename == "kanban_simulation_export.csv"

    csv_path = download.path()
    if csv_path is None:
        raise PlaywrightError("Downloaded CSV path was not available.")

    csv_text = Path(csv_path).read_text(encoding="utf-8")
    assert csv_text.startswith("sep=;")
    assert "task_id;task_name;task_processing_state;task_location" in csv_text
