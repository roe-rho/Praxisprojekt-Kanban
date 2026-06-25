import csv
import io
import json
from pathlib import Path

from flask import Response


EXPORT_JSON_PATH = Path(__file__).with_name("export.json")
CSV_FILENAME = "kanban_simulation_export.csv"

# Friendly names used only for exported analysis files.
DEFAULT_COLUMN_DISPLAY_NAMES = {
    0: "Backlog",
    1: "Analysis",
    2: "Development",
    3: "Review",
    4: "Testing",
    5: "Done",
}

TASK_SOURCE_KEYS = {
    "task_id": "Task id",
    "task_name": "Task name",
    "cycle_time_minutes": "Cycle time (Minutes)",
    "lead_time_minutes": "Lead time (Minutes)",
}

BASE_COLUMNS = [
    "simulation_day",
    "simulation_clock_time",
    "workflow_column_count",
    "active_work_in_progress_count",
    "completed_task_count",
    "task_id",
    "task_name",
    "task_processing_state",
    "worker_assigned",
    "remaining_processing_units",
    "created_day",
    "created_time",
    "completed_day",
    "completed_time",
    "cycle_time_minutes",
    "lead_time_minutes",
    "current_column_number",
    "current_column_name",
]

COLUMN_CYCLE_SOURCE = "Column Cycle Time (Minutes) [Backlog, Column 1, Column 2, Column 3, Column 4]"
COLUMN_ENTRY_SOURCE = "Column Entry Time [Backlog, Column 1, Column 2, Column 3, Column 4]"
COLUMN_EXIT_SOURCE = "Column Exit Time [Backlog, Column 1, Column 2, Column 3, Column 4]"


def _format_csv_cell(value):
    if value is None:
        return ""
    return value


def _slugify_column_name(name):
    return "".join(
        character.lower() if character.isalnum() else "_"
        for character in str(name)
    ).strip("_") or "column"


def _format_clock_time(value):
    if value in (None, ""):
        return ""

    try:
        raw_time = str(value).strip()
        hours_text, minutes_text = raw_time.split(".", 1) if "." in raw_time else (raw_time, "0")
        hours = int(hours_text)

        if len(minutes_text) == 1:
            minutes = int(minutes_text) * 10
        else:
            minutes = int(minutes_text[:2])

        return f"{hours:02d}:{minutes:02d}"
    except (TypeError, ValueError):
        return value


def _split_day_time(value):
    if not value:
        return "", ""

    day = ""
    time_value = ""

    for part in str(value).split(","):
        label, _, raw_value = part.strip().partition(":")
        normalized_label = label.strip().lower()
        if normalized_label == "day":
            day = raw_value.strip()
        elif normalized_label == "time":
            time_value = _format_clock_time(raw_value.strip())

    return day, time_value


def _task_state(task):
    status = task.get("Status")
    worker_task = task.get("Worker task")

    if status == "Completed":
        return "Completed"
    if status in (None, ""):
        return "Waiting"

    try:
        remaining_processing = float(status)
    except (TypeError, ValueError):
        return str(status)

    if remaining_processing <= 0:
        return "Ready to move"
    if worker_task:
        return "In progress"
    return "Waiting for worker"


def _remaining_processing_units(task):
    status = task.get("Status")

    try:
        remaining_processing = float(status)
    except (TypeError, ValueError):
        return ""

    if remaining_processing.is_integer():
        return int(remaining_processing)
    return status


def _worker_assigned(value):
    return "Yes" if value else "No"


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def load_export_data(export_path=None):
    export_path = Path(export_path or EXPORT_JSON_PATH)
    if not export_path.exists():
        return {"Tasks": []}

    try:
        with export_path.open("r", encoding="utf-8") as export_file:
            return json.load(export_file)
    except json.JSONDecodeError:
        return {"Tasks": []}


def _column_lookup(export_data):
    columns = export_data.get("Columns", [])
    return {
        column.get("Column id"): DEFAULT_COLUMN_DISPLAY_NAMES.get(
            column.get("Column id"),
            column.get("Column name", f"Column {column.get('Column id')}")
        )
        for column in columns
    }


def _last_column_id(export_data):
    column_ids = [
        column.get("Column id")
        for column in export_data.get("Columns", [])
        if column.get("Column id") is not None
    ]
    return max(column_ids) if column_ids else None


def _summary_data(export_data):
    time_elapsed = (export_data.get("Time Elapsed") or [{}])[0]
    columns = export_data.get("Columns", [])
    tasks = export_data.get("Tasks", [])
    completed_tasks = [task for task in tasks if task.get("Status") == "Completed"]
    active_columns = columns[1:-1] if len(columns) > 2 else []

    return {
        "simulation_day": time_elapsed.get("Day", ""),
        "simulation_clock_time": _format_clock_time(time_elapsed.get("Time [9am - 5pm]", "")),
        "workflow_column_count": len(columns),
        "active_work_in_progress_count": sum(column.get("Tasks amount", 0) for column in active_columns),
        "completed_task_count": len(completed_tasks),
    }


def _history_column_count(export_data):
    tasks = export_data.get("Tasks", [])
    max_task_history = 0

    for task in tasks:
        max_task_history = max(
            max_task_history,
            len(_safe_list(task.get(COLUMN_CYCLE_SOURCE))),
            len(_safe_list(task.get(COLUMN_ENTRY_SOURCE))),
            len(_safe_list(task.get(COLUMN_EXIT_SOURCE))),
        )

    column_count = len(export_data.get("Columns", []))
    return max(max_task_history, max(0, column_count - 1), 1)


def _history_column_name(index, export_data):
    return _slugify_column_name(_column_lookup(export_data).get(index, f"Column {index}"))


def _history_columns(export_data):
    columns = []

    for index in range(_history_column_count(export_data)):
        column_name = _history_column_name(index, export_data)
        columns.extend([
            f"{column_name}_cycle_time_minutes",
            f"{column_name}_entry_time",
            f"{column_name}_exit_time",
        ])

    return columns


def _current_column_for_task(task, export_data):
    current_column = task.get("Current column")
    if current_column is None and task.get("Status") == "Completed":
        return _last_column_id(export_data)
    return current_column


def _history_values(task, history_count, export_data):
    cycle_times = _safe_list(task.get(COLUMN_CYCLE_SOURCE))
    entry_times = _safe_list(task.get(COLUMN_ENTRY_SOURCE))
    exit_times = _safe_list(task.get(COLUMN_EXIT_SOURCE))
    values = {}

    for index in range(history_count):
        column_name = _history_column_name(index, export_data)
        values[f"{column_name}_cycle_time_minutes"] = _format_csv_cell(cycle_times[index] if index < len(cycle_times) else "")
        values[f"{column_name}_entry_time"] = _format_clock_time(entry_times[index] if index < len(entry_times) else "")
        values[f"{column_name}_exit_time"] = _format_clock_time(exit_times[index] if index < len(exit_times) else "")

    return values


def build_task_rows(export_data):
    tasks = export_data.get("Tasks", [])
    summary = _summary_data(export_data)
    column_names = _column_lookup(export_data)
    history_count = _history_column_count(export_data)
    rows = []

    for task in tasks:
        current_column = _current_column_for_task(task, export_data)
        created_day, created_time = _split_day_time(task.get("Created at"))
        completed_day, completed_time = _split_day_time(task.get("Done at"))
        row = dict(summary)
        row.update({
            csv_column: _format_csv_cell(task.get(source_key))
            for csv_column, source_key in TASK_SOURCE_KEYS.items()
        })
        row["task_processing_state"] = _task_state(task)
        row["worker_assigned"] = _worker_assigned(task.get("Worker task"))
        row["remaining_processing_units"] = _remaining_processing_units(task)
        row["created_day"] = created_day
        row["created_time"] = created_time
        row["completed_day"] = completed_day
        row["completed_time"] = completed_time
        row["current_column_number"] = _format_csv_cell(current_column)
        row["current_column_name"] = column_names.get(current_column, "")
        row.update(_history_values(task, history_count, export_data))
        rows.append(row)

    return rows


def generate_tasks_csv(export_data):
    output = io.StringIO()
    fieldnames = BASE_COLUMNS + _history_columns(export_data)

    # Helps Excel open the file with separate columns in locales that expect semicolons.
    output.write("sep=;\r\n")
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=";", lineterminator="\r\n")

    writer.writeheader()
    writer.writerows(build_task_rows(export_data))

    return output.getvalue()


def build_csv_response(export_path=None):
    export_data = load_export_data(export_path)
    csv_data = generate_tasks_csv(export_data)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={CSV_FILENAME}"
        },
    )
