from flask import Flask, jsonify, send_from_directory
# NEW: Added CORS support so Frontend can talk to Backend from different ports
from flask_cors import CORS
# NEW: Import webbrowser to automatically open Frontend in browser
import webbrowser
import Kanban as KB
import json
import threading
import time
import os

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
    
    # Check if columns exist in Kanban module
    if hasattr(KB, 'column'):
        with KB.lock:
            for i, col in enumerate(KB.column):
                board_state[f"column_{i}"] = col.copy()
    
    return board_state

def check_board_state():
    state = get_board_state()
    print(json.dumps(state, indent=4))

def monitor_board_state():
    """Continuously monitor and display board state"""
    while KB.running:
        check_board_state()
        time.sleep(2)  # Display state every 2 seconds

@app.route('/board', methods=['GET'])
def board():
    state = get_board_state()
    return jsonify(state)

@app.route('/start', methods=['POST'])
def start():
    # NEW: Set running flag to True to start the simulation
    KB.running = True
    KB.main()

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
    # MAIN FUNCTION EXPLANATION:
    # Before: KB.main() had a blocking while True loop that prevented Flask from handling requests
    # After: We now start simulation in background threads using start_kanban_simulation(), which
    # creates daemon threads for task generation and processing. These threads run independently
    # without blocking Flask, allowing the web server to stay responsive to Frontend API requests.
    # This architecture enables Frontend-Backend communication: the Frontend periodically fetches
    # the board state via /board endpoint, and buttons send control commands (/start, /stop, /reset)
    # to manage the simulation.
    
    # NEW: Initialize board settings
    KB.num_columns = 3
    KB.worker_count = 2
    KB.max_tasks = 5
    
    # NEW: Create empty columns for the board
    KB.generate_columns(KB.num_columns)
    # NEW: Initialize thread variables (needed for start/stop functionality)
    KB.generator_thread = None
    KB.worker_threads = []
    KB.done_thread = None
    
    print("\n=== Initial Board State ===")
    check_board_state()
    print("\n=== Starting Kanban Board ===\n")
    
    
    # NEW: Automatically open the Frontend in the default browser
    # Now opens localhost:5000 instead of 5500 (Flask serves the Frontend)
    webbrowser.open('http://127.0.0.1:5000/')
    
    # NEW: Start Flask server on localhost:5000 (serves both Backend API and Frontend)
    # debug=False: Don't show debug mode (safer for production)
    # use_reloader=False: Don't reload on code changes (prevents double thread creation)
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000)

    # NEW: Start the simulation
    KB.running = True
    start()
    
    print("\n=== Initial Board State ===")
    check_board_state()
    print("\n=== Starting Kanban Board ===\n")
    
    