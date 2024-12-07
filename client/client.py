import socket
import json
import os

host = '127.0.0.1'
port = 65432


def send_dict_as_json_to_server(dict_data):  # takes a dictionary
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Convert dict to JSON
    json_data = json.dumps(dict_data)

    # Send the JSON string
    client_socket.sendall(json_data.encode('utf-8'))

    # Receive response from the server
    response = client_socket.recv(1024).decode('utf-8')
    client_socket.close()
    return response


def login(username, password):
    dict_data = {"type": "login", "username": username, "password": password}
    return send_dict_as_json_to_server(dict_data)


def register(username, password):
    dict_data = {"type": "register", "username": username, "password": password}
    return send_dict_as_json_to_server(dict_data)


if __name__ == "__main__":
    while True:
        print("\n")
        print("COMMANDS: LOGIN, REGISTER")
        command = input("command: ")

        if command.lower() == "login":
            username = input("username: ")
            password = input("password: ")
            print(login(username, password))

        elif command.lower() == "register":
            username = input("username: ")
            password = input("password: ")
            print(register(username, password))
