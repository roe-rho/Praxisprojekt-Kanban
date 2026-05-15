# Backend/api_service.py to simplify connection between frontend and backend
import threading
import Kanban as KB

# Global variable to track if simulation thread is running
simulation_thread = None

def start_simulation():
    global simulation_thread
    
    if not KB.running:
        KB.running = True
        # Launch main() in background thread so it doesn't block Flask
        simulation_thread = threading.Thread(target=KB.main, daemon=True)
        simulation_thread.start()
        return {"status": "Simulation started"}
    return {"status": "Simulation already running"}

def stop_simulation():
    global simulation_thread
    """Stop the simulation"""
    if KB.running:
        KB.running = False
        simulation_thread.join()
        return {"status": "Simulation stopped"}

def reset_simulation():
    """Reset the board"""
    KB.running = False
    
    with KB.lock:
        if KB.board_1 is not None:
            for col in KB.board_1.columns:
                col.tasks = []
            KB.clock = 9.00
            KB.day = 1
            KB.completed_tasks_count = 0
    
    return {"status": "Board reset"}

def get_board_data():
    """Get current board state as JSON-serializable data"""
    board_state = {}
    
    if KB.board_1 is None:
        return board_state

    for i, col in enumerate(KB.board_1.columns):
            # Convert Task objects to dictionaries
        tasks_list = []
        for task in col.tasks:
            if task.status is not None and col.processing_time > 0:
                progress_percent = ((col.processing_time - task.status) / col.processing_time) * 100
                progress_percent = max(0, min(100, round(progress_percent, 2)))
            elif i == len(KB.board_1.columns) - 1:
                progress_percent = 100
            else:
                progress_percent = 0

            tasks_list.append({
                'id': task.id,
                'name': task.name,
                'created_at': task.created_at,
                'done_at': task.done_at,
                'status': task.status,
                'worker_task': task.worker_task,
                'progress_percent': progress_percent
            })
        board_state[f"column_{i}"] = tasks_list

    done_visible_count = len(KB.board_1.columns[-1].tasks)
    board_state["_metrics"] = {
        "completed_tasks": KB.completed_tasks_count + done_visible_count
    }
    
    #print(f"DEBUG api_service.py - board_state keys: {list(board_state.keys())}")
    #print(f"DEBUG api_service.py - column_0 type: {type(board_state.get('column_0'))}")
    #print(f"DEBUG api_service.py - column_0 first item type: {type(board_state['column_0'][0]) if board_state.get('column_0') else 'EMPTY'}")
    return board_state

def get_clock_and_day():

    if KB.board_1 is None:
        return {"clock": None, "day": None}
    
    if KB.running == True:
        clock = KB.clock
        day = KB.day

    #print(f"DEBUG api_service.py - clock: {clock}, day: {day}")

    return {"clock": clock, "day": day}

def update_config():
    if KB.board_1 is None:
        return {"error": "Board not initialized yet"}
    
    if KB.config_updated == False:
        KB.config_updated = True
        return {"status": "Config already updated"}
    
    for i, col in enumerate(KB.board_1.columns):
        wip_limit_updated = []
        for i in range(len(KB.board_1.columns)):
            wip_limit_updated.append({
                'column': f"column_{i}",
                'updated_wip_limit' : col.wip_limit
            })
        wip_limit_updated[f"column_{i}"] = col.wip_limit

    
    return wip_limit_updated

       
