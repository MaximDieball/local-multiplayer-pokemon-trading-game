import socket
import json
import os

host = '127.0.0.1'
port = 65432

user_data = {
        "ID": None,
        "Username": None,
        "Balance": None,
        "RankPoints": None
}
coins = 1000

def send_dict_as_json_to_server(dict_data):  # takes a dictionary
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Convert dict to JSON
    json_data = json.dumps(dict_data)

    # Send the JSON string
    client_socket.sendall(json_data.encode('utf-8'))

    # Receive response from the server
    json_response = client_socket.recv(1024).decode('utf-8')
    dict_response = json.loads(json_response)   # convert to dict

    client_socket.close()
    return dict_response     # return dict


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


if __name__ == "__main__":
    while True:
        print("\n")
        print(user_data)
        print("Balance: ", coins)
        print("COMMANDS: LOGIN, REGISTER, DEPOSIT, WITHDRAW, TRANSFER")
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
