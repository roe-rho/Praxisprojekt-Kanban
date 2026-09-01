import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "Backend"
CONFIG_PATH = BACKEND_DIR / "config.json"
EXPORT_PATH = BACKEND_DIR / "export.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def reset_kanban_state():
    import Kanban as KB
    import api_service

    original_config = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else None
    original_export = EXPORT_PATH.read_text(encoding="utf-8") if EXPORT_PATH.exists() else None

    KB.start_event.clear()
    KB.paused_event.clear()
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
    api_service.export_thread = None

    yield

    KB.start_event.clear()
    KB.paused_event.clear()
    KB.running = False
    api_service.simulation_thread = None
    api_service.export_thread = None

    if original_config is None:
        CONFIG_PATH.unlink(missing_ok=True)
    else:
        CONFIG_PATH.write_text(original_config, encoding="utf-8")

    if original_export is None:
        EXPORT_PATH.unlink(missing_ok=True)
    else:
        EXPORT_PATH.write_text(original_export, encoding="utf-8")
