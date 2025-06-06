import os
from flask import Flask, render_template, Response, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit
from camera import CameraHandler
from serial_handler import SerialHandler
import threading
import time
import cv2
import numpy as np
import serial
import json

# Flask app setup
app = Flask(__name__, static_folder='../static', template_folder='../static')
app.config['SECRET_KEY'] = 'robot_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Camera and Serial Handler initialization
camera_handler = CameraHandler()
serial_handler = SerialHandler()

# Initialize serial connection to Arduino
try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
except:
    print("Warning: Could not connect to Arduino")
    arduino = None

# Initialize camera
try:
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
except:
    print("Warning: Could not initialize camera")
    camera = None

# Start camera and serial connection in background
@app.before_first_request
def initialize_hardware():
    threading.Thread(target=camera_handler.start, daemon=True).start()
    threading.Thread(target=serial_handler.connect, daemon=True).start()

# MJPEG video stream endpoint
def gen_camera_stream():
    while True:
        frame = camera_handler.get_jpeg_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # ~30 FPS

@app.route('/video_feed')
def video_feed():
    return Response(gen_camera_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Serve index.html
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static files (css, js)
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

# WebSocket events for real-time control and data
@socketio.on('connect')
def handle_connect():
    emit('status', {'connected': True})

@socketio.on('move')
def handle_move(data):
    if arduino:
        try:
            left = int(data.get('left', 0))
            right = int(data.get('right', 0))
            command = f"M{left},{right}\n"
            arduino.write(command.encode())
        except Exception as e:
            print(f"Error sending move command: {e}")

@socketio.on('stop')
def handle_stop():
    if arduino:
        try:
            arduino.write(b"S\n")
        except Exception as e:
            print(f"Error sending stop command: {e}")

@socketio.on('servo')
def handle_servo(data):
    if arduino:
        try:
            angle = int(data.get('angle', 90))
            command = f"P{angle}\n"
            arduino.write(command.encode())
        except Exception as e:
            print(f"Error sending servo command: {e}")

def read_sensor_data():
    while True:
        if arduino:
            try:
                if arduino.in_waiting:
                    line = arduino.readline().decode().strip()
                    if line.startswith('S'):
                        data = line[1:].split(',')
                        if len(data) == 2:
                            socketio.emit('sensor_data', {
                                'light': int(data[0]),
                                'distance': float(data[1])
                            })
            except Exception as e:
                print(f"Error reading sensor data: {e}")
        time.sleep(0.1)

# Background thread to emit sensor data periodically
def sensor_data_broadcast():
    while True:
        light, distance = serial_handler.get_sensor_data()
        socketio.emit('sensor_data', {'light': light, 'distance': distance})
        time.sleep(0.5)

threading.Thread(target=sensor_data_broadcast, daemon=True).start()

if __name__ == '__main__':
    # Start sensor reading thread
    sensor_thread = threading.Thread(target=read_sensor_data, daemon=True)
    sensor_thread.start()
    
    # Start Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 