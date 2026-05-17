from flask import Flask, json, jsonify, request, send_from_directory
from flask_cors import CORS # NEW: Added CORS support so Frontend can talk to Backend from different ports
from api_service import get_board_data, get_metrics, start_simulation, pause_simulation, stop_simulation, get_clock_and_day, update_config
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
    #print("\n\n===== FLASK BOARD ENDPOINT CALLED =====\n\n")
    data = get_board_data()
    #print(f"DEBUG: get_board_data function exists: {callable(get_board_data)}")
    print(f"\n===== RETURNING DATA: {list(data.keys())} =====\n\n")
    return jsonify(data)



@app.route('/start', methods=['POST'])
def start():
    return jsonify(start_simulation())

@app.route('/pause', methods=['POST'])
def pause():
    return jsonify(pause_simulation())

@app.route('/stop', methods=['POST'])
def stop():
    return jsonify(stop_simulation())

@app.route('/clock-and-day', methods=['GET'])
def clock_and_day():
    #print("\n\n===== FLASK CLOCK_AND_DAY ENDPOINT CALLED =====\n\n")
    data2 = get_clock_and_day()  # Call the revised function
    #print(f"DEBUG: get_clock_and_day function exists: {callable(get_clock_and_day)}")
    #print(f"\n===== RETURNING DATA: {list(data2.keys())} =====\n\n")
    return jsonify(data2)

@app.route('/metrics', methods=['GET'])
def metrics():
    metrics_data = get_metrics()
    #print(f"\n\n===== FLASK METRICS ENDPOINT CALLED =====\n\n")
    #print(f"DEBUG: get_metrics function exists: {callable(get_metrics)}")
    #print(f"Metrics data: {metrics_data}")
    return jsonify(metrics_data)


@app.route('/update-config', methods=['POST'])
def update_config():
    try:
        #print("\n\n===== FLASK UPDATE_CONFIG ENDPOINT CALLED =====\n\n")
        new_config = request.get_json(silent=True) #I changed the JSON reader so that if no JSON is sent, the app politely returns a clear 400 error instead of crashing. via silent = true, it will return None instead of raising an error if the JSON is invalid or missing.
        if new_config is None:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Get the Backend directory path
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(backend_dir, 'config.json')
        
        # Save config to file
        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=2)
        
        # Signal that config has been updated so columns will regenerate
        KB.config_updated = True
        
        return jsonify({"status": "Config updated successfully", "config": new_config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    


    


if __name__ == '__main__':
   KB.num_columns = 6  # Set number of columns before starting
   KB.generate_columns(KB.num_columns)

   webbrowser.open('http://127.0.0.1:5000/')
   app.run(debug = False, use_reloader = False, host='127.0.0.1', port=5000)  # Ensure use_reloader is False to avoid double-starting threads
