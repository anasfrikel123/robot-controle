"""
Serial Handler for Robot Control

This module handles serial communication with the Arduino controller.
It sends commands to control the robot and receives sensor data.
"""

import serial
import threading
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SerialHandler:
    """Handles serial communication with Arduino."""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        """
        Initialize the serial connection.
        
        Args:
            port (str): Serial port name
            baudrate (int): Baud rate for serial communication
            timeout (float): Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.is_connected = False
        self.running = False
        self.read_thread = None
        
        # Callbacks
        self.on_sensor_data = None
        self.on_command_ack = None
        
        # Buffer for incoming data
        self.buffer = ""
        
        # Last received sensor data
        self.light_level = 0
        self.distance = 0.0
        
    def connect(self):
        """Establish connection to the Arduino."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            self.is_connected = True
            self.running = True
            
            # Start the read thread
            self.read_thread = threading.Thread(target=self._read_serial)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            logger.info(f"Connected to Arduino on {self.port}")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the Arduino."""
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            logger.info("Disconnected from Arduino")
    
    def _read_serial(self):
        """Read data from the serial port in a separate thread."""
        while self.running:
            if not self.serial_conn or not self.serial_conn.is_open:
                time.sleep(0.1)
                continue
                
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8')
                    self.buffer += data
                    self._process_buffer()
            except Exception as e:
                logger.error(f"Error reading from serial port: {e}")
                time.sleep(0.1)
    
    def _process_buffer(self):
        """Process the data buffer to extract complete messages."""
        while '<' in self.buffer and '>' in self.buffer:
            start = self.buffer.find('<')
            end = self.buffer.find('>', start)
            
            if start >= 0 and end >= 0:
                message = self.buffer[start+1:end]
                self.buffer = self.buffer[end+1:]
                self._parse_message(message)
            else:
                break
    
    def _parse_message(self, message):
        """Parse a message from the Arduino."""
        parts = message.split(',')
        
        if not parts:
            return
            
        message_type = parts[0]
        
        if message_type == 'SEN' and len(parts) >= 3:
            # Sensor data message
            try:
                self.light_level = int(parts[1])
                self.distance = float(parts[2])
                
                if self.on_sensor_data:
                    self.on_sensor_data(self.light_level, self.distance)
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing sensor data: {e}")
        
        elif message_type == 'ACK' and len(parts) >= 2:
            # Command acknowledgment
            command = parts[1]
            if self.on_command_ack:
                self.on_command_ack(command, parts[2:])
    
    def send_command(self, command):
        """
        Send a command to the Arduino.
        
        Args:
            command (str): Command string without the markers
            
        Returns:
            bool: True if command was sent, False otherwise
        """
        if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Cannot send command: Not connected to Arduino")
            return False
            
        try:
            # Add markers to the command
            full_command = f"<{command}>\n"
            self.serial_conn.write(full_command.encode('utf-8'))
            logger.debug(f"Sent command: {command}")
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
    
    def set_motor_speed(self, left_speed, right_speed):
        """
        Set the speed of both motors.
        
        Args:
            left_speed (int): Speed for left motor (-255 to 255)
            right_speed (int): Speed for right motor (-255 to 255)
            
        Returns:
            bool: True if command was sent, False otherwise
        """
        # Ensure speeds are within valid range
        left_speed = max(-255, min(255, left_speed))
        right_speed = max(-255, min(255, right_speed))
        
        command = f"MOV,{left_speed},{right_speed}"
        return self.send_command(command)
    
    def stop_motors(self):
        """
        Stop both motors.
        
        Returns:
            bool: True if command was sent, False otherwise
        """
        command = "STP"
        return self.send_command(command)
    
    def get_sensor_data(self):
        """
        Get the latest sensor data.
        
        Returns:
            tuple: (light_level, distance)
        """
        return (self.light_level, self.distance)


# Example usage
if __name__ == "__main__":
    # For testing
    handler = SerialHandler()
    
    def on_sensor_data(light, distance):
        print(f"Light: {light}, Distance: {distance} cm")
    
    handler.on_sensor_data = on_sensor_data
    
    if handler.connect():
        try:
            print("Connected to Arduino. Press Ctrl+C to exit.")
            
            # Move forward
            handler.set_motor_speed(150, 150)
            time.sleep(2)
            
            # Stop
            handler.stop_motors()
            
            # Keep running to receive sensor data
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            handler.disconnect()
    else:
        print("Failed to connect to Arduino.")
