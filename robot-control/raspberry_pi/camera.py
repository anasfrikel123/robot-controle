"""
Camera Handler for Robot Control

This module handles the Raspberry Pi camera and servo control for camera movement.
It captures video frames and provides methods to control the camera servo.
"""

import cv2
import threading
import time
import logging
import numpy as np
import RPi.GPIO as GPIO
from io import BytesIO
from picamera2 import Picamera2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CameraHandler:
    """Handles Raspberry Pi camera operations and servo control."""
    
    def __init__(self, servo_pin=18, resolution=(640, 480), framerate=20):
        """
        Initialize the camera and servo.
        
        Args:
            servo_pin (int): GPIO pin for servo control
            resolution (tuple): Camera resolution (width, height)
            framerate (int): Camera framerate
        """
        self.servo_pin = servo_pin
        self.resolution = resolution
        self.framerate = framerate
        
        # Camera setup
        self.camera = None
        self.is_running = False
        self.frame = None
        self.last_frame_time = 0
        self.frame_lock = threading.Lock()
        self.camera_thread = None
        
        # Servo setup
        self.servo_angle = 90  # Middle position (0-180)
        
        # Initialize GPIO for servo
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.servo_pwm = GPIO.PWM(self.servo_pin, 50)  # 50Hz frequency
        self.servo_pwm.start(0)
        
        # Set initial servo position
        self.set_servo_angle(self.servo_angle)
        
    def start(self):
        """Start the camera capture."""
        if self.is_running:
            return
            
        try:
            # Initialize camera
            self.camera = Picamera2()
            config = self.camera.create_still_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self.camera.configure(config)
            self.camera.start()
            
            # Wait for camera to initialize
            time.sleep(2)
            
            self.is_running = True
            
            # Start capture thread
            self.camera_thread = threading.Thread(target=self._capture_loop)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
            logger.info("Camera started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """Stop the camera capture."""
        self.is_running = False
        
        if self.camera_thread:
            self.camera_thread.join(timeout=1.0)
            
        if self.camera:
            self.camera.stop()
            self.camera.close()
            self.camera = None
            
        # Clean up servo
        self.servo_pwm.stop()
        GPIO.cleanup(self.servo_pin)
        
        logger.info("Camera stopped")
    
    def _capture_loop(self):
        """Continuously capture frames from the camera."""
        while self.is_running:
            try:
                # Capture a frame
                frame = self.camera.capture_array()
                
                # Update the frame with thread safety
                with self.frame_lock:
                    self.frame = frame
                    self.last_frame_time = time.time()
                    
            except Exception as e:
                logger.error(f"Error capturing frame: {e}")
                time.sleep(0.1)
    
    def get_frame(self):
        """
        Get the latest camera frame.
        
        Returns:
            numpy.ndarray: The latest camera frame, or None if no frame is available
        """
        with self.frame_lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
    
    def get_jpeg_frame(self):
        """
        Get the latest camera frame as JPEG bytes.
        
        Returns:
            bytes: JPEG encoded frame, or None if no frame is available
        """
        frame = self.get_frame()
        if frame is None:
            return None
            
        # Convert frame to JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    
    def set_servo_angle(self, angle):
        """
        Set the servo angle.
        
        Args:
            angle (int): Angle in degrees (0-180)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure angle is within valid range
            angle = max(0, min(180, angle))
            
            # Convert angle to duty cycle (0.5ms to 2.5ms)
            # 0 degrees = 2.5% duty cycle
            # 180 degrees = 12.5% duty cycle
            duty_cycle = 2.5 + (angle / 180.0) * 10.0
            
            self.servo_pwm.ChangeDutyCycle(duty_cycle)
            self.servo_angle = angle
            
            # Small delay to allow servo to move
            time.sleep(0.1)
            
            # Stop PWM to prevent jitter
            self.servo_pwm.ChangeDutyCycle(0)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting servo angle: {e}")
            return False
    
    def move_servo_relative(self, delta):
        """
        Move the servo by a relative amount.
        
        Args:
            delta (int): Change in angle (-180 to 180)
            
        Returns:
            bool: True if successful, False otherwise
        """
        new_angle = self.servo_angle + delta
        return self.set_servo_angle(new_angle)
    
    def get_servo_angle(self):
        """
        Get the current servo angle.
        
        Returns:
            int: Current servo angle (0-180)
        """
        return self.servo_angle


# Example usage
if __name__ == "__main__":
    # For testing
    camera_handler = CameraHandler()
    
    if camera_handler.start():
        try:
            print("Camera started. Press Ctrl+C to exit.")
            
            # Move servo to different positions
            print("Moving servo to 45 degrees")
            camera_handler.set_servo_angle(45)
            time.sleep(1)
            
            print("Moving servo to 135 degrees")
            camera_handler.set_servo_angle(135)
            time.sleep(1)
            
            print("Moving servo back to 90 degrees")
            camera_handler.set_servo_angle(90)
            time.sleep(1)
            
            # Display video feed
            while True:
                frame = camera_handler.get_frame()
                if frame is not None:
                    cv2.imshow('Camera Feed', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                time.sleep(0.03)  # ~30 FPS
                
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            camera_handler.stop()
            cv2.destroyAllWindows()
    else:
        print("Failed to start camera.")
