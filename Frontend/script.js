const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');  

let isRunning = false;
let holdTimer = null;
const holdDuration = 2000; // Duration in milliseconds to consider as a long press currently 2 secs

startBtn.addEventListener('click', function() {
    isRunning = true;
    console.log('Kanban simulation started');
    startBtn.disabled = true;
    stopBtn.disabled = false;
});

stopBtn.addEventListener('click', function() {
    isRunning = false;
    console.log('Kanban simulation stopped');
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

resetBtn.addEventListener('mousedown', function() {
    holdTimer = setTimeout(function() {
        isRunning = false;
        console.log('Kanban simulation reset');
        document.querySelectorAll('.cards').forEach(column => {
            column.innerHTML = '';
        });
    startBtn.disabled = false;
    stopBtn.disabled = true;
    }, holdDuration);
});

resetBtn.addEventListener('mouseup', function() {
    clearTimeout(holdTimer);
});

resetBtn.addEventListener('mouseleave', function() {
    clearTimeout(holdTimer);
});

stopBtn.disabled = true;