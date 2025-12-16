const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');  

let isRunning = false;

startBtn.addEventListener('click', function() {
    isRunning = true;
    console.log()