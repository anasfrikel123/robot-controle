import pygame
import socket
import time

# Initialize pygame and joystick
pygame.init()
pygame.joystick.init()

# Set up the socket connection to Raspberry Pi
RASPBERRY_PI_IP = '192.168.11.107'  # Replace with your Raspberry Pi's IP
PORT = 12345

# Create a socket object and connect to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((RASPBERRY_PI_IP, PORT))

# Wait for the joystick to initialize
if pygame.joystick.get_count() == 0:
    print("No joystick connected!")
    pygame.quit()
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Controller connected: {joystick.get_name()}")

# Function to get joystick data
def get_joystick_data():
    # Get joystick button and axis states
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    
    # Format the data to send it
    data = {
        'buttons': buttons,
        'axes': axes
    }
    return data

# Main loop to send joystick data continuously
try:
    while True:
        pygame.event.pump()  # Process events
        joystick_data = get_joystick_data()  # Get joystick data
        
        # Send the joystick data to the Raspberry Pi as a string
        client_socket.send(str(joystick_data).encode('utf-8'))
        
        time.sleep(0.1)  # Small delay to prevent flooding the server with data

except KeyboardInterrupt:
    print("Exiting...")
    client_socket.close()
    pygame.quit()
