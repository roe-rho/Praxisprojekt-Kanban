const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');  

let isRunning = false;

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

resetBtn.addEventListener('click', function() {
    isRunning = false;
    console.log('Kanban simulation reset');
    document.querySelectorAll('.cards').forEach(column => {
        column.innerHTML = '';
    });
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

stopBtn.disabled = true;