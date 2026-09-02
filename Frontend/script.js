// Get references to the three buttons
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const stopBtn = document.getElementById('stop-btn');
const updateBtn = document.getElementById('update-btn');
const exportCsvBtn = document.getElementById('export-csv-btn');
const speedInput = document.getElementById('speed');
const speedValue = document.getElementById('speed-value');

// NEW: URL where Backend Flask server is running (must match app.run() host:port)
const API_URL = window.location.origin;
let isRunning = false;
let holdTimer = null;
let isExportingCsv = false;
let displayVersion = 0;
// NEW: Changed to 3 seconds for reset hold (user must hold button 3 seconds to reset)
const HOLD_DURATION = 3000; // 3 seconds for reset hold

function updateSpeedValue() {
    speedValue.textContent = `${Number(speedInput.value).toFixed(1)}x`;
}

speedInput.addEventListener('input', updateSpeedValue);
updateSpeedValue();

function getBackendTickInterval() {
    const selectedSpeed = Number(speedInput.value);
    return (2.1 - selectedSpeed).toFixed(1);
}

function getTaskStatusLabel(status) {
    if (status === null || status === undefined) {
        return 'Waiting';
    }
    if (status === 'Completed') {
        return 'Completed';
    }
    if (Number(status) <= 0) {
        return 'Ready to move';
    }
    return `Status ${status}`;
}

function getTaskStatusClass(status) {
    if (status === 'Completed') {
        return 'status-completed';
    }
    if (status === null || status === undefined || Number(status) <= 0) {
        return 'status-waiting';
    }
    return 'status-active';
}

function clearBoardDisplay() {
    const columns = ['col-backlog', 'col-doing', 'col-doing-2', 'col-doing-3', 'col-doing-4', 'col-testing'];

    columns.forEach(colId => {
        const cardsContainer = document.querySelector(`#${colId} .cards`);
        if (cardsContainer) {
            cardsContainer.innerHTML = '';
        }
    });
}

function resetClockAndDayDisplay() {
    document.getElementById('clock').textContent = 'Clock: 9.00';
    document.getElementById('day').textContent = 'Day: 1';
}

function resetMetricsDisplay() {
    document.getElementById('average-cycle-time').textContent = 'Average Cycle Time: 0';
    document.getElementById('completed-tasks').textContent = 'Completed Tasks: 0';
    document.getElementById('total-wip').textContent = 'Total WIP: 0';
    document.getElementById('average-lead-time').textContent = 'Average Lead Time: 0';
    document.getElementById('throughput').textContent = 'Throughput: 0 per day';
}

function resetLocalDisplay() {
    isRunning = false;
    clearBoardDisplay();
    resetClockAndDayDisplay();
    resetMetricsDisplay();
}

function invalidatePendingDisplayUpdates() {
    displayVersion += 1;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 1500) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        return await fetch(url, {
            ...options,
            signal: controller.signal
        });
    } finally {
        clearTimeout(timeoutId);
    }
}

// NEW: Fetch the current board state from the Backend API
async function fetchBoardState() {
    const requestVersion = displayVersion;

    try {
        // NEW: Make GET request to /board endpoint
        const response = await fetchWithTimeout(`${API_URL}/board`);
        if (!response.ok) {
            throw new Error(`Board request failed with status ${response.status}`);
        }
        // NEW: Convert response to JSON
        const data = await response.json();
        if (requestVersion !== displayVersion) {
            return;
        }
        // NEW: Update the display with the fetched data
        updateBoardDisplay(data);
    } catch (error) {
        if (requestVersion !== displayVersion) {
            return;
        }
        // NEW: Log any errors (e.g., if server is not running)
        console.error('Error fetching board:', error);
        resetLocalDisplay();
    }
}

async function fetchClockAndDay() {
    const requestVersion = displayVersion;

    try {
        // NEW: Make GET request to /clock-and-day endpoint to get clock and day
        const response = await fetchWithTimeout(`${API_URL}/clock-and-day`);
        if (!response.ok) {
            throw new Error(`Clock request failed with status ${response.status}`);
        }
        const data2 = await response.json();
        if (requestVersion !== displayVersion) {
            return;
        }
        // NEW: Update the display with the fetched clock and day (formatted to 2 decimal places)
        document.getElementById('clock').textContent = `Clock: ${parseFloat(data2.clock).toFixed(2)}`;
        document.getElementById('day').textContent = `Day: ${data2.day}`;
    } catch (error) {
        if (requestVersion !== displayVersion) {
            return;
        }
        console.error('Error fetching clock and day:', error);
        resetClockAndDayDisplay();
    }
}

// NEW: Update the HTML board with task data from the API
function updateBoardDisplay(data) {
    console.log('Board state:', data);
    
    // NEW: List of HTML column IDs in order (matches Backend column_0, column_1, column_2)
    const columns = ['col-backlog', 'col-doing', 'col-doing-2','col-doing-3','col-doing-4', 'col-testing'];
    
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

            const taskTitle = document.createElement('h3');
            taskTitle.className = 'task-title';
            taskTitle.textContent = `Task ${task.id}`;

            const taskMeta = document.createElement('div');
            taskMeta.className = 'task-meta';

            const statusBadge = document.createElement('span');
            statusBadge.className = `task-badge ${getTaskStatusClass(task.status)}`;
            statusBadge.textContent = getTaskStatusLabel(task.status);

            const workerBadge = document.createElement('span');
            workerBadge.className = 'task-badge worker';
            workerBadge.textContent = `Worker ${task.worker_task}`;

            const cycleBadge = document.createElement('span');
            cycleBadge.className = 'task-badge cycle';
            cycleBadge.textContent = `Cycle ${task.cycle_time}`;

            const createdAt = document.createElement('p');
            createdAt.className = 'task-created';
            createdAt.textContent = task.created_at;

            const progressTrack = document.createElement('div');
            progressTrack.className = 'progress-track';

            const progressFill = document.createElement('div');
            progressFill.className = 'progress-fill';
            progressFill.style.width = `${task.progress_percent || 0}%`;

            const progressLabel = document.createElement('span');
            progressLabel.className = 'progress-label';
            progressLabel.textContent = `${Math.round(task.progress_percent || 0)}%`;

            taskMeta.appendChild(statusBadge);
            taskMeta.appendChild(workerBadge);
            taskMeta.appendChild(cycleBadge);
            progressTrack.appendChild(progressFill);
            progressTrack.appendChild(progressLabel);
            card.appendChild(taskTitle);
            card.appendChild(taskMeta);
            card.appendChild(createdAt);
            card.appendChild(progressTrack);
            cardsContainer.appendChild(card);
        });
    });
}

async function fetchMetricsDisplay() {
    const requestVersion = displayVersion;

    try {
        const response = await fetchWithTimeout(`${API_URL}/metrics`);
        if (!response.ok) {
            throw new Error(`Metrics request failed with status ${response.status}`);
        }
        const metrics_data = await response.json();
        if (requestVersion !== displayVersion) {
            return;
        }
        console.log('Metrics data:', metrics_data);
        document.getElementById('average-cycle-time').textContent = `Average Cycle Time: ${metrics_data.average_cycle_time}`;
        document.getElementById('completed-tasks').textContent = `Completed Tasks: ${metrics_data.completed_tasks_count}`;
        document.getElementById('total-wip').textContent = `Total WIP: ${metrics_data.total_wip}`;
        document.getElementById('average-lead-time').textContent = `Average Lead Time: ${metrics_data.average_lead_time}`;
        document.getElementById('throughput').textContent = `Throughput: ${metrics_data.throughput} per day`;
    } catch (error) {
        if (requestVersion !== displayVersion) {
            return;
        }
        console.error('Error fetching metrics:', error);
        resetMetricsDisplay();
    }
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

async function resetSimulation() {
    invalidatePendingDisplayUpdates();
    await callAPI('/stop');
    invalidatePendingDisplayUpdates();
    isRunning = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    await fetchBoardState();
    await fetchClockAndDay();
    await fetchMetricsDisplay();
}

function stopSimulationWhenLeavingPage() {
    if (isExportingCsv) {
        return;
    }

    const stopUrl = `${API_URL}/stop`;
    isRunning = false;

    if (navigator.sendBeacon) {
        const payload = new Blob(['{}'], { type: 'application/json' });
        navigator.sendBeacon(stopUrl, payload);
        return;
    }

    fetch(stopUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
        keepalive: true
    }).catch(error => console.error('Error stopping simulation on page exit:', error));
}

window.addEventListener('pagehide', stopSimulationWhenLeavingPage);
window.addEventListener('beforeunload', stopSimulationWhenLeavingPage);

// NEW: Start button click - call Backend to start simulation
startBtn.addEventListener('click', function() {
    // NEW: Tell Backend to start the simulation
    callAPI('/start');
    isRunning = true;
    console.log('Kanban simulation started');
    //window.alert('Start button clicked.');
    // NEW: Disable Start button, enable Stop button
    //startBtn.disabled = true;
    pauseBtn.disabled = false;
});

// NEW: Pause button click - call Backend to pause simulation
pauseBtn.addEventListener('click', function() {
    // NEW: Tell Backend to pause the simulation
    callAPI('/pause');
    isRunning = false;
    console.log('Kanban simulation paused');
    //window.alert('Pause button clicked.');
    // NEW: Enable Start button, disable Pause button
    startBtn.disabled = false;
    pauseBtn.disabled = true;
});

// NEW: Reset button - user must hold for 3 seconds (security feature)
stopBtn.addEventListener('mousedown', function() {
    // NEW: Start counting down - if user holds 3 seconds, reset
    holdTimer = setTimeout(async function() {
        await resetSimulation();
        console.log('Kanban simulation reset');
    }, HOLD_DURATION);
});

// NEW: If user releases button before 3 seconds, cancel the reset
stopBtn.addEventListener('mouseup', function() {
    clearTimeout(holdTimer);
});

// NEW: If user moves mouse away from button before 3 seconds, cancel the reset
stopBtn.addEventListener('mouseleave', function() {
    clearTimeout(holdTimer);
});

updateBtn.addEventListener('click', async function() {
    // NEW: Placeholder for future configuration update logic
    //window.alert('Update button clicked.');
    const selectedSpeed = Number(speedInput.value);
    const newconfig = {
        column_0: document.getElementById('column_0').value,
        column_1: document.getElementById('column_1').value,
        column_2: document.getElementById('column_2').value,
        column_3: document.getElementById('column_3').value,
        column_4: document.getElementById('column_4').value,
        column_5: document.getElementById('column_5').value,
        workers_1: document.getElementById('workers_1').value,
        workers_2: document.getElementById('workers_2').value,
        workers_3: document.getElementById('workers_3').value,
        workers_4: document.getElementById('workers_4').value,
        tick_interval: getBackendTickInterval()
    };
    //window.alert('Convig saved');

    if (newconfig.column_0 < 1 || newconfig.column_1 < 1 || newconfig.column_2 < 1 || newconfig.column_3 < 1 || newconfig.column_4 < 1 || newconfig.column_5 < 1 || newconfig.workers_1 < 1 || newconfig.workers_2 < 1 || newconfig.workers_3 < 1 || newconfig.workers_4 < 1 || selectedSpeed < 0.1 || selectedSpeed > 2.0) {
        window.alert('WIP limits and worker counts must be at least 1, and speed must be between 0.1 and 2.0.');
        return;
    }   

    try {
        const response = await fetch(`${API_URL}/update-config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newconfig)
        });

        //window.alert('Configuration update request sent. Waiting for response...');

        const data = await response.json();

        if (data.success){
            console.log('Configuration updated successfully:', data);
            //window.alert('Configuration updated successfully.');
        }

    } catch (error) {
        console.error('Error updating configuration:', error);
        //window.alert('Error updating configuration. Please try again.');
    }


    //window.alert(`Update button clicked. New WIP limits: Backlog=${newconfig.column_0}, Doing=${newconfig.column_1}, Doing 2=${newconfig.column_2}, Done=${newconfig.column_3}, Workers 1=${newconfig.workers_1}, Workers 2=${newconfig.workers_2}`);
});

exportCsvBtn.addEventListener('click', function() {
    isExportingCsv = true;
    window.location.href = `${API_URL}/export/csv`;
    setTimeout(function() {
        isExportingCsv = false;
    }, 2000);
});

// NEW: Automatically fetch board state every 2 seconds to keep UI in sync with Backend
setInterval(fetchBoardState, 500);

// NEW: Automatically fetch clock and day every 1 second
setInterval(fetchClockAndDay, 500);

setInterval(fetchMetricsDisplay, 500);

// NEW: Start with Stop button disabled (simulation must start first)
//stopBtn.disabled = true;
