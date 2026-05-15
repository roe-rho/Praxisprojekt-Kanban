import app as flask_app
import Kanban as KB


def test_board_route_returns_current_board_state_as_json():
    KB.generate_columns(3)
    client = flask_app.app.test_client()

    response = client.get("/board")

    assert response.status_code == 200
    assert response.get_json() == {
        "column_0": [],
        "column_1": [],
        "column_2": [],
    }


def test_reset_route_resets_board_state():
    KB.generate_columns(3)
    KB.generate_task()
    client = flask_app.app.test_client()

    response = client.post("/reset")

    assert response.status_code == 200
    assert response.get_json() == {"status": "Board reset"}
    assert all(col.tasks == [] for col in KB.board_1.columns)


def test_clock_and_day_route_returns_none_values_when_board_is_missing():
    client = flask_app.app.test_client()

    response = client.get("/clock-and-day")

    assert response.status_code == 200
    assert response.get_json() == {"clock": None, "day": None}


def test_update_config_route_rejects_missing_json_body():
    client = flask_app.app.test_client()

    response = client.post("/update-config")

    assert response.status_code == 400
    assert response.get_json() == {"error": "No JSON data provided"}


def test_update_config_route_writes_json_and_marks_config_updated():
    client = flask_app.app.test_client()
    new_config = {
        "column_0": "9",
        "column_1": "4",
        "column_2": "5",
        "workers_1": "2",
        "columns": [
            {"name": "To Do", "type": "queue", "wip_limit": "9", "workers": "0", "processing_time": "0"},
            {"name": "Analysis", "type": "process", "wip_limit": "4", "workers": "2", "processing_time": "8"},
            {"name": "Development", "type": "process", "wip_limit": "5", "workers": "2", "processing_time": "10"},
            {"name": "Review", "type": "process", "wip_limit": "4", "workers": "1", "processing_time": "6"},
            {"name": "Testing", "type": "process", "wip_limit": "4", "workers": "1", "processing_time": "8"},
            {"name": "Done", "type": "done", "wip_limit": "99", "workers": "0", "processing_time": "0"},
        ],
    }

    response = client.post("/update-config", json=new_config)

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "Config updated successfully",
        "config": new_config,
    }
    assert KB.config_updated is True
