import csv
import io

import export_service
import app as flask_app


def _read_export_rows(csv_text):
    lines = csv_text.splitlines()
    if lines and lines[0] == "sep=;":
        lines = lines[1:]

    return list(csv.DictReader(io.StringIO("\n".join(lines)), delimiter=";"))


def test_generate_tasks_csv_contains_readable_task_rows():
    export_data = {
        "Time Elapsed": [
            {
                "Time [9am - 5pm]": "16.50",
                "Day": 2,
            }
        ],
        "Columns": [
            {"Column id": 0, "Column name": "Backlog", "Tasks amount": 2},
            {"Column id": 1, "Column name": "Analysis", "Tasks amount": 1},
            {"Column id": 2, "Column name": "Development", "Tasks amount": 0},
            {"Column id": 3, "Column name": "Review", "Tasks amount": 0},
            {"Column id": 4, "Column name": "Testing", "Tasks amount": 0},
            {"Column id": 5, "Column name": "Done", "Tasks amount": 1},
        ],
        "Tasks": [
            {
                "Task id": 1,
                "Task name": "Task 1",
                "Created at": "Day: 1, Time: 9.1",
                "Done at": "Day: 1, Time: 16.5",
                "Status": "Completed",
                "Worker task": 0,
                "Cycle time (Minutes)": 460,
                "Lead time (Minutes)": 460,
                "Current column": 5,
                "Column Cycle Time (Minutes) [Backlog, Column 1, Column 2, Column 3, Column 4]": [0, 110, 130, 110, 110],
                "Column Entry Time [Backlog, Column 1, Column 2, Column 3, Column 4]": ["9.10", "9.10"],
                "Column Exit Time [Backlog, Column 1, Column 2, Column 3, Column 4]": ["9.10", "11.00"],
            }
        ]
    }

    csv_text = export_service.generate_tasks_csv(export_data)
    rows = _read_export_rows(csv_text)

    assert csv_text.startswith("sep=;")
    assert rows[0]["simulation_day"] == "2"
    assert rows[0]["simulation_clock_time"] == "16:50"
    assert rows[0]["active_work_in_progress_count"] == "1"
    assert rows[0]["completed_task_count"] == "1"
    assert rows[0]["task_id"] == "1"
    assert rows[0]["task_name"] == "Task 1"
    assert rows[0]["task_processing_state"] == "Completed"
    assert rows[0]["task_location"] == "Visible Board"
    assert rows[0]["worker_assigned"] == "No"
    assert rows[0]["remaining_processing_units"] == ""
    assert rows[0]["created_day"] == "1"
    assert rows[0]["created_time"] == "09:10"
    assert rows[0]["completed_day"] == "1"
    assert rows[0]["completed_time"] == "16:50"
    assert rows[0]["cycle_time_minutes"] == "460"
    assert rows[0]["lead_time_minutes"] == "460"
    assert rows[0]["current_column_number"] == "5"
    assert rows[0]["current_column_name"] == "Done"
    assert rows[0]["backlog_cycle_time_minutes"] == "0"
    assert rows[0]["analysis_cycle_time_minutes"] == "110"
    assert rows[0]["backlog_entry_time"] == "09:10"
    assert rows[0]["analysis_exit_time"] == "11:00"


def test_generate_tasks_csv_returns_headers_when_no_tasks_exist():
    csv_text = export_service.generate_tasks_csv({"Tasks": []})

    assert csv_text.startswith("sep=;\r\nsimulation_day;simulation_clock_time")


def test_completed_tasks_are_exported_as_done_even_with_stale_current_column():
    export_data = {
        "Columns": [
            {"Column id": 0, "Column name": "Column 0", "Tasks amount": 0},
            {"Column id": 1, "Column name": "Column 1", "Tasks amount": 0},
            {"Column id": 2, "Column name": "Column 2", "Tasks amount": 0},
            {"Column id": 3, "Column name": "Column 3", "Tasks amount": 0},
            {"Column id": 4, "Column name": "Column 4", "Tasks amount": 0},
            {"Column id": 5, "Column name": "Column 5", "Tasks amount": 1},
        ],
        "Tasks": [
            {
                "Task id": 9,
                "Task name": "Task 9",
                "Status": "Completed",
                "Worker task": 0,
                "Current column": 4,
            }
        ],
    }

    rows = _read_export_rows(export_service.generate_tasks_csv(export_data))

    assert rows[0]["task_processing_state"] == "Completed"
    assert rows[0]["task_location"] == "Visible Board"
    assert rows[0]["current_column_number"] == "5"
    assert rows[0]["current_column_name"] == "Done"


def test_archived_completed_tasks_are_labeled_as_completed_archive():
    export_data = {
        "Columns": [
            {"Column id": 0, "Column name": "Column 0", "Tasks amount": 0},
            {"Column id": 1, "Column name": "Column 1", "Tasks amount": 0},
            {"Column id": 2, "Column name": "Column 2", "Tasks amount": 0},
            {"Column id": 3, "Column name": "Column 3", "Tasks amount": 0},
            {"Column id": 4, "Column name": "Column 4", "Tasks amount": 0},
            {"Column id": 5, "Column name": "Column 5", "Tasks amount": 5},
        ],
        "Tasks": [
            {
                "Task id": 1,
                "Task name": "Task 1",
                "Status": "Completed",
                "Task location": "Completed Archive",
                "Worker task": 0,
                "Current column": 4,
            },
            {
                "Task id": 2,
                "Task name": "Task 2",
                "Status": "Completed",
                "Task location": "Visible Board",
                "Worker task": 0,
                "Current column": 4,
            },
        ],
    }

    rows = _read_export_rows(export_service.generate_tasks_csv(export_data))

    assert rows[0]["task_location"] == "Completed Archive"
    assert rows[0]["current_column_number"] == ""
    assert rows[0]["current_column_name"] == "Completed Archive"
    assert rows[1]["task_location"] == "Visible Board"
    assert rows[1]["current_column_number"] == "5"
    assert rows[1]["current_column_name"] == "Done"


def test_export_csv_route_downloads_csv_file(tmp_path, monkeypatch):
    export_path = tmp_path / "export.json"
    export_path.write_text(
        '{"Tasks": [{"Task id": 7, "Task name": "Task 7", "Status": "Completed"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(export_service, "EXPORT_JSON_PATH", export_path)

    client = flask_app.app.test_client()
    response = client.get("/export/csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment; filename=kanban_simulation_export.csv" in response.headers["Content-Disposition"]
    assert "Task 7" in response.get_data(as_text=True)
