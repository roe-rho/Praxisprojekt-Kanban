import Kanban as KB


def test_generate_columns_creates_expected_board():
    KB.generate_columns(3)

    assert KB.board_1.total_columns == 3
    assert len(KB.board_1.columns) == 3
    assert KB.board_1.columns[0].workers == 0
    assert KB.board_1.columns[0].processing_time == 0
    assert KB.board_1.columns[1].workers == 2
    assert KB.board_1.columns[1].processing_time == 10
    assert KB.board_1.columns[2].workers == 0
    assert KB.board_1.columns[2].processing_time == 0


def test_tick_manager_advances_from_end_of_day_to_next_day():
    KB.tick = 0
    KB.clock = 16.50
    KB.day = 1
    KB.tick_interval = 1

    KB.tick_manager()

    assert KB.tick == 1
    assert KB.clock == 9.00
    assert KB.day == 2


def test_generate_task_adds_task_to_backlog():
    KB.generate_columns(3)

    KB.generate_task()

    backlog = KB.board_1.columns[0].tasks
    assert len(backlog) == 1
    assert backlog[0].id == 1
    assert backlog[0].name == "Task 1"
    assert backlog[0].created_at == "Day: 1, Time: 9.0"
    assert backlog[0].worker_task == 0


def test_generate_task_respects_backlog_wip_limit():
    KB.generate_columns(3)
    KB.board_1.columns[0].max_tasks = 1

    KB.generate_task()
    KB.generate_task()

    assert len(KB.board_1.columns[0].tasks) == 1


def test_process_tasks_moves_task_from_backlog_to_processing_column():
    KB.generate_columns(3)
    KB.generate_task()

    KB.process_tasks(1)

    assert KB.board_1.columns[0].tasks == []
    assert len(KB.board_1.columns[1].tasks) == 1
    task = KB.board_1.columns[1].tasks[0]
    assert task.status == 10
    assert task.worker_task == 1
    assert KB.board_1.columns[1].workers == 1


def test_process_tasks_moves_finished_task_to_done_column():
    KB.generate_columns(3)
    task = KB.Task(id=1, name="Task 1", created_at="Day: 1, Time: 9.0", worker_task=1, status=1)
    KB.board_1.columns[1].tasks.append(task)

    KB.process_tasks(1)

    assert KB.board_1.columns[1].tasks == []
    assert KB.board_1.columns[2].tasks == [task]
    assert task.status is None
    assert task.worker_task == 0


def test_update_config_loads_wip_limits_and_worker_count():
    KB.generate_columns(3)

    KB.update_config()

    assert KB.board_1.columns[0].max_tasks == 9
    assert KB.board_1.columns[1].max_tasks == 4
    assert KB.board_1.columns[1].workers == 2
    assert KB.board_1.columns[2].max_tasks == 5


def test_generate_columns_can_use_configured_column_definitions(monkeypatch):
    monkeypatch.setattr(KB, "load_config", lambda: {
        "columns": [
            {"name": "To Do", "type": "queue", "wip_limit": 7, "workers": 0, "processing_time": 0},
            {"name": "Analysis", "type": "process", "wip_limit": 3, "workers": 1, "processing_time": 6},
            {"name": "Development", "type": "process", "wip_limit": 4, "workers": 2, "processing_time": 8},
            {"name": "Done", "type": "done", "wip_limit": 99, "workers": 0, "processing_time": 0},
        ]
    })

    KB.generate_columns()

    assert KB.num_columns == 4
    assert [col.name for col in KB.board_1.columns] == ["To Do", "Analysis", "Development", "Done"]
    assert [col.column_type for col in KB.board_1.columns] == ["queue", "process", "process", "done"]
    assert KB.board_1.columns[2].workers == 2
    assert KB.board_1.columns[2].processing_time == 8


def test_even_index_process_column_can_process_tasks(monkeypatch):
    monkeypatch.setattr(KB, "load_config", lambda: {
        "columns": [
            {"name": "To Do", "type": "queue", "wip_limit": 7, "workers": 0, "processing_time": 0},
            {"name": "Analysis", "type": "process", "wip_limit": 3, "workers": 1, "processing_time": 1},
            {"name": "Development", "type": "process", "wip_limit": 4, "workers": 1, "processing_time": 8},
            {"name": "Done", "type": "done", "wip_limit": 99, "workers": 0, "processing_time": 0},
        ]
    })
    KB.generate_columns()
    KB.generate_task()

    KB.process_tasks(1)
    KB.process_tasks(1)
    KB.process_tasks(2)

    assert KB.board_1.columns[1].tasks == []
    assert len(KB.board_1.columns[2].tasks) == 1
    task = KB.board_1.columns[2].tasks[0]
    assert task.status == 8
    assert task.worker_task == 1
