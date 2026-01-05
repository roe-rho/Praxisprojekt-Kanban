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
    """Stop the simulation"""
    KB.running = False
    return {"status": "Simulation stopped"}

def reset_simulation():
    """Reset the board"""
    KB.running = False
    
    with KB.lock:
        if KB.board_1 is not None:
            for col in KB.board_1.columns:
                col.tasks = []
    
    return {"status": "Board reset"}

def get_board_data():
    """Get current board state as JSON-serializable data"""
    board_state = {}
    
    if KB.board_1 is None:
        return board_state
    
    with KB.lock:
        for i, col in enumerate(KB.board_1.columns):
            # Convert Task objects to dictionaries
            tasks_list = []
            for task in col.tasks:
                tasks_list.append({
                    'id': task.id,
                    'name': task.name,
                    'created_at': task.created_at,
                    'done_at': task.done_at,
                    'status': task.status
                })
            board_state[f"column_{i}"] = tasks_list
    
    print(f"DEBUG api_service.py - board_state keys: {list(board_state.keys())}")
    print(f"DEBUG api_service.py - column_0 type: {type(board_state.get('column_0'))}")
    print(f"DEBUG api_service.py - column_0 first item type: {type(board_state['column_0'][0]) if board_state.get('column_0') else 'EMPTY'}")
    return board_state