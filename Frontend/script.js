const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');
const updateBtn = document.getElementById('update-btn');
const columnCountInput = document.getElementById('column-count');
const boardContainer = document.getElementById('kanban-board');

const API_URL = 'http://localhost:5000';
const HOLD_DURATION = 3000;

let isRunning = false;
let holdTimer = null;

const columnDefinitions = [
    { id: 0, name: 'To Do', type: 'queue', badge: 'Input', badgeClass: 'text-bg-info', wipLimit: 9, workers: 0, processingTime: 0 },
    { id: 1, name: 'Analysis', type: 'process', badge: 'Plan', badgeClass: 'text-bg-primary', wipLimit: 4, workers: 2, processingTime: 8 },
    { id: 2, name: 'Development', type: 'process', badge: 'Build', badgeClass: 'text-bg-primary', wipLimit: 5, workers: 2, processingTime: 10 },
    { id: 3, name: 'Review', type: 'process', badge: 'Check', badgeClass: 'text-bg-primary', wipLimit: 4, workers: 1, processingTime: 6 },
    { id: 4, name: 'Testing', type: 'process', badge: 'Verify', badgeClass: 'text-bg-primary', wipLimit: 4, workers: 1, processingTime: 8 },
    { id: 5, name: 'Done', type: 'done', badge: 'Complete', badgeClass: 'text-bg-success', wipLimit: 99, workers: 0, processingTime: 0 }
];

function getColumnKicker(column) {
    if (column.type === 'queue') {
        return 'Queue';
    }
    if (column.type === 'done') {
        return 'Output';
    }
    return 'Active';
}

function renderColumns() {
    boardContainer.innerHTML = '';
    columnCountInput.value = columnDefinitions.length;

    columnDefinitions.forEach(column => {
        const columnWrap = document.createElement('div');
        columnWrap.className = 'kanban-column-wrap';

        const workerInput = column.type === 'process'
            ? `
                <div>
                    <label for="workers_${column.id}" class="form-label mb-1">Worker(s)</label>
                    <input id="workers_${column.id}" class="form-control form-control-sm" type="number" value="${column.workers}" min="1">
                </div>
            `
            : '';
        const settingsPanel = column.type === 'done'
            ? ''
            : `
                <div class="user-inputs column-settings ${column.type === 'process' ? 'two-fields' : ''}">
                    <div>
                        <label for="column_${column.id}" class="form-label mb-1">WIP Limit</label>
                        <input id="column_${column.id}" class="form-control form-control-sm" type="number" value="${column.wipLimit}" min="1">
                        <div class="count"></div>
                    </div>
                    ${workerInput}
                </div>
            `;

        columnWrap.innerHTML = `
            <article class="column kanban-column card border-0 h-100" id="col-${column.id}">
                <div class="card-body p-4">
                    <div class="d-flex align-items-start justify-content-between gap-3 mb-3">
                        <div>
                            <span class="column-kicker">${getColumnKicker(column)}</span>
                            <h2 class="h4 fw-bold mb-0">${column.name}</h2>
                        </div>
                        <span class="badge rounded-pill ${column.badgeClass}">${column.badge}</span>
                    </div>

                    ${settingsPanel}

                    <div class="cards task-list"></div>
                </div>
            </article>
        `;

        boardContainer.appendChild(columnWrap);
    });
}

async function fetchBoardState() {
    try {
        const response = await fetch(`${API_URL}/board`);
        const data = await response.json();
        updateBoardDisplay(data);
    } catch (error) {
        console.error('Error fetching board:', error);
    }
}

async function fetchClockAndDay() {
    try {
        const response = await fetch(`${API_URL}/clock-and-day`);
        const data2 = await response.json();
        document.getElementById('clock').textContent = `Clock: ${parseFloat(data2.clock).toFixed(2)}`;
        document.getElementById('day').textContent = `Day: ${data2.day}`;
    } catch (error) {
        console.error('Error fetching clock and day:', error);
    }
}

function updateBoardDisplay(data) {
    console.log('Board state:', data);

    let workInProgress = 0;

    columnDefinitions.forEach(column => {
        const cardsContainer = document.querySelector(`#col-${column.id} .cards`);
        const columnKey = `column_${column.id}`;
        const tasks = data[columnKey] || [];

        if (column.type !== 'done') {
            workInProgress += tasks.length;
        }

        cardsContainer.innerHTML = '';

        tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = 'card task-card';

            const taskInfo = document.createElement('div');
            taskInfo.className = 'task-info';
            taskInfo.textContent = `Task ${task.id} (${task.created_at}) (${task.status}) (Worker: ${task.worker_task})`;

            const progressTrack = document.createElement('div');
            progressTrack.className = 'progress progress-track';

            const progressFill = document.createElement('div');
            progressFill.className = 'progress-bar progress-fill';
            progressFill.style.width = `${task.progress_percent || 0}%`;

            const progressLabel = document.createElement('span');
            progressLabel.className = 'progress-label';
            progressLabel.textContent = `${Math.round(task.progress_percent || 0)}%`;

            progressTrack.appendChild(progressFill);
            progressTrack.appendChild(progressLabel);
            card.appendChild(taskInfo);
            card.appendChild(progressTrack);
            cardsContainer.appendChild(card);
        });
    });

    document.getElementById('in-progress').textContent = `Work In Progress: ${workInProgress}`;
}

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

function buildConfigPayload() {
    return {
        columns: columnDefinitions.map(column => {
            const wipInput = document.getElementById(`column_${column.id}`);
            const workerInput = document.getElementById(`workers_${column.id}`);

            return {
                name: column.name,
                type: column.type,
                wip_limit: wipInput ? wipInput.value : column.wipLimit,
                workers: workerInput ? workerInput.value : 0,
                processing_time: column.processingTime
            };
        })
    };
}

function hasInvalidConfig(config) {
    return config.columns.some(column => {
        const wipLimit = Number(column.wip_limit);
        const workers = Number(column.workers);
        return wipLimit < 1 || (column.type === 'process' && workers < 1);
    });
}

startBtn.addEventListener('click', function() {
    callAPI('/start');
    isRunning = true;
    console.log('Kanban simulation started');
    window.alert('Start button clicked.');
    startBtn.disabled = true;
    stopBtn.disabled = false;
});

stopBtn.addEventListener('click', function() {
    callAPI('/stop');
    isRunning = false;
    console.log('Kanban simulation stopped');
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

resetBtn.addEventListener('mousedown', function() {
    holdTimer = setTimeout(function() {
        callAPI('/reset');
        isRunning = false;
        console.log('Kanban simulation reset');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }, HOLD_DURATION);
});

resetBtn.addEventListener('mouseup', function() {
    clearTimeout(holdTimer);
});

resetBtn.addEventListener('mouseleave', function() {
    clearTimeout(holdTimer);
});

updateBtn.addEventListener('click', async function() {
    const newconfig = buildConfigPayload();

    if (hasInvalidConfig(newconfig)) {
        window.alert('WIP limits and worker counts must be at least 1.');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/update-config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newconfig)
        });

        const data = await response.json();
        console.log('Configuration update response:', data);
        window.alert('Configuration updated successfully.');
    } catch (error) {
        console.error('Error updating configuration:', error);
        window.alert('Error updating configuration. Please try again.');
    }
});

renderColumns();
setInterval(fetchBoardState, 100);
setInterval(fetchClockAndDay, 100);
stopBtn.disabled = true;
