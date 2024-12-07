import socket
import json

def start_server(host='127.0.0.1', port=65432):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()  # Start listening for incoming connections
    print(f"Server listening on {host}:{port}")

    while True:
        conn, addr = server_socket.accept()  # Accept a new client
        print(f"Connection from {addr}")

        # Receive data
        data = conn.recv(1024).decode('utf-8')
        print(f"Received from {addr}: {data}")

        # Process and respond
        try:
            deserialized_data = json.loads(data)
            response = {"messaase": "Processed", "data": deserialized_data}
        except json.JSONDecodeError:
            response = {"error": "Invalid JSON"}

        conn.sendall(json.dumps(response).encode('utf-8'))  # Send response
        conn.close()  # Close the connection

if __name__ == "__main__":
    start_server()
