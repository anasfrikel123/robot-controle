import socket
import ast
import time

# Set up the server socket
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 12345

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on {HOST}:{PORT}")

# Function to process joystick data
def process_joystick_data(data):
    # Convert the string representation of the dictionary back to a dictionary
    joystick_data = ast.literal_eval(data.decode('utf-8'))
    
    # Extract buttons and axes
    buttons = joystick_data['buttons']
    axes = joystick_data['axes']
    
    # Here you can add your robot control logic based on the joystick data
    # For example:
    # - Use axes[0] and axes[1] for movement (left stick)
    # - Use axes[2] and axes[3] for camera control (right stick)
    # - Use buttons for specific actions
    
    print(f"Received data - Buttons: {buttons}, Axes: {axes}")

# Main loop to receive and process joystick data
try:
    while True:
        # Accept client connection
        client_socket, client_address = server_socket.accept()
        print(f"Connected to client: {client_address}")
        
        while True:
            # Receive data from the client
            data = client_socket.recv(1024)
            if not data:
                break
                
            # Process the received data
            process_joystick_data(data)
            
            time.sleep(0.1)  # Small delay to prevent CPU overload
            
except KeyboardInterrupt:
    print("Exiting...")
    server_socket.close() 