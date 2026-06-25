# Backend/api_service.py to simplify connection between frontend and backend
import os
import os
import threading
import time
import Kanban as KB
import json

# Global variable to track if simulation thread is running
simulation_thread = None
export_thread = None

def start_simulation():
    global simulation_thread
    
    if not KB.start_event.is_set():
        KB.start_event.set()
        # Launch main() in background thread so it doesn't block Flask
        simulation_thread = threading.Thread(target=KB.main, daemon=True)
        simulation_thread.start()
        # Launch export_management() in background thread so it doesn't block Flask
        export_thread = threading.Thread(target=export_management, daemon=True)
        export_thread.start()
        return {"status": "Simulation started"}
    
    if KB.paused_event.is_set() and simulation_thread is not None and simulation_thread.is_alive():
        KB.paused_event.clear()
        return {"status": "Simulation resumed"}
    return {"status": "Simulation already running"}

def pause_simulation():
    global simulation_thread
    """Pause the simulation"""
    if KB.start_event.is_set() and not KB.paused_event.is_set():
        KB.paused_event.set()
        return {"status": "Simulation paused"}

def stop_simulation():
    """Reset the board"""
    global simulation_thread

    KB.start_event.clear()
    KB.paused_event.clear()

    if simulation_thread is not None and simulation_thread.is_alive():
        simulation_thread.join(timeout=2)

    with KB.lock:
        if KB.board_1 is not None:
            for col in KB.board_1.columns:
                col.tasks = []
            KB.board_1.completed_tasks = []
            KB.board_1.completed_tasks_count = 0
            KB.board_1.average_cycle_time = 0
            KB.board_1.average_lead_time = 0
            KB.board_1.throughput = 0
            KB.board_1.total_wip = 0
            KB.clock = 9.00
            KB.day = 1
            KB.tick = 0
            KB.id = 0
    
    return {"status": "Board reset"}

def get_board_data():
    """Get current board state as JSON-serializable data"""
    with KB.lock:
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
                    'cycle_time': task.cycle_time,
                    'progress_percent': progress_percent
                })
            board_state[f"column_{i}"] = tasks_list
        
        #print(f"DEBUG api_service.py - board_state keys: {list(board_state.keys())}")
        #print(f"DEBUG api_service.py - column_0 type: {type(board_state.get('column_0'))}")
        #print(f"DEBUG api_service.py - column_0 first item type: {type(board_state['column_0'][0]) if board_state.get('column_0') else 'EMPTY'}")
        return board_state

def get_clock_and_day():

    with KB.lock:

        if KB.board_1 is None:
            return {"clock": None, "day": None}
        
        
        clock = KB.clock
        day = KB.day

        #print(f"DEBUG api_service.py - clock: {clock}, day: {day}")

        return {"clock": clock, "day": day}

def get_metrics():
    with KB.lock:
        if KB.board_1 is None:
            return {"average_cycle_time": None, "average_lead_time": None, "completed_tasks_count": None, "total_wip": None, "throughput": None}

        visible_task_count = sum(len(col.tasks) for col in KB.board_1.columns)
        if visible_task_count == 0 and len(KB.board_1.completed_tasks) == 0:
            return {"average_cycle_time": 0, "average_lead_time": 0, "completed_tasks_count": 0, "total_wip": 0, "throughput": 0}
    
        average_cycle_time = KB.board_1.average_cycle_time
        average_lead_time = KB.board_1.average_lead_time
        completed_tasks_count = KB.board_1.completed_tasks_count
        throughput = KB.board_1.throughput
        total_wip = KB.board_1.total_wip

        return {"average_cycle_time": average_cycle_time, "average_lead_time": average_lead_time, "completed_tasks_count": completed_tasks_count, "total_wip": total_wip, "throughput": throughput}

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

#Data preparations for export (NEW NEW!)
def export_management():
    # Get the Backend directory path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    # Define the export file path
    export_path = os.path.join(backend_dir, 'export.json')
    while True:
        if KB.board_1 is not None:
            with KB.lock:
                Tasks =[]
                Tasks_completed = []
                Columns =[]
                Time_Elapsed = []
                config_changes = []

                #For time and day
                Time_Elapsed.append({
                    'Time [9am - 5pm]': f"{KB.clock:.2f}",
                    'Day': KB.day
                })

                #For tasks in visible columns
                for col in KB.board_1.columns[::-1]:
                    for task in col.tasks:
                        Tasks.append({
                            'Task id': task.id,
                            'Task name': task.name,
                            'Created at': task.created_at,
                            'Done at': task.done_at,
                            'Status': task.status,
                            'Task location': 'Visible Board', #added by ronan: this is to differentiate between visible and invisible tasks in the export file
                            'Worker task': task.worker_task,
                            'Cycle time (Minutes)': task.cycle_time,
                            'Lead time (Minutes)': task.lead_time,
                            'Current column': task.current_column,
                            'Column Cycle Time (Minutes) [Backlog, Column 1, Column 2, Column 3, Column 4]': task.cycle_time_column,
                            'Column Entry Time [Backlog, Column 1, Column 2, Column 3, Column 4]': task.column_entry_time,
                            'Column Exit Time [Backlog, Column 1, Column 2, Column 3, Column 4]': task.column_exit_time
                        })

                #For columns
                for col in KB.board_1.columns:
                    Columns.append({
                        'Column id': col.id,
                        'Column name': col.name,
                        'WIP Limit': col.max_tasks,
                        'Total Workers': col.initial_workers,
                        'Unassigned workers': col.workers,
                        'Tasks amount': len(col.tasks)
                    })
                
                #For config changes
                for config in KB.board_1.configs:
                    config_changes.append(config)

                #For tasks in invisible column (completed tasks)
                for task in KB.board_1.completed_tasks:
                    Tasks_completed.append({
                        'Task id': task.id,
                        'Task name': task.name,
                        'Created at': task.created_at,
                        'Done at': task.done_at,
                        'Status': task.status,
                        'Task location': 'Completed Archive', #added by ronan: this is to differentiate between visible and invisible tasks in the export file
                        'Worker task': task.worker_task,
                        'Cycle time (Minutes)': task.cycle_time,
                        'Lead time (Minutes)': task.lead_time,
                        'Column Cycle Time (Minutes) [Backlog, Column 1, Column 2, Column 3, Column 4]': task.cycle_time_column,
                        'Column Entry Time [Backlog, Column 1, Column 2, Column 3, Column 4]': task.column_entry_time,
                        'Column Exit Time [Backlog, Column 1, Column 2, Column 3, Column 4]': task.column_exit_time

                        })
                
                #Combine completed tasks and current tasks for export
                all_task = Tasks_completed + Tasks

                #Export to JSON file
                with open(export_path, 'w') as f:
                    json.dump({"Time Elapsed": Time_Elapsed,"config_changes": config_changes, "Columns": Columns, "Tasks" : all_task}, f, indent=2)
        
        while KB.paused_event.is_set():
            time.sleep(0.1)  # Sleep while paused or not started to avoid busy waiting
        time.sleep(0.5)  # Check for updates every second
