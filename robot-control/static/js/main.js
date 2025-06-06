// main.js - Robot Control Panel Frontend

// --- Socket.IO Setup ---
const socket = io();

// --- UI Elements ---
const lightLevelEl = document.getElementById('light-level');
const distanceEl = document.getElementById('distance');
const servoAngleInput = document.getElementById('servo-angle');
const servoAngleValue = document.getElementById('servo-angle-value');
const stopBtn = document.getElementById('stop-btn');
const joystickContainer = document.getElementById('joystick-container');

// --- State ---
let isMobile = /Mobi|Android/i.test(navigator.userAgent);
let currentLeft = 0;
let currentRight = 0;

// --- Joystick Controls (Mobile) ---
function setupJoystick() {
    if (typeof nipplejs !== 'undefined') {
        const joystick = nipplejs.create({
            zone: joystickContainer,
            mode: 'static',
            position: { left: '50%', top: '50%' },
            color: '#00b894',
            size: 120
        });
        joystick.on('move', (evt, data) => {
            if (data && data.distance) {
                // Convert angle/distance to left/right motor speeds
                const maxSpeed = 255;
                const angle = data.angle ? data.angle.degree : 0;
                const distance = Math.min(data.distance, 100) / 100;
                let left = 0, right = 0;
                if (angle >= 45 && angle < 135) { // Up
                    left = right = maxSpeed * distance;
                } else if (angle >= 135 && angle < 225) { // Left
                    left = -maxSpeed * distance;
                    right = maxSpeed * distance;
                } else if (angle >= 225 && angle < 315) { // Down
                    left = right = -maxSpeed * distance;
                } else { // Right
                    left = maxSpeed * distance;
                    right = -maxSpeed * distance;
                }
                sendMove(left, right);
            }
        });
        joystick.on('end', () => {
            sendStop();
        });
    } else {
        joystickContainer.innerHTML = '<div style="color:#b2bec3">Joystick not available</div>';
    }
}

// --- Keyboard Controls (Desktop) ---
function setupKeyboard() {
    document.addEventListener('keydown', (e) => {
        let left = 0, right = 0, speed = 200;
        switch (e.key.toLowerCase()) {
            case 'w': case 'arrowup':
                left = right = speed; break;
            case 's': case 'arrowdown':
                left = right = -speed; break;
            case 'a': case 'arrowleft':
                left = -speed; right = speed; break;
            case 'd': case 'arrowright':
                left = speed; right = -speed; break;
            default: return;
        }
        sendMove(left, right);
    });
    document.addEventListener('keyup', (e) => {
        sendStop();
    });
}

// --- Servo Angle Control ---
servoAngleInput.addEventListener('input', () => {
    const angle = parseInt(servoAngleInput.value);
    servoAngleValue.textContent = angle + '°';
    socket.emit('servo', { angle });
});

// --- Stop Button ---
stopBtn.addEventListener('click', sendStop);

// --- Send Move/Stop Commands ---
function sendMove(left, right) {
    if (left !== currentLeft || right !== currentRight) {
        socket.emit('move', { left: Math.round(left), right: Math.round(right) });
        currentLeft = left; currentRight = right;
    }
}
function sendStop() {
    socket.emit('stop');
    currentLeft = 0; currentRight = 0;
}

// --- Sensor Data Updates ---
socket.on('sensor_data', data => {
    if (typeof data.light !== 'undefined') lightLevelEl.textContent = data.light;
    if (typeof data.distance !== 'undefined') distanceEl.textContent = data.distance.toFixed(1);
});

// --- Connection Status ---
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// --- Initialization ---
window.addEventListener('DOMContentLoaded', () => {
    if (isMobile) {
        setupJoystick();
        document.getElementById('keyboard-hint').style.display = 'none';
    } else {
        setupKeyboard();
        joystickContainer.style.display = 'none';
    }
    // Request sensor data periodically
    setInterval(() => {
        socket.emit('get_sensor_data');
    }, 500);
}); 