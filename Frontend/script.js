// Get references to the three buttons
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');

// NEW: URL where Backend Flask server is running (must match app.run() host:port)
const API_URL = 'http://localhost:5000';
let isRunning = false;
let holdTimer = null;
// NEW: Changed to 3 seconds for reset hold (user must hold button 3 seconds to reset)
const HOLD_DURATION = 3000; // 3 seconds for reset hold

// NEW: Fetch the current board state from the Backend API
async function fetchBoardState() {
    try {
        // NEW: Make GET request to /board endpoint
        const response = await fetch(`${API_URL}/board`);
        // NEW: Convert response to JSON
        const data = await response.json();
        // NEW: Update the display with the fetched data
        updateBoardDisplay(data);
    } catch (error) {
        // NEW: Log any errors (e.g., if server is not running)
        console.error('Error fetching board:', error);
    }
}

// NEW: Update the HTML board with task data from the API
function updateBoardDisplay(data) {
    console.log('Board state:', data);
    
    // NEW: List of HTML column IDs in order (matches Backend column_0, column_1, column_2)
    const columns = ['col-backlog', 'col-doing', 'col-testing'];
    
    // NEW: Loop through each column and update it with tasks
    columns.forEach((colId, index) => {
        // NEW: Find the cards container for this column
        const cardsContainer = document.querySelector(`#${colId} .cards`);
        // NEW: Get the corresponding data from Backend (e.g., column_0, column_1)
        const columnKey = `column_${index}`;
        // NEW: Get tasks for this column (empty array if none exist)
        const tasks = data[columnKey] || [];
        
        // NEW: Remove all old task cards from this column
        cardsContainer.innerHTML = '';
        
        // NEW: Create new card for each task
        tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = 'card';
            // NEW: Display task name and when it was created
            card.textContent = `${task.id} (${task.created_at})`;
            cardsContainer.appendChild(card);
        });
    });
}

// NEW: Send commands to the Backend API
async function callAPI(endpoint) {
    try {
        // NEW: Make POST request to Backend endpoint (e.g., /start, /stop, /reset)
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        // NEW: Get response and log it
        const data = await response.json();
        console.log(`${endpoint} response:`, data);
    } catch (error) {
        // NEW: Log errors if request fails
        console.error(`Error calling ${endpoint}:`, error);
    }
}

// NEW: Start button click - call Backend to start simulation
startBtn.addEventListener('click', function() {
    // NEW: Tell Backend to start the simulation
    callAPI('/start');
    isRunning = true;
    console.log('Kanban simulation started');
    // NEW: Disable Start button, enable Stop button
    startBtn.disabled = true;
    stopBtn.disabled = false;
});

// NEW: Stop button click - call Backend to stop simulation
stopBtn.addEventListener('click', function() {
    // NEW: Tell Backend to stop the simulation
    callAPI('/stop');
    isRunning = false;
    console.log('Kanban simulation stopped');
    // NEW: Enable Start button, disable Stop button
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

// NEW: Reset button - user must hold for 3 seconds (security feature)
resetBtn.addEventListener('mousedown', function() {
    // NEW: Start counting down - if user holds 3 seconds, reset
    holdTimer = setTimeout(function() {
        // NEW: Tell Backend to reset (clear all tasks)
        callAPI('/reset');
        isRunning = false;
        console.log('Kanban simulation reset');
        // NEW: Reset buttons to initial state
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }, HOLD_DURATION);
});

// NEW: If user releases button before 3 seconds, cancel the reset
resetBtn.addEventListener('mouseup', function() {
    clearTimeout(holdTimer);
});

// NEW: If user moves mouse away from button before 3 seconds, cancel the reset
resetBtn.addEventListener('mouseleave', function() {
    clearTimeout(holdTimer);
});

// NEW: Automatically fetch board state every 2 seconds to keep UI in sync with Backend
setInterval(fetchBoardState, 2000);

// NEW: Start with Stop button disabled (simulation must start first)
stopBtn.disabled = true;