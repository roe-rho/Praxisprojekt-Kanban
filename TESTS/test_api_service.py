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
        }
    ]
    assert data["column_1"] == []
    assert data["column_2"] == []


def test_reset_simulation_clears_tasks_and_resets_clock_and_day():
    KB.generate_columns(3)
    KB.generate_task()
    KB.clock = 12.30
    KB.day = 4

    result = api_service.reset_simulation()

    assert result == {"status": "Board reset"}
    assert KB.clock == 9.00
    assert KB.day == 1
    assert all(col.tasks == [] for col in KB.board_1.columns)


def test_get_clock_and_day_returns_none_values_when_board_is_missing():
    assert api_service.get_clock_and_day() == {"clock": None, "day": None}


def test_stop_simulation_returns_none_when_not_running():
    assert api_service.stop_simulation() is None
