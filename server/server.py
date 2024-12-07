import sqlite3
import os
import socket
import json
import socket
import json

class DataBaseManager:
    USERS_DB = "users.db"

    # Check if users.db already exists
    if os.path.exists(USERS_DB):
        print("users.db found")
        users_conn = sqlite3.connect(USERS_DB)
        users_cursor = users_conn.cursor()
    else:
        users_conn = sqlite3.connect(USERS_DB)
        users_cursor = users_conn.cursor()

        users_conn.execute('''
            CREATE TABLE Users (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE,
                Password TEXT NOT NULL,
                Coins INTEGER DEFAULT 50,
                RankPoints INTEGER DEFAULT 100
            )
        ''')
        print("new users.db created")

    def add_user(self, name, password):
        try:
            # Check if username is taken
            self.users_cursor.execute(f'''
                SELECT ID FROM Users WHERE Name = "{name}"
            ''')
            if self.users_cursor.fetchone():
                return False  # User already exists

            # Add new user
            self.users_conn.execute(f'''
                INSERT INTO Users (Name, Password)
                VALUES ("{name}", "{password}")
            ''')
            self.users_conn.commit()
            return True     # User created

        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def login(self, name, password):
        try:
            # Fetch user details if credentials match
            self.users_cursor.execute(f'''
                SELECT ID, Name, Coins, RankPoints FROM Users
                WHERE Name = "{name}" AND Password = "{password}"
            ''')
            result = self.users_cursor.fetchone()
            if result:
                return {
                    "ID": result[0],
                    "Name": result[1],
                    "Coins": result[2],
                    "RankPoints": result[3]
                }
            return None  # Login failed
        except Exception as e:
            print(f"Error loging in: {e}")
            return None

class Server:
    data_base_manager = DataBaseManager()
    def __init__(self):
        pass
    def start(self, host='127.0.0.1', port=65432):    # starting server / infinit while loop
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen()  # Start listening for incoming connections
        print(f"Server listening on {host}:{port}")

        while True:
            # Accept a new client
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")

            # Receive data
            data = conn.recv(1024).decode('utf-8')
            print(f"Received from {addr}")

            # Process packet and respond
            json_data = json.loads(data)
            packet_type = json_data['type']
            response = None
            match packet_type:
                case "login":
                    response = self.data_base_manager.login(json_data['username'], json_data['password'])
                case "register":
                    response = self.data_base_manager.add_user(json_data['username'], json_data['password'])

            response = {f"{packet_type}": response}
            conn.sendall(json.dumps(response).encode('utf-8'))
            conn.close()  # Close connection

def main():
    server = Server()
    server.start()

main()
