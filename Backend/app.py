from flask import Flask, jsonify, send_from_directory
# NEW: Added CORS support so Frontend can talk to Backend from different ports
from flask_cors import CORS
# NEW: Import webbrowser to automatically open Frontend in browser
import webbrowser
import Kanban as KB
import json
import time
import os
import threading

# NEW: Get the absolute path to the Frontend folder
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'Frontend')

app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')
# NEW: Enable CORS - allows localhost:8000 (Frontend) to communicate with localhost:5000 (Backend)
CORS(app)  # Enable CORS for all routes

# NEW: Serve Frontend files (index.html, script.js, style.css) directly from Flask
@app.route('/')
def index():
    return send_from_directory(FRONTEND_PATH, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_PATH, filename)

def get_board_state():
    board_state = {}
    
    if hasattr(KB, 'board_1') and KB.board_1 is not None:
        with KB.lock:
            for i in range(len(KB.board_1.columns)):
                column = KB.board_1.columns[i]
                tasks = []
                for task in column.tasks:
                    tasks.append({
                        "id": task.id,
                        "name": task.name,
                        "status": task.status,
                        "created_at": task.created_at,
                        "done_at": task.done_at,
                        "worker_task": task.worker_task
                    })
                board_state[f"column_{i}"] = {
                    "id": column.id,
                    "name": column.name,
                    "max_tasks": column.max_tasks,
                    "workers": column.workers,
                    "processing_time": column.processing_time,
                    "tasks": tasks
                }
    
    return board_state

def check_board_state(): #Print board state to terminal
    state = get_board_state()
    print(json.dumps(state, indent=4))

def monitor_board_state(): #Terminal display of board state
    """Continuously monitor and display board state"""
    while KB.running:
        check_board_state()
        time.sleep(2)  # Display state every 2 seconds

#def get_user_config():
    
    #config = {
        #for i in range(KB.num_columns):
            #f"column_{i}": {
                #"max_tasks": KB.board_1.columns[0].max_tasks,
                #"worker_count": KB.worker_count,
        #"num_columns": KB.num_columns
    #}

#@app.route('/config', methods=['GET'])
#def config():
    #config = get_user_config()
    #return jsonify(config)

@app.route('/board', methods=['GET'])
def board():
    state = get_board_state()
    return jsonify(state)

@app.route('/start', methods=['POST'])
def start():
    # Start Kanban simulation in a background thread
    def run_kanban():
        KB.main()
    
    kanban_thread = threading.Thread(target=run_kanban, daemon=True)
    kanban_thread.start()
    
    # Start monitor in a background thread
    monitor_thread = threading.Thread(target=monitor_board_state, daemon=True)
    monitor_thread.start()
    
    return jsonify({"status": "Simulation started"})

@app.route('/stop', methods=['POST'])
def stop():
    # NEW: Check if running before stopping (safety check)
    if KB.running:
        # NEW: Set running flag to False - this stops all threads gracefully
        KB.running = False
    # NEW: Return JSON response so Frontend knows it worked
    return jsonify({"status": "Simulation stopped"})

@app.route('/reset', methods=['POST'])
def reset():
    try:
        # NEW: Stop the simulation first
        KB.running = False
        # NEW: Use thread lock to safely clear all columns
        with KB.lock:
            # NEW: Loop through all columns and empty them
            for i in range(len(KB.column)):
                KB.column[i] = []
        print("Board has been reset.")
        # NEW: Return success message
        return jsonify({"status": "Board reset"})
    except Exception as e:
        # NEW: Error handling - if something goes wrong, return error message
        print(f"Error resetting board: {e}")
        return jsonify({"status": "Error resetting board", "error": str(e)}), 500


if __name__ == '__main__':
    print("\n=== Starting Flask Server ===")
    print("Board state will be available at /board endpoint")
    print("Use /start endpoint via POST request to begin simulation\n")
    
    # Automatically open the Frontend in the default browser
    webbrowser.open('http://127.0.0.1:5000/')
    
    # Start Flask server on localhost:5000
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000)
    
    