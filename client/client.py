import socket
import json
import zlib

host = '127.0.0.1'
port = 65432

user_data = {
        "ID": None,
        "Username": None,
        "Balance": None,
        "RankPoints": None
}
coins = 3000

def send_dict_as_json_to_server(dict_data):  # takes a dictionary
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Convert dict to JSON
    json_data = json.dumps(dict_data)

    # Send the JSON string
    client_socket.sendall(json_data.encode('utf-8'))

    # Receive response from the server
    compressed_response = client_socket.recv(1024*4)  # receiving compressed data
    response = json.loads(zlib.decompress(compressed_response).decode('utf-8'))  # decompress
    #dict_response = json.loads(response)   # json convert to dict

    client_socket.close()
    return response     # return response


def login(username, password):
    global user_data
    dict_data = {"type": "login", "username": username, "password": password}
    user_data = send_dict_as_json_to_server(dict_data)


def register(username, password):
    dict_data = {"type": "register", "username": username, "password": password}
    return send_dict_as_json_to_server(dict_data)


def update_user_data():
    global user_data
    dict_data = {"type": "getData", "id": user_data['ID']}
    user_data = send_dict_as_json_to_server(dict_data)


def deposit(amount):
    global user_data, coins
    dict_data = {"type": "deposit", "id": user_data['ID'], "amount": amount}
    response = send_dict_as_json_to_server(dict_data)
    if response is not None and coins >= 0:    # if response is None the deposit failed because the Balance are less than 0
        coins = coins - amount
    update_user_data()


def withdraw(amount):
    global user_data, coins
    dict_data = {"type": "withdraw", "id": user_data['ID'], "amount": amount}
    response = send_dict_as_json_to_server(dict_data)
    if response is not None and coins >= 0:    # if response is None the deposit failed because the Balance are less than 0
        coins = coins + amount
    update_user_data()


def transfer(receiver_id, amount):
    global user_data
    dict_data = {"type": "transfer", "sender_id": user_data['ID'], "receiver_id": receiver_id, "amount": amount}
    response = send_dict_as_json_to_server(dict_data)
    update_user_data()

def open_pack(pack_id):
    global user_data, coins

    if pack_id == "1":
        if coins < 200:     # Return if the user does not have enough coins
            return
        coins -= 200        # Subtract price from coins
    elif pack_id == "2":
        if coins < 600:     # Return if the user does not have enough coins
            return
        coins -= 600       # Subtract price from coins
    elif pack_id == "3":
        if coins < 3000:    # Return if the user does not have enough coins
            return
        coins -= 3000       # Subtract price from coins
    else:
        return  # Return the pack_id does not exist
    dict_data = {"type": "openPack", "user_id": user_data['ID'], "pack_id": pack_id}
    pack = send_dict_as_json_to_server(dict_data)   # Array of cards (dicts)
    # Sort the pack
    sorted_pack = []
    for card in pack:
        if card[11] == "Common":
            sorted_pack.append(card)
    for card in pack:
        if card[11] == "Uncommon":
            sorted_pack.append(card)
    for card in pack:
        if card[11] == "Rare":
            sorted_pack.append(card)
    for card in pack:
        if card[11] == "HoloRare":
            sorted_pack.append(card)

    for card in sorted_pack:
        input(card)

def send_sql_query(query):
    dict_data = {"type": "query", "query": query}
    send_dict_as_json_to_server(dict_data)

def get_inventory():
    global user_data
    dict_data = {"type": "inventory", "user_id": user_data['ID']}
    inventory = send_dict_as_json_to_server(dict_data)
    sorted_inv = []
    for card in inventory:
        if card[11] == "Common":
            sorted_inv.append(card)
    for card in inventory:
        if card[11] == "Uncommon":
            sorted_inv.append(card)
    for card in inventory:
        if card[11] == "Rare":
            sorted_inv.append(card)
    for card in inventory:
        if card[11] == "HoloRare":
            sorted_inv.append(card)
    return sorted_inv

def send_card(receiver_id, card_id):
    dict_data = {"type": "sendCard", "user_id": user_data['ID'], "receiver_id": receiver_id, "card_id": card_id}
    response = send_dict_as_json_to_server(dict_data)


if __name__ == "__main__":
    while True:
        print("\n")
        print(user_data)
        print("Coins: ", coins)
        print("COMMANDS: LOGIN, REGISTER, DEPOSIT, WITHDRAW, TRANSFER, OPENPACK, INVENTORY, QUERY, SEND CARD")
        command = input("command: ")
        match command.lower():
            case "login":
                username = input("username: ")
                password = input("password: ")
                login(username, password)

            case "register":
                username = input("username: ")
                password = input("password: ")
                print(register(username, password))

            case "getdata":
                id = input("id: ")
                update_user_data()

            case "deposit":
                amount = input("amount: ")
                deposit(int(amount))
                update_user_data()

            case "withdraw":
                amount = input("amount: ")
                withdraw(int(amount))
                update_user_data()

            case "transfer":
                receiver_id = input("receiver id: ")
                amount = input("amount: ")
                transfer(int(receiver_id), int(amount))
                update_user_data()
            case "openpack":
                pack_id = input("pack id: ")
                open_pack(pack_id)
                update_user_data()
            case "inventory":
                inv = get_inventory()
                for card in inv:
                    print(card)
            case "command":
                query = input("SQL query: ")
                send_sql_query(query)
            case "send card":
                receiver_id = input("receiver id: ")
                card_id = input("card id: ")
                send_card(receiver_id, card_id)
