from flask import Flask, jsonify
import Kanban as KB
import json
import threading
import time




app = Flask(__name__)

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
    if not KB.running:
        KB.running = True


@app.route('/stop', methods=['POST'])
def stop():
    if KB.running:
        KB.running = False

@app.route('/reset', methods=['POST'])
def reset():
    KB.reset_board()
    return jsonify({"status": "Board reset"})


if __name__ == '__main__':
    
    # Initialize Kanban board parameters
    KB.num_columns = 3
    KB.worker_count = 2
    KB.max_tasks = 5
    
    start()
    
    # Generate columns for initial state display
    KB.generate_columns(KB.num_columns)
    
    print("\n=== Initial Board State ===")
    check_board_state()
    print("\n=== Starting Kanban Board ===\n")
    
    # Start monitoring thread to display board state
    monitor_thread = threading.Thread(target=monitor_board_state, daemon=True)
    monitor_thread.start()
    
    # Start Kanban main function in a separate thread
    kanban_thread = threading.Thread(target=KB.main, daemon=True)
    kanban_thread.start()
    
    # Start the Flask app
    app.run(debug=True, use_reloader=False)