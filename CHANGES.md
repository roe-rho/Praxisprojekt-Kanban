# Kanban Project - Complete Change Documentation

## Overview
This document details all changes made to the Backend and Frontend to enable Frontend-Backend communication and dynamic task display.

---

## BACKEND CHANGES (Backend/app.py)

### 1. Added CORS Support
**Purpose:** Allow Frontend (localhost:8000) to communicate with Backend (localhost:5000)

```python
# Added import
from flask_cors import CORS

# Added to app initialization
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

**Installation:** `pip install flask-cors`

---

### 2. Fixed /start Endpoint
**Before:**
```python
@app.route('/start', methods=['POST'])
def start():
    if not KB.running:
        KB.running = True
    # No return value
```

**After:**
```python
@app.route('/start', methods=['POST'])
def start():
    if not KB.running:
        KB.running = True
    return jsonify({"status": "Simulation started"})
```

---

### 3. Fixed /stop Endpoint
**Before:**
```python
@app.route('/stop', methods=['POST'])
def stop():
    if KB.running:
        KB.running = False
    # No return value
```

**After:**
```python
@app.route('/stop', methods=['POST'])
def stop():
    if KB.running:
        KB.running = False
    return jsonify({"status": "Simulation stopped"})
```

---

### 4. Created start_kanban_simulation() Function
**Purpose:** Start simulation threads without blocking Flask server

```python
def start_kanban_simulation():
    """Start the Kanban simulation in background threads"""
    if KB.generator_thread is None or not KB.generator_thread.is_alive():
        KB.generator_thread = threading.Thread(target=KB.generate_task, daemon=True)
        KB.generator_thread.start()
    
    if not KB.worker_threads or not any(t.is_alive() for t in KB.worker_threads):
        KB.worker_threads = []
        for col in range(KB.num_columns):
            if col % 2 != 0 and col < KB.num_columns - 1:
                for i in range(KB.worker_count):
                    t = threading.Thread(target=KB.process_tasks, args=(col,), daemon=True)
                    t.start()
                    KB.worker_threads.append(t)
    
    if KB.done_thread is None or not KB.done_thread.is_alive():
        KB.done_thread = threading.Thread(target=KB.done_tasks, daemon=True)
        KB.done_thread.start()
```

**Why:** Avoids the infinite `while True` loop in `KB.main()` that was blocking Flask

---

### 5. Modified if __name__ == '__main__' Block
**Major Changes:**

- Removed: `start()` function call (caused "Working outside of application context" error)
- Removed: `KB.main()` call (had infinite loop blocking Flask)
- Added: Thread variable initialization
- Changed: `app.run()` parameters to `debug=False, use_reloader=False`

**Before:**
```python
if __name__ == '__main__':
    KB.num_columns = 3
    KB.worker_count = 2
    KB.max_tasks = 5
    
    start()  # ERROR: Can't call this outside Flask context
    KB.generate_columns(KB.num_columns)
    
    # ... monitoring thread ...
    kanban_thread = threading.Thread(target=KB.main, daemon=True)  # Infinite loop!
    kanban_thread.start()
    
    app.run(debug=True, use_reloader=False)
```

**After:**
```python
if __name__ == '__main__':
    KB.num_columns = 3
    KB.worker_count = 2
    KB.max_tasks = 5
    
    KB.generate_columns(KB.num_columns)
    KB.generator_thread = None
    KB.worker_threads = []
    KB.done_thread = None
    
    print("\n=== Initial Board State ===")
    check_board_state()
    print("\n=== Starting Kanban Board ===\n")
    
    KB.running = True
    start_kanban_simulation()
    
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000)
```

---

## FRONTEND CHANGES (Frontend/script.js)

### 1. Updated API_URL Constant
**Before:** Not properly configured
**After:** 
```javascript
const API_URL = 'http://localhost:5000';
```

---

### 2. Changed Reset Button Hold Duration
**Before:**
```javascript
const holdDuration = 2000; // 2 seconds
```

**After:**
```javascript
const HOLD_DURATION = 3000; // 3 seconds for reset hold
```

---

### 3. Implemented updateBoardDisplay() Function
**Purpose:** Display tasks fetched from API on the board

```javascript
function updateBoardDisplay(data) {
    console.log('Board state:', data);
    
    // Update each column with tasks
    const columns = ['col-backlog', 'col-doing', 'col-testing'];
    
    columns.forEach((colId, index) => {
        const cardsContainer = document.querySelector(`#${colId} .cards`);
        const columnKey = `column_${index}`;
        const tasks = data[columnKey] || [];
        
        // Clear existing cards
        cardsContainer.innerHTML = '';
        
        // Add new cards
        tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = 'card';
            card.textContent = `${task.name} (${task.created_at})`;
            cardsContainer.appendChild(card);
        });
    });
}
```

**Features:**
- Maps API columns (column_0, column_1, column_2) to HTML columns (col-backlog, col-doing, col-testing)
- Creates task cards dynamically
- Displays task name and creation timestamp
- Clears old cards before adding new ones

---

### 4. Added fetchBoardState() Function
**Purpose:** Fetch board state from API every 2 seconds

```javascript
async function fetchBoardState() {
    try {
        const response = await fetch(`${API_URL}/board`);
        const data = await response.json();
        updateBoardDisplay(data);
    } catch (error) {
        console.error('Error fetching board:', error);
    }
}
```

---

### 5. Added callAPI() Function
**Purpose:** Make API calls to backend endpoints

```javascript
async function callAPI(endpoint) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        console.log(`${endpoint} response:`, data);
    } catch (error) {
        console.error(`Error calling ${endpoint}:`, error);
    }
}
```

---

### 6. Updated Button Event Listeners
**Before:** Local state management only

**After:** API calls to backend
```javascript
// Start button
startBtn.addEventListener('click', function() {
    callAPI('/start');  // NEW: Calls backend
    isRunning = true;
    console.log('Kanban simulation started');
    startBtn.disabled = true;
    stopBtn.disabled = false;
});

// Stop button
stopBtn.addEventListener('click', function() {
    callAPI('/stop');   // NEW: Calls backend
    isRunning = false;
    console.log('Kanban simulation stopped');
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

// Reset button - hold for 3 seconds
resetBtn.addEventListener('mousedown', function() {
    holdTimer = setTimeout(function() {
        callAPI('/reset');  // NEW: Calls backend
        isRunning = false;
        console.log('Kanban simulation reset');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }, HOLD_DURATION);
});
```

---

### 7. Added Periodic Board State Fetching
**Purpose:** Keep UI in sync with backend

```javascript
// Fetch board state every 2 seconds
setInterval(fetchBoardState, 2000);
```

---

## FRONTEND CHANGES (Frontend/index.html)

### 1. Moved Script Tag
**Before:**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kanban Simulation</title>
    <link rel="stylesheet" href="style.css">
    <script src="script.js"></script>  <!-- In head -->
</head>
```

**After:**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kanban Simulation</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- ... HTML content ... -->
    <script src="script.js"></script>  <!-- Before closing </body> -->
</body>
```

**Reason:** Best practice - ensures HTML is loaded before JavaScript runs

---

### 2. Button IDs Verified
Confirmed button IDs match JavaScript:
- `id="start-btn"` → `startBtn` variable
- `id="stop-btn"` → `stopBtn` variable  
- `id="reset-btn"` → `resetBtn` variable

---

## ISSUES FIXED

✅ **CORS Error** - Frontend couldn't communicate with Backend
- Fixed by: Adding `flask_cors` and `CORS(app)`

✅ **Indentation Error** - Duplicate line in /stop endpoint
- Fixed by: Removed incorrect `KB.running = False` line

✅ **Application Context Error** - `start()` called outside Flask context
- Fixed by: Removed `start()` call, directly set `KB.running = True`

✅ **Blocking Flask Server** - `KB.main()` had infinite loop
- Fixed by: Created `start_kanban_simulation()` with proper threading

✅ **Empty Task Display** - No tasks shown on Frontend
- Fixed by: Implemented `updateBoardDisplay()` with dynamic card creation

✅ **No API Communication** - Buttons didn't call backend
- Fixed by: Added `callAPI()` function and updated event listeners

✅ **Script Loading Issue** - JavaScript might run before HTML loads
- Fixed by: Moved script tag to end of body

---

## CURRENT ISSUES REMAINING

⚠️ **Start/Stop/Reset Button Functionality** - In Progress
- Buttons call API endpoints but may not fully control simulation
- Need to verify `KB.running` flag is respected by all threads

---

## HOW TO RUN THE PROJECT

### Terminal 1: Start Flask Backend
```powershell
cd "c:\Users\HP Envy X360\Praxisprojekt Kanban\Backend"
python app.py
```

### Terminal 2: Start Frontend Web Server
```powershell
cd "c:\Users\HP Envy X360\Praxisprojekt Kanban\Frontend"
python -m http.server 8000
```

### Terminal 3: Open Browser
Navigate to: `http://localhost:8000`

---

## ARCHITECTURE

```
Frontend (localhost:8000)
    ↓ HTTP/CORS
Backend Flask (localhost:5000)
    ↓ Uses
Backend Kanban Logic (Kanban.py)
    ↓ Manages
Tasks moving through columns
```

---

## FILES MODIFIED

1. `Backend/app.py` - 6 major changes
2. `Frontend/script.js` - 7 major changes
3. `Frontend/index.html` - 2 minor changes

---

**Last Updated:** December 16, 2025
