from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS # NEW: Added CORS support so Frontend can talk to Backend from different ports
from api_service import get_board_data, start_simulation, stop_simulation, reset_simulation
import webbrowser # NEW: Import webbrowser to automatically open Frontend in browser
import Kanban as KB
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

#define API endpoints for starting, stopping, resetting simulation and getting board data
#defined in api_service.py
@app.route('/board', methods=['GET'])
def board():
    print("\n\n===== FLASK BOARD ENDPOINT CALLED =====\n\n")
    data = get_board_data()
    print(f"DEBUG: get_board_data function exists: {callable(get_board_data)}")
    print(f"\n===== RETURNING DATA: {list(data.keys())} =====\n\n")
    return jsonify(data)

@app.route('/start', methods=['POST'])
def start():
    return jsonify(start_simulation())

@app.route('/stop', methods=['POST'])
def stop():
    return jsonify(stop_simulation())

@app.route('/reset', methods=['POST'])
def reset():
    return jsonify(reset_simulation())


if __name__ == '__main__':
   KB.num_columns = 3  # Set number of columns before starting
   KB.generate_columns(KB.num_columns)

   webbrowser.open('http://127.0.0.1:5000/')
   app.run(debug = False, use_reloader = False, host='127.0.0.1', port=5000)  # Ensure use_reloader is False to avoid double-starting threads