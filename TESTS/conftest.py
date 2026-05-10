import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "Backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def reset_kanban_state():
    import Kanban as KB
    import api_service

    KB.running = False
    KB.config_updated = False
    KB.initial_gen = False
    KB.tick_interval = 1
    KB.tick = 0
    KB.id = 0
    KB.clock = 9.00
    KB.day = 1
    KB.num_columns = 3
    KB.board_1 = None
    api_service.simulation_thread = None

    yield

    KB.running = False
    api_service.simulation_thread = None
