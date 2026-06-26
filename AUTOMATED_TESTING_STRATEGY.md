# Automated Testing Strategy for the Kanban Simulator

## 1. Purpose of the Automated Testing Strategy

This project is a web-based Kanban simulator with a Flask backend and a plain HTML, CSS, and JavaScript frontend. The goal of the automated testing strategy is not only to check that individual files work, but to verify that the simulator behaves correctly as a complete application.

The testing strategy focuses on meaningful workflow-based coverage. This means the tests are selected based on important user actions and project risks, such as starting the simulation, displaying tasks, updating metrics, resetting state, changing configuration, and exporting simulation data.

The implemented test strategy covers:

- backend API behavior
- core Kanban simulation logic
- frontend browser behavior
- frontend/backend integration
- reset and stale-state regression risks
- CSV export correctness
- configuration behavior
- continuous integration through GitHub Actions

This makes the test suite suitable for the project title:

> Frontend Development and Automated Testing for a Web-Based Kanban Simulator

## 2. Current Technology Stack

The project currently uses:

- Flask for the backend web server
- Flask-CORS for frontend/backend communication support
- plain HTML, CSS, and JavaScript for the frontend
- pytest for Python backend and simulation tests
- Playwright for browser-based frontend end-to-end tests
- GitHub Actions for automated CI test execution

No React, Vue, Angular, Jest, Vitest, Cypress, Docker test containers, or database testing tools are currently required because the project does not use those technologies.

## 3. Main Testing Philosophy

The testing approach is layered. Each layer checks the application from a different angle.

The project uses:

- unit tests for internal Kanban logic
- API tests for Flask endpoints
- export tests for CSV output
- end-to-end tests for browser workflows
- integration tests for frontend/backend communication
- regression tests for previously discovered bugs
- static validation for frontend JavaScript syntax
- CI automation so tests run automatically

This is better than only chasing high line coverage, because a simulator can have high code coverage and still fail during real user interaction. The more important goal is to test the flows that users and evaluators actually care about.

## 4. Unit Testing

Unit tests check small pieces of internal logic directly.

Implemented in:

- `TESTS/test_kanban.py`

These tests directly call functions from `Backend/Kanban.py`.

Examples of tested functions:

- `generate_columns()`
- `generate_task()`
- `process_tasks()`
- `tick_manager()`
- `update_config()`

Current unit test coverage includes:

- columns are generated correctly
- first and last columns do not process tasks
- the clock moves from end of day to the next day
- tasks are created in the backlog
- backlog WIP limit is respected
- tasks can move from backlog into the next workflow column
- completed tasks move into the Done column
- WIP limits and worker counts can be loaded from config

This is a white-box testing layer because the tests know and directly call internal functions.

Why this matters:

The Kanban simulator depends on internal simulation rules. If task creation, task movement, or time progression breaks, the frontend may still load but the simulation result becomes wrong.

## 5. Backend API Testing

Backend API tests check the Flask routes and backend service layer.

Implemented in:

- `TESTS/test_app.py`
- `TESTS/test_api_service.py`

These tests check the backend through route handlers and service functions.

Current backend API coverage includes:

- `/board` returns JSON board state
- `/clock-and-day` returns clock and day information
- `/update-config` accepts valid configuration data
- `/update-config` rejects missing JSON with a clear error
- `/stop` resets the board state
- metrics return predictable values after reset
- stopping the simulation is safe even when it is not actively running

This is mainly grey-box testing. The tests interact with public backend behavior, but they also know the expected response fields and state structure.

Why this matters:

The frontend depends on predictable backend responses. If the backend returns missing fields, invalid JSON, or stale values, the frontend can display wrong information or crash.

## 6. Simulation State Reset Testing

Reset behavior is tested separately because it is critical for a simulator.

Implemented in:

- `TESTS/test_api_service.py`
- `TESTS/test_frontend_e2e.py`

The reset-related tests verify that stopping/resetting the simulation clears:

- visible task cards
- hidden completed/archive tasks
- completed task count
- average cycle time
- average lead time
- throughput
- total WIP
- clock
- day
- tick counter
- task ID counter

Why this matters:

A simulator must be repeatable. If old data remains after reset, the next simulation run is contaminated by the previous run. That would make metrics, exported data, and demonstrations unreliable.

This is also regression testing because reset/stale-state behavior was already a real issue during development.

## 7. Regression Testing

Regression tests protect against bugs that were already discovered before.

Implemented in:

- `TESTS/test_api_service.py`
- `TESTS/test_export_service.py`
- `TESTS/test_frontend_e2e.py`

Regression risks currently covered:

- reset not clearing the backend state
- reset not clearing visible frontend cards
- hidden completed/archive tasks causing confusing data
- metrics showing stale values after reset
- frontend showing stale cards when backend requests fail
- speed slider using the wrong direction
- CSV export becoming unreadable or inconsistent

Why this matters:

Regression tests turn real development problems into permanent checks. When future changes are made, these tests help prevent old bugs from returning.

Good report wording:

> Regression tests were added for previously observed issues such as reset behavior, stale frontend state, speed configuration, and CSV export readability.

## 8. Frontend Smoke Testing

Smoke tests check that the application loads and the most important interface elements are visible.

Implemented in:

- `TESTS/test_frontend_e2e.py`

Specific test:

- `test_smoke_page_loads_core_kanban_ui`

This test opens the real application in a browser and checks:

- the main title is visible
- Start button exists
- Pause button exists
- Stop(Hold) button exists
- Update Configuration button exists
- Export CSV button exists
- all Kanban columns are visible:
  - Backlog
  - Analysis
  - Development
  - Review
  - Testing
  - Done
- the metrics panel exists
- the app starts without existing task cards

Why this matters:

Smoke tests catch obvious UI breakages early. If a button ID changes, a column disappears, or the page fails to load, the test fails immediately.

## 9. End-to-End Browser Testing

End-to-end tests simulate real user behavior in a real browser.

Implemented in:

- `TESTS/test_frontend_e2e.py`

Tool:

- Playwright

Current browser workflows tested:

- open the simulator
- click Start
- wait for task cards to appear
- check that metrics exist
- click Pause
- hold Stop(Hold) long enough to reset
- verify the board clears
- verify clock and day reset
- verify completed tasks reset
- verify total WIP resets
- click Export CSV
- verify a CSV file downloads

This is black-box testing because the test interacts with the visible user interface and does not depend on the internal implementation of `Kanban.py`.

Why this matters:

The project title emphasizes frontend development and automated testing. Playwright tests are especially relevant because they test the user-facing application in the browser, not only backend functions.

Good report wording:

> Playwright end-to-end tests validate the simulator from the user perspective by interacting with the browser interface and checking visible results.

## 10. Frontend and Backend Integration Testing

The Playwright tests also act as integration tests.

They verify the full data flow:

1. user clicks a frontend button
2. frontend JavaScript sends an API request
3. Flask backend receives the request
4. simulation state changes
5. frontend polls updated backend data
6. browser UI updates

Example:

1. User clicks Start.
2. Frontend calls `/start`.
3. Backend starts the simulation.
4. Frontend polls `/board`.
5. Task cards appear in the Kanban board.

Why this matters:

The frontend can look correct by itself and the backend can pass API tests by itself, but the real application only works if both sides communicate correctly.

## 11. Configuration Testing

Configuration tests verify that user-controlled simulator settings work correctly.

Implemented in:

- `TESTS/test_app.py`
- `TESTS/test_kanban.py`
- `TESTS/test_frontend_e2e.py`

Covered configuration areas:

- WIP limits
- worker counts
- update configuration endpoint
- missing JSON validation
- speed slider mapping

The frontend speed slider is tested because the user-facing meaning is different from the backend value.

Frontend meaning:

- `0.1x` means slowest
- `2.0x` means fastest

Backend meaning:

- larger tick interval means slower
- smaller tick interval means faster

Therefore:

- frontend `0.1x` maps to backend tick interval `2.0`
- frontend `2.0x` maps to backend tick interval `0.1`

Why this matters:

Configuration directly affects simulation behavior. If speed, workers, or WIP limits are wrong, the simulation output becomes misleading.

## 12. CSV Export Testing

CSV export tests verify that generated simulation data can be used for analysis.

Implemented in:

- `TESTS/test_export_service.py`
- `TESTS/test_frontend_e2e.py`

The tests check:

- CSV generation works
- the CSV route returns a downloadable file
- the browser Export CSV button downloads a file
- the filename is `kanban_simulation_export.csv`
- CSV output starts with `sep=;` for Excel compatibility
- task ID is exported
- task name is exported
- task processing state is exported
- task location is exported
- worker assignment is exported
- created and completed times are exported
- cycle time is exported
- lead time is exported
- current column number and name are exported
- archived completed tasks are labeled as `Completed Archive`

Why this matters:

The project is intended as a simulation. Therefore, the exported data is part of the value of the application. If the export is unreadable or inconsistent, users cannot analyze cycle time, lead time, throughput, WIP, or bottlenecks properly.

## 13. Stale UI and Failure-State Testing

The frontend includes a test for stale UI behavior.

Implemented in:

- `TESTS/test_frontend_e2e.py`

Specific test:

- `test_frontend_clears_stale_board_when_backend_requests_fail`

What it does:

1. Opens the simulator.
2. Inserts a fake stale task card into the board.
3. Blocks the `/board` backend request.
4. Calls the frontend board-fetching function.
5. Verifies that the old task card is cleared.

Why this matters:

If the backend is stopped or unavailable, the frontend should not continue showing old task cards as if the simulation is still running. This improves trust in the UI.

This is a meaningful frontend reliability test, not just a simple button visibility check.

## 14. Static Frontend Validation

The CI pipeline runs a JavaScript syntax check.

Implemented in:

- `.github/workflows/daily-tests.yml`

Command:

```bash
node --check Frontend/script.js
```

What it catches:

- syntax errors
- missing brackets
- invalid JavaScript structure

Why this matters:

This catches simple frontend mistakes before browser tests run.

## 15. Continuous Integration with GitHub Actions

The project uses GitHub Actions for CI automation.

Implemented in:

- `.github/workflows/daily-tests.yml`

The workflow runs on:

- push
- pull request
- daily schedule
- manual trigger

The CI workflow performs:

1. checkout repository
2. install Python
3. install dependencies from `requirements.txt`
4. install Playwright Chromium
5. run JavaScript syntax check
6. run all pytest tests

Why this matters:

The test suite is no longer only manual. GitHub automatically checks whether changes break the project. This is important for group work because code changes can be validated before or during merging.

Good report wording:

> GitHub Actions is used as a continuous integration pipeline to automatically execute backend tests, export tests, frontend syntax validation, regression tests, and Playwright browser tests.

## 16. Test Isolation

The test suite uses a pytest fixture to reset shared state.

Implemented in:

- `TESTS/conftest.py`

The fixture resets:

- Kanban running state
- start and pause events
- tick interval
- clock
- day
- task ID counter
- board object
- simulation thread reference

It also restores:

- `Backend/config.json`
- `Backend/export.json`

Why this matters:

The simulator uses global state. Without test isolation, one test could affect another test. This would make test results unreliable.

## 17. How to Run the Tests Manually

Install dependencies:

```powershell
pip install -r requirements.txt
```

Install the browser used by Playwright:

```powershell
python -m playwright install chromium
```

Run all tests:

```powershell
python -m pytest TESTS -v
```

Run only backend/export/unit tests without browser tests:

```powershell
python -m pytest TESTS -v -m "not e2e"
```

Run only browser end-to-end tests:

```powershell
python -m pytest TESTS/test_frontend_e2e.py -v
```

Check frontend JavaScript syntax:

```powershell
node --check Frontend/script.js
```

## 18. What Meaningful Coverage Means in This Project

Meaningful coverage does not mean testing every line of CSS or every visual detail.

Meaningful coverage means testing the behavior that would make the simulator fail if broken.

The current test suite focuses on:

- can the app load?
- are the workflow columns visible?
- can the simulation start?
- do task cards appear?
- can the simulation pause?
- can the simulation reset?
- does reset fully clear state?
- do metrics reset correctly?
- does the speed slider map correctly?
- does CSV export work?
- is exported data readable?
- does the frontend clear stale data?
- does CI run the tests automatically?

This is why the strategy is workflow-based rather than purely line-coverage-based.

## 19. Limitations of the Current Test Strategy

The current test suite is meaningful, but it is not perfect.

Current limitations:

- visual styling is not deeply tested
- exact animations are not tested
- browser tests currently use Chromium only
- no performance/load testing exists
- no mutation testing exists
- no accessibility audit is currently automated
- no Dockerized test environment exists
- no real deployment/CD pipeline exists

These are acceptable limitations for the current Praxisprojekt scope.

## 20. Possible Future Improvements

Future improvements could include:

- accessibility testing with axe-core
- cross-browser Playwright tests for Firefox and WebKit
- visual regression screenshots
- mutation testing for backend metrics/export logic
- stronger validation tests for invalid configuration values
- performance checks for long simulation runs
- deployment pipeline if the app is hosted online
- test coverage reporting

These are future extensions, not required before the current test strategy is considered useful.

## 21. Short Report Summary

The automated testing strategy combines unit tests, backend API tests, CSV export tests, frontend end-to-end tests, regression tests, configuration tests, state reset tests, and CI automation. Unit tests verify the internal Kanban simulation logic, API tests validate Flask endpoints, and Playwright tests check real browser workflows from the user perspective. Regression tests protect against previously observed issues such as stale UI state, reset problems, speed configuration mistakes, and export readability problems. GitHub Actions runs the test suite automatically on code changes and scheduled executions. This provides meaningful workflow-based coverage for the web-based Kanban simulator.

