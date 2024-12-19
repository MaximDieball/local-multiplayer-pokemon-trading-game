import sqlite3
import os
import socket
import json
import random
import zlib

class DataBaseManager:
    USERS_DB = "users.db"
    CARD_DB = "pokemon_cards.db"
    CARDS_OWNED_DB = "cards_owned.db"
    PACKS_DB = "packs.db"
    MARKETPLACE_DB = "marketplace.db"

    # Check if users.db already exists and create a new users.db database if needed
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

    # Check if cards owned database exists and create a new cards_owned.db database if not
    if os.path.exists(CARDS_OWNED_DB):
        print("cards_owned.db found")
        cards_owned_conn = sqlite3.connect(CARDS_OWNED_DB)
        cards_owned_cursor = cards_owned_conn.cursor()
    else:
        cards_owned_conn = sqlite3.connect(CARDS_OWNED_DB)
        cards_owned_cursor = cards_owned_conn.cursor()

        cards_owned_conn.execute('''
            CREATE TABLE CardsOwned (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID INTEGER,
                CardID INTEGER
            )
        ''')
        cards_owned_conn.commit()
        print("new cards_owned.db created")

    # Check if marketplace.db database exists and create a new marketplace.db database if not
    if os.path.exists(MARKETPLACE_DB):
        print("marketplace.db found")
        marketplace_conn = sqlite3.connect(MARKETPLACE_DB)
        marketplace_cursor = marketplace_conn.cursor()
    else:
        marketplace_conn = sqlite3.connect(MARKETPLACE_DB)
        marketplace_cursor = marketplace_conn.cursor()

        marketplace_conn.execute('''
            CREATE TABLE Marketplace (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID INTEGER,
                CardID INTEGER,
                Price INTEGER
            )
        ''')
        marketplace_conn.commit()
        print("new marketplace.db created")

    # Check if cards packs database exists and create a new packs.db database if not
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
            INSERT INTO Packs (Name, Price, CommonChance, UncommonChance, RareChance, HoloRareChance)
            VALUES ("SuperRarePack", 3000, 0.40, 0.50, 0.60, 1.00)
        ''')    # CommonChange = 40% / UncommonChange = 30% / RareChance = 18% / HoloRareChance = 12%
        packs_conn.commit()
        print("new packs.db created")

    def add_user(self, name, password):
        """
        Add a new user to the Users table.

        Args:
            name (str): The username of the new user.
            password (str): The password for the new user.

        Returns:
            bool: True if the user is successfully added, False if the username already exists or an error occurs.
        """
        try:
            # Check if the username already exists in the Users table
            self.users_cursor.execute(f'''
                SELECT ID FROM Users WHERE Username = "{name}"
            ''')
            if self.users_cursor.fetchone():
                print(f"Error: Username '{name}' is already taken.")
                return False  # Username is already in use

            # Insert the new user into the Users table
            self.users_conn.execute(f'''
                INSERT INTO Users (Username, Password)
                VALUES ("{name}", "{password}")
            ''')
            self.users_conn.commit()  # Commit the changes to the database
            print(f"User '{name}' successfully added.")
            return True

        except Exception as e:
            # Handle any exception that occurs during the operation
            print(f"Error adding user: {e}")
            return False

    def get_none_credential_data_by_id(self, id):
        """
        Retrieve non-credential data (ID, Username, Balance, RankPoints) for a user by their ID.

        Args:
            id (int): The ID of the user to retrieve.

        Returns:
            dict: A dictionary containing the user's non-credential data if found, or None if an error occurs.
        """
        try:
            # Query the Users table to retrieve non-credential data for the given user ID
            self.users_cursor.execute(f'''
                SELECT ID, Username, Balance, RankPoints FROM Users
                WHERE ID = "{id}"
            ''')
            result = self.users_cursor.fetchone()

            # Return the user's data if found
            if result:
                return {
                    "ID": result[0],
                    "Username": result[1],
                    "Balance": result[2],
                    "RankPoints": result[3]
                }
            else:
                print(f"User with ID {id} not found.")
                return None

        except Exception as e:
            # Handle any exception that occurs during the query
            print(f"Error getting none credential data: {e}")
            return None

    def transfer_balance_by_id(self, sender_id, receiver_id, amount):
        """
        Transfer balance from one user to another.

        Args:
            sender_id (int): ID of the sender (user transferring balance).
            receiver_id (int): ID of the receiver (user receiving balance).
            amount (int): The amount of balance to transfer.

        Returns:
            bool: True if the transfer is successful, None if it fails.
        """
        try:
            # Retrieve data for both sender and receiver
            sender_data = self.get_none_credential_data_by_id(sender_id)
            receiver_data = self.get_none_credential_data_by_id(receiver_id)

            # Validate that both users exist
            if not sender_data or not receiver_data:
                print(f"Error: Sender ID {sender_id} or Receiver ID {receiver_id} not found.")
                return None

            # Validate transfer conditions
            if sender_data['Balance'] - amount < 0 or amount <= 0:
                print(
                    f"Error: Invalid transfer amount. Sender's balance: {sender_data['Balance']}, Attempted transfer: {amount}")
                return None

            # Calculate new balances
            sender_balance = sender_data['Balance'] - amount
            receiver_balance = receiver_data['Balance'] + amount

            # Update sender's balance in the database
            self.users_cursor.execute(f'''
                UPDATE Users
                SET Balance = {sender_balance}
                WHERE ID = "{sender_id}"
            ''')

            # Update receiver's balance in the database
            self.users_cursor.execute(f'''
                UPDATE Users
                SET Balance = {receiver_balance}
                WHERE ID = "{receiver_id}"
            ''')

            # Commit the changes to the database
            self.users_conn.commit()
            print(f"Transferred {amount} from User ID {sender_id} to User ID {receiver_id}.")
            return True

        except Exception as e:
            # Handle any exception that occurs during the transfer
            print(f"Error transferring balance: {e}")
            return None

    def add_balance_by_id(self, id, amount):
        """
        Add balance to a user's account by their ID.

        Args:
            id (int): The ID of the user.
            amount (int): The amount to add to the user's balance (can be negative to deduct balance).

        Returns:
            int: The updated balance if successful, or None if the operation fails (e.g., balance becomes negative).
        """
        try:
            print(f"add_balance_by_id({id}, {amount})")
            amount = int(amount)  # Ensure the amount is an integer

            # Retrieve the user's current data
            data = self.get_none_credential_data_by_id(id)
            if not data:
                print(f"User with ID {id} not found.")
                return None

            # Calculate the new balance
            balance = data['Balance'] + amount

            # Ensure balance does not become negative
            if balance < 0:
                print(f"Balance cannot be negative. Current: {data['Balance']}, Attempted: {balance}")
                return None

            # Update the user's balance in the database
            self.users_cursor.execute(f'''
                UPDATE Users
                SET Balance = {balance}
                WHERE ID = "{id}"
            ''')
            self.users_conn.commit()  # Commit the changes
            return balance

        except Exception as e:
            # Handle any exception that occurs during the update
            print(f"Error updating balance for user ID {id}: {e}")
            return None

    def add_ranked_points_by_id(self, id, amount):
        """
        Add ranked points to a user by their ID.

        Args:
            id (int): The ID of the user.
            amount (int): The number of ranked points to add (can be negative to deduct points).

        Returns:
            int: The updated ranked points if successful, or None if the operation fails.
        """
        try:
            # Retrieve the user's current data
            data = self.get_none_credential_data_by_id(id)
            if not data:
                print(f"User with ID {id} not found.")
                return None

            # Calculate the new ranked points
            ranked_points = data['RankPoints'] + amount

            # Ensure ranked points are not negative
            if ranked_points < 0:
                print(f"Ranked points cannot be negative. Current: {data['RankPoints']}, Attempted: {ranked_points}")
                return None

            # Update the user's ranked points in the database
            self.users_cursor.execute(f'''
                UPDATE Users
                SET RankPoints = {ranked_points}
                WHERE ID = "{id}"
            ''')
            self.users_conn.commit()  # Commit the changes
            return ranked_points

        except Exception as e:
            # Handle any exception that occurs during the update
            print(f"Error updating ranked points for user ID {id}: {e}")
            return None

    def login(self, name, password):
        """
        Authenticate a user by their username and password.

        Args:
            name (str): The username of the user.
            password (str): The password of the user.

        Returns:
            dict: A dictionary containing user details if login is successful,
                  or a dictionary with None values if login fails.
        """
        try:
            # Query the Users table to validate credentials
            self.users_cursor.execute(f'''
                SELECT ID, Username, Balance, RankPoints FROM Users
                WHERE Username = "{name}" AND Password = "{password}"
            ''')
            result = self.users_cursor.fetchone()  # Fetch the user details if credentials match

            if result:
                return {
                    "ID": result[0],
                    "Username": result[1],
                    "Balance": result[2],
                    "RankPoints": result[3]
                }

            # Return default values if login fails
            return {
                "ID": None,
                "Username": None,
                "Balance": None,
                "RankPoints": None
            }

        except Exception as e:
            # Handle any exception that occurs during the query
            print(f"Error logging in: {e}")
            return {
                "ID": None,
                "Username": None,
                "Balance": None,
                "RankPoints": None
            }

    def get_pack_by_id(self, id):
        """
        Retrieve pack details by its ID from the Packs table.

        Args:
            id (int): The ID of the pack to retrieve.

        Returns:
            dict: A dictionary containing the pack details if found, or None if an error occurs.
        """
        try:
            # Query the Packs table to get details of the pack with the given ID
            self.packs_cursor.execute(f'''
                SELECT * FROM Packs
                WHERE ID = "{id}"
            ''')
            result = self.packs_cursor.fetchone()  # Fetch the pack details

            if result:
                return {
                    "ID": result[0],
                    "Name": result[1],
                    "Price": result[2],
                    "CommonChance": result[3],
                    "UncommonChance": result[4],
                    "RareChance": result[5],
                    "HoloRareChance": result[6]
                }
            else:
                print(f"No pack found with ID: {id}")
                return None

        except Exception as e:
            # Handle any exception that occurs during the query
            print(f"Error getting pack data: {e}")
            return None

    def get_random_card_by_rarity(self, seltenheit):
        """
        Retrieve a random card of a specific rarity from the Cards table.

        Args:
            seltenheit (str): The rarity of the card to be retrieved (e.g., "Common", "Rare").

        Returns:
            dict: Details of the randomly selected card, or an error message if no card is found.
        """
        print(f"get_random_card_by_rarity({seltenheit})")
        try:
            # Query the Cards table to get all cards with the specified rarity
            self.cards_cursor.execute(f'''
                SELECT ID, Name, Type, A1Schaden, A2Schaden, A1Energie, A2Energie, Schwäche, Resistenz, RückzugsKosten, Leben, Seltenheit
                FROM Cards
                WHERE Seltenheit = "{seltenheit}"
            ''')
            results = self.cards_cursor.fetchall()  # Fetch all matching rows

            # Choose a random card from the results
            if not results:
                print("no_random_card")
                return {
                    "Name": "No Card Found",
                    "Seltenheit": seltenheit,
                    "ERROR": "No matching cards found"
                }

            random_card = random.choice(results)
            return random_card  # Return the randomly selected card

        except Exception as e:
            # Handle any exception that occurs during the query or random selection
            print("Error picking a random card: ", e)
            return {
                "Name": "No Card Found",
                "Seltenheit": seltenheit,
                "ERROR": str(e)
            }

    def add_card_to_user(self, user_id, card_id):
        """
        Add a new card to a user's ownership in the CardsOwned table (works inside cards_owned.db).

        Args:
            user_id (int): ID of the user who will own the card.
            card_id (int): ID of the card to be added.

        Returns:
            bool: True if the card is successfully added, else False.
        """
        try:
            # Insert a new record into the CardsOwned table with the given user ID and card ID
            self.cards_owned_conn.execute(f'''
                INSERT INTO CardsOwned (UserID, CardID)
                VALUES ("{user_id}", "{card_id}")
            ''')
            self.cards_owned_conn.commit()  # Commit the changes to the database
            return True

        except Exception as e:
            # Handle any exception that occurs during insertion
            print(f"Error adding card to cards_owned: {e}")
            return False

    def get_cards_owned_by_id(self, id):
        """
        Retrieve all card ownership entries for a specific user (works inside cards_owned.db).

        Args:
            id (int): ID of the user whose card ownership records are being queried.

        Returns:
            list: A list of tuples representing the cards owned by the user.
        """
        try:
            # Query the CardsOwned table to retrieve all records for the given user ID
            self.cards_owned_cursor.execute(f'''
                SELECT * FROM CardsOwned
                WHERE UserID = "{id}"
            ''')
            results = self.cards_owned_cursor.fetchall()  # Fetch all matching rows
            return results  # Return the list of cards owned

        except Exception as e:
            # Print an error message if an exception occurs during the query
            print(f"Error getting cards_owned by id: {e}")
            return []  # Return an empty list in case of an error

    def get_cards_owned_by_user_id(self, user_id):
        """
        Retrieve all cards owned by a user (works inside cards_owned.db and pokemon_cards.db).

        Args:
            user_id (int): ID of the user whose cards are being queried.

        Returns:
            list: A list of card details for the cards owned by the user.
        """
        # Query the CardsOwned table to get all cards associated with the user
        self.cards_owned_cursor.execute(f'''
            SELECT UserID, CardID FROM CardsOwned
            WHERE UserID = "{user_id}"
        ''')
        cards_owned = self.cards_owned_cursor.fetchall()  # Fetch all rows from the query
        user_cards = []  # Initialize an empty list to store card details

        if cards_owned:
            # Iterate over each card the user owns
            for card_user_connection in cards_owned:
                card_id = card_user_connection[1]  # Extract the CardID

                # Query the Cards table to get full details of the card
                self.cards_cursor.execute(f'''
                    SELECT * FROM Cards
                    WHERE ID = "{card_id}"
                ''')
                card = self.cards_cursor.fetchone()  # Fetch the card details

                if card:
                    user_cards.append(card)  # Add the card details to the user's card list

        return user_cards  # Return the list of cards owned by the user

    def transfer_card(self, sender_id, receiver_id, card_id):
        """
        Transfer a card from one user to another (works inside cards_owned.db)

        Args:
            sender_id (int): ID of original owner of the card
            receiver_id (int): ID of the receiver (new owner of the card)
            card_id (int): ID of the card that is being sent

        Returns:
            bool: True if transfer is successful else False
        """
        try:
            # Check if the sender owns the card
            self.cards_owned_cursor.execute(f'''
                SELECT * FROM CardsOwned
                WHERE CardID = "{card_id}" AND UserID = "{sender_id}"
            ''')
            card = self.cards_owned_cursor.fetchone()
            card_rowid = card[0]

            if not card:
                print(f"Card ID {card_id} is not owned by User ID {sender_id}")
                return False  # The sender does not own the card with the id he entered

            # Update the UserID to the ID of the new owner
            self.cards_owned_cursor.execute(f'''
                UPDATE CardsOwned
                SET UserID = "{receiver_id}"
                WHERE ID = "{card_rowid}"
            ''')
            self.cards_owned_conn.commit()
            return True

        except Exception as e:
            print(f"Error transferring card: {e}")
            return False

    def delete_card_from_cards_owned(self, user_id, card_id):
        """
        Delete a card from the CardsOwned table (works inside cards_owned.db).

        Args:
            user_id (int): ID of the user who owns the card
            card_id (int): ID of the card that is supposed to be deleted

        Returns:
            bool: True if the deletion is successful, else False
        """
        try:
            # Get row ID of the card that is supposed to be deleted
            self.cards_owned_cursor.execute(f'''
                SELECT * FROM CardsOwned
                WHERE CardID = "{card_id}" AND UserID = "{user_id}"
            ''')
            card = self.cards_owned_cursor.fetchone()

            # If no card is found, return False
            if not card:
                print(f"Card ID {card_id} is not owned by User ID {user_id}")
                return False

            card_rowid = card[0]  # Extract the unique row ID for deletion

            # Delete the card with the specific row ID
            self.cards_owned_cursor.execute(f'''
                DELETE FROM CardsOwned
                WHERE ID = {card_rowid}
            ''')

            self.cards_owned_conn.commit()  # Commit the deletion to the database
            return True

        except Exception as e:
            # Handle any exception that occurs during deletion
            print(f"Error deleting card from cards_owned.db: {e}")
            return False

    def add_marketplace_entry(self, user_id, card_id, price):
        """
        Add an entry to the Marketplace table (works inside marketplace.db).

        Args:
            user_id (int): ID of the user who is listing the card
            card_id (int): ID of the card being listed
            price (int): Price of the card being listed on the marketplace

        Returns:
            bool: True if the entry is successfully added, else False
        """
        try:
            # Insert a new entry into the Marketplace table with the given user ID, card ID, and price
            self.marketplace_cursor.execute(f'''
                INSERT INTO Marketplace (UserID, CardID, Price)
                VALUES({user_id}, {card_id}, {price})
            ''')

            self.marketplace_conn.commit()  # Commit the changes to the database
            return True

        except Exception as e:
            # Handle any exception that occurs during insertion
            print(f"Error adding entry to marketplace.db: {e}")
            return False


class Server:
    data_base_manager = DataBaseManager()

    def __init__(self):
        pass

    def start(self, host='0.0.0.0', port=65432):    # starting server / infinite while loop
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
            print(f"RECEIVED:\t{json_data}{" "*6}FROM :{addr}")
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
                case "openPack":
                    response = self.pull_cards(json_data["user_id"], json_data["pack_id"])
                case "inventory":
                    response = self.data_base_manager.get_cards_owned_by_user_id(json_data["user_id"])
                case "query":
                    response = "pass"
                case "sendCard":
                    response = self.data_base_manager.transfer_card(json_data["user_id"], json_data["receiver_id"],
                                                                    json_data["card_id"])
                case "marketplaceEntry":
                    response = self.add_entry_to_marketplace(json_data["user_id"], json_data["card_id"],
                                                             json_data["price"])

            compressed_data = zlib.compress(json.dumps(response).encode('utf-8'))  # compress and send data
            conn.sendall(compressed_data)
            conn.close()  # Close connection

            print(f"SEND:\t\t{json.dumps(response)}{" "*6}TO: {addr}")

    def add_entry_to_marketplace(self, user_id, card_id, price):
        """
        Add a card to the marketplace by first removing it from the user's ownership.

        Args:
            user_id (int): ID of the user listing the card on the marketplace.
            card_id (int): ID of the card being listed.
            price (int): Price of the card on the marketplace.

        Returns:
            bool: True if the card is successfully listed on the marketplace, False otherwise.
        """
        # Execute delete_card_from_cards_owned to remove the card from the user's ownership
        r1 = self.data_base_manager.delete_card_from_cards_owned(user_id, card_id)
        if r1:  # Proceed only if the card was successfully removed
            # Attempt to add the card to the marketplace
            r2 = self.data_base_manager.add_marketplace_entry(user_id, card_id, price)
            return r2  # Return True if add_marketplace_entry is successful

        return r1  # Return False if delete_card_from_cards_owned fails

    def pull_cards(self, user_id, pack_id):
        """
        Pull cards from a pack for a user.

        Args:
            user_id (int): ID of the user pulling the cards.
            pack_id (int): ID of the pack being opened.

        Returns:
            list: A list of cards pulled from the pack.
        """
        try:
            # Retrieve pack details using pack_id
            pack_data = self.data_base_manager.get_pack_by_id(pack_id)
            if not pack_data:
                print(f"Error: Pack ID {pack_id} not found.")
                return []

            print(pack_data)
            cards = []

            # Pull 8 cards from the pack
            for i in range(8):

                if random.random() > pack_data["CommonChance"]:
                    if random.random() > pack_data["UncommonChance"]:
                        if random.random() > pack_data["RareChance"]:
                            card = self.data_base_manager.get_random_card_by_rarity("HoloRare")
                            cards.append(card)
                        else:
                            card = self.data_base_manager.get_random_card_by_rarity("Rare")
                            cards.append(card)
                    else:
                        card = self.data_base_manager.get_random_card_by_rarity("Uncommon")
                        cards.append(card)
                else:
                    card = self.data_base_manager.get_random_card_by_rarity("Common")
                    cards.append(card)

            # Add the pulled cards to the user's ownership
            for card in cards:
                if card and card[0]:  # Ensure card data is valid before adding
                    self.data_base_manager.add_card_to_user(user_id, card[0])

            return cards

        except Exception as e:
            # Handle any exception during the process
            print(f"Error pulling cards for user {user_id} and pack {pack_id}: {e}")
            return []


def main():
    server = Server()
    server.start()


main()
