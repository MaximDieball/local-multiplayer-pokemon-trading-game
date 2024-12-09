import sqlite3
import os
import socket
import json


class DataBaseManager:
    USERS_DB = "users.db"
    CARD_DB = "pokemon_cards.db"
    CARDS_OWNED_DB = "cards_owned.db"
    PACKS_DB = "packs.db"

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
                Username TEXT NOT NULL UNIQUE,
                Password TEXT NOT NULL,
                Balance INTEGER DEFAULT 50,
                RankPoints INTEGER DEFAULT 100
            )
        ''')
        print("new users.db created")

    # Check if card database exists
    if os.path.exists(CARD_DB):
        print("pokemon_cards.db found")
        cards_conn = sqlite3.connect(CARD_DB)
        cards_cursor = cards_conn.cursor()
    else:
        print("NO CARD DATABASE -> this will likely crash the server")

    # Check if cards owned database exists
    if os.path.exists(CARDS_OWNED_DB):
        print("cards_owned.db found")
        cards_owned_conn = sqlite3.connect(CARDS_OWNED_DB)
        cards_owned_cursor = cards_owned_conn.cursor()
    else:
        cards_owned_conn = sqlite3.connect(CARDS_OWNED_DB)
        cards_owned_cursor = cards_owned_conn.cursor()

        users_conn.execute('''
            CREATE TABLE CardsOwned (
                UserID INTEGER,
                CardID INTEGER
            )
        ''')
        print("new cards_owned.db created")

    # Check if cards packs database exists
    if os.path.exists(PACKS_DB):
        print("packs.db found")
        packs_conn = sqlite3.connect(PACKS_DB)
        packs_cursor = packs_conn.cursor()
    else:
        packs_conn = sqlite3.connect(PACKS_DB)
        packs_cursor = packs_conn.cursor()

        packs_conn.execute('''
            CREATE TABLE Packs (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE,
                Price INTEGER,
                CommonChance INTEGER,
                UncommonChance INTEGER,
                RareChance INTEGER,
                HoloRareChance INTEGER
            )
        ''')
        packs_conn.execute(f'''
            INSERT INTO Packs (Name, Price, CommonChance, UncommonChance, RareChance, HoloRareChance)
            VALUES ("CommonPack", 200, 0.90, 0.80, 0.99, 1.00)
        ''')    # CommonChange = 90% / UncommonChange = 8% / RareChance = 1.98% / HoloRareChance = 0.02%
        packs_conn.execute(f'''
            INSERT INTO Packs (Name, Price, CommonChance, UncommonChance, RareChance, HoloRareChance)
            VALUES ("RarePack", 600, 0.60, 0.60, 0.80, 1.00)
        ''')    # CommonChange = 60% / UncommonChange = 24% / RareChance = 12.8% / HoloRareChance = 3.2%
        packs_conn.execute(f'''
            INSERT INTO Packs (Name, CommonChance, UncommonChance, RareChance, HoloRareChance)
            VALUES ("SuperRarePack", 3000, 0.40, 0.50, 0.60, 1.00)
        ''')    # CommonChange = 40% / UncommonChange = 30% / RareChance = 18% / HoloRareChance = 12%

        print("new packs.db created")

    def add_user(self, name, password):
        try:
            # Check if username is taken
            self.users_cursor.execute(f'''
                SELECT ID FROM Users WHERE Username = "{name}"
            ''')
            if self.users_cursor.fetchone():
                return False  # User already exists

            # Add new user
            self.users_conn.execute(f'''
                INSERT INTO Users (Username, Password)
                VALUES ("{name}", "{password}")
            ''')
            self.users_conn.commit()
            return True     # User created

        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def get_none_credential_data_by_id(self, id):
        try:
            self.users_cursor.execute(f'''
                SELECT ID, Username, Balance, RankPoints FROM Users
                WHERE ID = "{id}"
            ''')
            result = self.users_cursor.fetchone()
            return {
                "ID": result[0],
                "Username": result[1],
                "Balance": result[2],
                "RankPoints": result[3]
            }
        except Exception as e:
            print(f"Error getting none credential data: {e}")
            return None

    def transfer_balance_by_id(self, sender_id, receiver_id, amount):
        sender_data = self.get_none_credential_data_by_id(sender_id)
        receiver_data = self.get_none_credential_data_by_id(receiver_id)
        if not sender_data or not receiver_data:
            return None
        if sender_data['Balance'] - amount < 0 or amount <= 0:    # check for not valid inputs
            return None
        sender_balance = sender_data['Balance'] - amount    # calculate new bank values
        receiver_balance = receiver_data['Balance'] + amount

        self.users_cursor.execute(f'''
                        UPDATE Users
                        SET Balance = {sender_balance}
                        WHERE ID = "{sender_id}"
                    ''')
        self.users_cursor.execute(f'''
                        UPDATE Users
                        SET Balance = {receiver_balance}
                        WHERE ID = "{receiver_id}"
                    ''')
        self.users_conn.commit()
        return True

    def add_balance_by_id(self, id, amount):
        print(f"add_balance_by_id({id}, {amount})")
        amount = int(amount)
        data = self.get_none_credential_data_by_id(id)
        balance = data['Balance'] + amount
        if balance < 0:
            return None
        self.users_cursor.execute(f'''
                        UPDATE Users
                        SET Balance = {balance}
                        WHERE ID = "{id}"
                    ''')
        self.users_conn.commit()
        return balance

    def add_ranked_points_by_id(self, id, amount):
        data = self.get_none_credential_data_by_id(id)
        ranked_points = data['RankPoints'] + amount
        if ranked_points < 0:
            return None
        self.users_cursor.execute(f'''
                        UPDATE Users
                        SET RankPoints = {ranked_points}
                        WHERE ID = "{id}"
                    ''')
        self.users_conn.commit()
        return ranked_points

    def login(self, name, password):
        try:
            # Fetch user details if credentials match
            self.users_cursor.execute(f'''
                SELECT ID, Username, Balance, RankPoints FROM Users
                WHERE Username = "{name}" AND Password = "{password}"
            ''')
            result = self.users_cursor.fetchone()
            if result:
                return {
                    "ID": result[0],
                    "Username": result[1],
                    "Balance": result[2],
                    "RankPoints": result[3]
                }
            return {    # Login failed
                "ID": None,
                "Username": None,
                "Balance": None,
                "RankPoints": None
            }

        except Exception as e:
            print(f"Error logging in: {e}")
            return {  # Login failed
                "ID": None,
                "Username": None,
                "Balance": None,
                "RankPoints": None
            }


class Server:
    data_base_manager = DataBaseManager()

    def __init__(self):
        pass

    def start(self, host='127.0.0.1', port=65432):    # starting server / infinite while loop
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen()  # Start listening for incoming connections
        print(f"Server listening on {host}:{port}")

        while True:
            # Accept a new client
            conn, addr = server_socket.accept()

            # Receive data
            data = conn.recv(1024).decode('utf-8')

            # Process packet and respond
            json_data = json.loads(data)
            packet_type = json_data['type']
            response = None
            print(f"RECEIVED: {json_data} FROM {addr}")
            match packet_type:
                case "login":
                    response = self.data_base_manager.login(json_data['username'], json_data['password'])
                case "register":
                    response = self.data_base_manager.add_user(json_data['username'], json_data['password'])
                case "getData":
                    response = self.data_base_manager.get_none_credential_data_by_id(json_data['id'])
                case "deposit":
                    response = self.data_base_manager.add_balance_by_id(json_data['id'], json_data['amount'])
                case "withdraw":
                    response = self.data_base_manager.add_balance_by_id(json_data['id'], json_data['amount'] * -1)
                case "transfer":
                    response = self.data_base_manager.transfer_balance_by_id(json_data['sender_id'],
                                                                             json_data['receiver_id'],
                                                                             json_data['amount'])

            conn.sendall(json.dumps(response).encode('utf-8'))
            conn.close()  # Close connection

            print("send json_data: ", json.dumps(response).encode('utf-8'))


def main():
    server = Server()
    server.start()


main()
