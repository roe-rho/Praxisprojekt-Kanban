import time

import api_service
import Kanban as KB


def test_get_board_data_returns_empty_dict_when_board_is_missing():
    assert api_service.get_board_data() == {}


def test_get_board_data_serializes_columns_and_tasks():
    KB.generate_columns(3)
    KB.generate_task()

    data = api_service.get_board_data()

    assert list(data.keys()) == ["column_0", "column_1", "column_2"]
    assert data["column_0"] == [
        {
            "id": 1,
            "name": "Task 1",
            "created_at": "Day: 1, Time: 9.0",
            "done_at": None,
            "status": None,
            "worker_task": 0,
            "cycle_time": 0,
            "progress_percent": 0,
        }
    ]
    assert data["column_1"] == []
    assert data["column_2"] == []


def test_stop_simulation_clears_tasks_and_resets_clock_and_day():
    KB.generate_columns(3)
    KB.generate_task()
    KB.clock = 12.30
    KB.day = 4

    result = api_service.stop_simulation()

    assert result == {"status": "Board reset"}
    assert KB.clock == 9.00
    assert KB.day == 1
    assert all(col.tasks == [] for col in KB.board_1.columns)


def test_stop_simulation_clears_visible_tasks_archive_and_metrics():
    KB.generate_columns(6)
    visible_task = KB.Task(
        id=1,
        name="Task 1",
        created_at="Day: 1, Time: 9.0",
        worker_task=1,
        status=5,
        cycle_time=120,
    )
    archived_task = KB.Task(
        id=2,
        name="Task 2",
        created_at="Day: 1, Time: 9.1",
        worker_task=0,
        status="Completed",
        cycle_time=300,
    )
    KB.board_1.columns[2].tasks.append(visible_task)
    KB.board_1.completed_tasks.append(archived_task)
    KB.board_1.completed_tasks_count = 7
    KB.board_1.average_cycle_time = 99
    KB.board_1.average_lead_time = 88
    KB.board_1.throughput = 3
    KB.board_1.total_wip = 4
    KB.clock = 14.50
    KB.day = 3
    KB.tick = 22
    KB.id = 15
    KB.start_event.set()

    result = api_service.stop_simulation()

    assert result == {"status": "Board reset"}
    assert not KB.start_event.is_set()
    assert not KB.paused_event.is_set()
    assert all(col.tasks == [] for col in KB.board_1.columns)
    assert KB.board_1.completed_tasks == []
    assert KB.board_1.completed_tasks_count == 0
    assert KB.board_1.average_cycle_time == 0
    assert KB.board_1.average_lead_time == 0
    assert KB.board_1.throughput == 0
    assert KB.board_1.total_wip == 0
    assert KB.clock == 9.00
    assert KB.day == 1
    assert KB.tick == 0
    assert KB.id == 0


def test_stop_simulation_stops_background_export_thread(monkeypatch):
    KB.generate_columns(6)

    def wait_until_stopped():
        while KB.start_event.is_set():
            time.sleep(0.01)

    monkeypatch.setattr(KB, "main", wait_until_stopped)

    assert api_service.start_simulation() == {"status": "Simulation started"}
    started_export_thread = api_service.export_thread
    assert started_export_thread is not None
    assert started_export_thread.is_alive()

    assert api_service.stop_simulation() == {"status": "Board reset"}
    started_export_thread.join(timeout=1)

    assert not started_export_thread.is_alive()
    assert api_service.export_thread is None


def test_get_metrics_returns_zero_values_after_board_is_cleared():
    KB.generate_columns(6)
    KB.board_1.average_cycle_time = 99
    KB.board_1.average_lead_time = 88
    KB.board_1.completed_tasks_count = 7
    KB.board_1.total_wip = 4
    KB.board_1.throughput = 3

    assert api_service.get_metrics() == {
        "average_cycle_time": 0,
        "average_lead_time": 0,
        "completed_tasks_count": 0,
        "total_wip": 0,
        "throughput": 0,
    }


def test_get_clock_and_day_returns_none_values_when_board_is_missing():
    assert api_service.get_clock_and_day() == {"clock": None, "day": None}


def test_stop_simulation_is_safe_when_not_running():
    KB.generate_columns(3)

    assert api_service.stop_simulation() == {"status": "Board reset"}
