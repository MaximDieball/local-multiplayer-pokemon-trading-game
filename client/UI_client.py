import sys
import socket
import json
import zlib

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QDialog, QDialogButtonBox,
    QGridLayout, QScrollArea
)
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt, QRect

width = 800
height = 500

# ---------------------------------------------------------------------
# EXTENDED CLIENT CODE
# ---------------------------------------------------------------------
class Client:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port

        # Server-side data about the user
        self.user_data = {
            "ID": None,
            "Username": None,
            "Balance": None,      # the 'bank' balance on the server
            "RankPoints": None
        }

        # Local coins: on-hand coins that the client can deposit or receive via withdraw
        self.local_coins = 3000  # an arbitrary starting value for demonstration

    def send_dict_as_json_to_server(self, dict_data):
        """Send a JSON-encoded dict to the server and return the response."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.host, self.port))

        json_data = json.dumps(dict_data)
        client_socket.sendall(json_data.encode('utf-8'))

        compressed_response = client_socket.recv(1024*4)
        response_data = json.loads(zlib.decompress(compressed_response).decode('utf-8'))

        client_socket.close()
        return response_data

    def login(self, username, password):
        dict_data = {
            "type": "login",
            "username": username,
            "password": password
        }
        response = self.send_dict_as_json_to_server(dict_data)
        self.user_data = response  # e.g.: {"ID": 2, "Username": "user", "Balance": 50, "RankPoints": 100} or all None if fail
        return response

    def register(self, username, password):
        dict_data = {
            "type": "register",
            "username": username,
            "password": password
        }
        response = self.send_dict_as_json_to_server(dict_data)
        return response  # Could be True, False, or error message

    def update_user_data(self):
        """Pull fresh user data from the server (like server-side Balance)."""
        if self.user_data["ID"] is None:
            return None  # not logged in
        dict_data = {
            "type": "getData",
            "id": self.user_data["ID"]
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response:
            self.user_data = response
        return response

    # ----------------- DEPOSIT / WITHDRAW (NEW LOGIC) ----------------- #
    def deposit(self, amount):
        """
        Deposit local coins to server.
        1) Check if we have enough local_coins.
        2) If yes, reduce local_coins and call server deposit -> increase server balance.
        3) Refresh user_data.
        """
        if amount <= 0:
            print("Deposit amount must be positive.")
            return None

        if self.local_coins < amount:
            print(f"Not enough local coins. Currently have {self.local_coins}.")
            return None

        # Enough local_coins -> proceed
        dict_data = {
            "type": "deposit",
            "id": self.user_data["ID"],
            "amount": amount
        }
        response = self.send_dict_as_json_to_server(dict_data)

        if response is not None:
            # deposit succeeded on server side
            self.local_coins -= amount
            self.update_user_data()  # refresh from server
        else:
            print("Server deposit failed or returned None.")
        return response

    def withdraw(self, amount):
        """
        Withdraw from server to local coins.
        1) Check if server-side Balance >= amount
        2) If yes, call server withdraw, which lowers server balance. Then we add local_coins.
        3) Refresh user_data
        """
        if amount <= 0:
            print("Withdraw amount must be positive.")
            return None

        if self.user_data["Balance"] is None or self.user_data["Balance"] < amount:
            print(f"Not enough balance on the server. Currently have {self.user_data['Balance']}.")
            return None

        dict_data = {
            "type": "withdraw",
            "id": self.user_data["ID"],
            "amount": amount
        }
        response = self.send_dict_as_json_to_server(dict_data)

        if response is not None:
            # withdraw succeeded on server side
            self.local_coins += amount
            self.update_user_data()  # refresh from server
        else:
            print("Server withdraw failed or returned None.")
        return response

    # ----------------- TRANSFER / SEND CARD ----------------- #
    def transfer(self, receiver_id, amount):
        """
        Transfer coins from this user’s server balance to another user’s server balance.
        Not to be confused with local_coins!
        1) Check if user_data["Balance"] >= amount
        2) If yes, do "type": "transfer" to the server
        3) Refresh user data on success
        """
        if amount <= 0:
            print("Transfer amount must be positive.")
            return None

        if self.user_data["Balance"] is None or self.user_data["Balance"] < amount:
            print(f"Not enough balance on the server to transfer. Currently have {self.user_data['Balance']}.")
            return None

        dict_data = {
            "type": "transfer",
            "sender_id": self.user_data["ID"],
            "receiver_id": receiver_id,
            "amount": amount
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response is True:
            self.update_user_data()  # refresh from server
        else:
            print(f"Server transfer failed or returned: {response}")
        return response

    def send_card(self, receiver_id, card_id):
        """
        Transfer a card from this user to another user on the server side.
        """
        dict_data = {
            "type": "sendCard",
            "user_id": self.user_data["ID"],
            "receiver_id": receiver_id,
            "card_id": card_id
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response is True:
            self.update_user_data()
        else:
            print("Send card request failed or returned:", response)
        return response


# ------------------------------ LoginRegisterUI ------------------------------ #
class LoginRegisterUI(QWidget):
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window = main_window_ref
        self.init_ui()

    def init_ui(self):
        w, h = 800, 400
        self.setFixedSize(w, h)

        half_width = w // 2
        left_x = half_width - 220
        right_x = half_width + 20

        # ================ LOGIN SECTION ================
        login_label = QLabel("Login", self)
        login_label.setGeometry(QRect(left_x, 30, 100, 30))

        login_name_label = QLabel("Name:", self)
        login_name_label.setGeometry(QRect(left_x, 70, 60, 20))

        self.login_name_input = QLineEdit(self)
        self.login_name_input.setGeometry(QRect(left_x + 65, 70, 150, 20))

        login_password_label = QLabel("Password:", self)
        login_password_label.setGeometry(QRect(left_x, 110, 60, 20))

        self.login_password_input = QLineEdit(self)
        self.login_password_input.setGeometry(QRect(left_x + 65, 110, 150, 20))
        self.login_password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login", self)
        login_button.setGeometry(QRect(left_x, 150, 80, 30))
        login_button.clicked.connect(self.handle_login)

        # ================ REGISTER SECTION ================
        register_label = QLabel("Register", self)
        register_label.setGeometry(QRect(right_x, 30, 100, 30))

        register_name_label = QLabel("Name:", self)
        register_name_label.setGeometry(QRect(right_x, 70, 60, 20))

        self.register_name_input = QLineEdit(self)
        self.register_name_input.setGeometry(QRect(right_x + 65, 70, 150, 20))

        register_password_label = QLabel("Password:", self)
        register_password_label.setGeometry(QRect(right_x, 110, 60, 20))

        self.register_password_input = QLineEdit(self)
        self.register_password_input.setGeometry(QRect(right_x + 65, 110, 150, 20))
        self.register_password_input.setEchoMode(QLineEdit.Password)

        register_button = QPushButton("Register", self)
        register_button.setGeometry(QRect(right_x, 150, 80, 30))
        register_button.clicked.connect(self.handle_register)

    def handle_login(self):
        username = self.login_name_input.text()
        password = self.login_password_input.text()

        if not username or not password:
            print("Username or password is empty!")
            return

        response = self.main_window.client.login(username, password)
        if response["ID"] is not None:
            # success
            self.main_window.show_main_widget()
        else:
            print("Login failed!")

    def handle_register(self):
        username = self.register_name_input.text()
        password = self.register_password_input.text()

        if not username or not password:
            print("Username or password is empty!")
            return

        reg_response = self.main_window.client.register(username, password)
        # If server returns True or a success code
        if reg_response is True or reg_response == 1:
            # auto-login
            login_response = self.main_window.client.login(username, password)
            if login_response["ID"] is not None:
                self.main_window.show_main_widget()
            else:
                print("Login after registration failed!")
        else:
            print("Registration failed or username taken!")


# ------------------------------ TopBar ------------------------------ #
class TopBar(QWidget):
    """
    Top bar:
      - local coins on the left
      - deposit/withdraw/transfer send-cards
      - user data (ID, Name, Balance, RankPoints) on the right
    """
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.setFixedHeight(80)
        self.init_ui()

    def init_ui(self):
        bar_width = self.parent_widget.width()
        self.setFixedWidth(bar_width)

        # Local coin image
        self.coin_label = QLabel(self)
        coin_pixmap = QPixmap("images/coin.png")
        self.coin_label.setPixmap(coin_pixmap)
        self.coin_label.setScaledContents(True)
        self.coin_label.setGeometry(20, 10, 60, 60)

        # Local coin count label
        self.local_coins_label = QLabel("Local: 3000", self)
        self.local_coins_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.local_coins_label.setGeometry(90, 25, 100, 30)

        # Deposit
        self.deposit_button = QPushButton("Deposit", self)
        self.deposit_button.setGeometry(190, 25, 80, 30)
        self.deposit_button.clicked.connect(self.parent_widget.show_deposit_dialog)

        # Withdraw
        self.withdraw_button = QPushButton("Withdraw", self)
        self.withdraw_button.setGeometry(280, 25, 80, 30)
        self.withdraw_button.clicked.connect(self.parent_widget.show_withdraw_dialog)

        # Send coins
        self.send_coins_button = QPushButton("Send coins", self)
        self.send_coins_button.setGeometry(370, 25, 80, 30)
        self.send_coins_button.clicked.connect(self.parent_widget.show_send_coins_dialog)

        # Send cards
        self.send_cards_button = QPushButton("Send cards", self)
        self.send_cards_button.setGeometry(460, 25, 80, 30)
        self.send_cards_button.clicked.connect(self.parent_widget.show_send_cards_dialog)

        # User data label (server side)
        self.user_data_label = QLabel("""
ID: ?
Name: ?
Balance: ?
RankedPoints: ?
""", self)
        self.user_data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_data_label.setGeometry(560, 5, 150, 70)

        # Profile image
        self.profile_label = QLabel(self)
        profile_pixmap = QPixmap("images/profile.png")
        self.profile_label.setPixmap(profile_pixmap)
        self.profile_label.setScaledContents(True)
        self.profile_label.setGeometry(720, 10, 60, 60)

    def update_display(self, client):
        """
        Update the top bar to show:
          - local coins
          - user_data from client.user_data
        """
        # Update local coins
        self.local_coins_label.setText(f"Local: {client.local_coins}")

        # If user_data is valid, show ID, Name, Balance, etc.
        if client.user_data["ID"] is not None:
            id_ = client.user_data["ID"]
            name_ = client.user_data["Username"]
            bal_ = client.user_data["Balance"]
            rp_ = client.user_data["RankPoints"]
            text = f"ID: {id_}\nName: {name_}\nBalance: {bal_}\nRankedPoints: {rp_}"
        else:
            text = """ID: ?\nName: ?\nBalance: ?\nRankedPoints: ?"""

        self.user_data_label.setText(text)


# ------------------------------ MainPage ------------------------------ #
class MainPage(QWidget):
    """
    main page:
      - Pokeball + pointer images for style
      - Buttons: open packs, inventory, wager
    """
    def __init__(self, switch_to_wager_page_callback, switch_to_open_packs_page_callback, switch_to_inventory_page_callback):
        super().__init__()
        self.switch_to_wager_page_callback = switch_to_wager_page_callback
        self.switch_to_open_packs_page_callback = switch_to_open_packs_page_callback
        self.switch_to_inventory_page_callback = switch_to_inventory_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)

        # Pokeball Image
        self.pokeball_label = QLabel(self)
        pokeball_pixmap = QPixmap("images/pokeball.png")
        self.pokeball_label.setPixmap(pokeball_pixmap)
        self.pokeball_label.setScaledContents(True)
        self.pokeball_label.setGeometry(QRect(50, 40, 200, 200))

        # Pointer Image
        self.pointer_label = QLabel(self)
        pointer_pixmap = QPixmap("images/pointer.png")
        transform = QTransform()
        transform.rotate(-45)
        rotated_pointer = pointer_pixmap.transformed(transform, Qt.SmoothTransformation)
        self.pointer_label.setPixmap(rotated_pointer)
        self.pointer_label.setScaledContents(True)
        self.pointer_label.setGeometry(QRect(180, 180, 50, 50))

        # Open packs
        self.open_packs_button = QPushButton("Open packs", self)
        self.open_packs_button.setGeometry(QRect(350, 20, 200, 100))
        self.open_packs_button.clicked.connect(self.switch_to_open_packs_page_callback)

        # Inventory
        self.inventory_button = QPushButton("Inventory", self)
        self.inventory_button.setGeometry(QRect(350, 120, 200, 100))
        self.inventory_button.clicked.connect(self.switch_to_inventory_page_callback)

        # Wager
        self.wager_button = QPushButton("Wager", self)
        self.wager_button.setGeometry(QRect(350, 220, 200, 100))
        self.wager_button.clicked.connect(self.switch_to_wager_page_callback)


# ------------------------------ OpenPacksPage ------------------------------ #
class OpenPacksPage(QWidget):
    def __init__(self, switch_to_main_page_callback):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)

        self.pack1_button = QPushButton("Pack 1", self)
        self.pack1_button.setGeometry(200, 100, 80, 130)

        self.pack2_button = QPushButton("Pack 2", self)
        self.pack2_button.setGeometry(320, 100, 80, 130)

        self.pack3_button = QPushButton("Pack 3", self)
        self.pack3_button.setGeometry(440, 100, 80, 130)

        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)


# ------------------------------ InventoryPage ------------------------------ #
class InventoryPage(QWidget):
    def __init__(self, switch_to_main_page_callback):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        container = QWidget()
        grid_layout = QGridLayout(container)
        container.setLayout(grid_layout)

        # Add placeholders
        for i in range(30):
            label = QLabel(f"item {i+1}")
            label.setStyleSheet(
                "border: 1px solid gray; background: white; min-width:80px; min-height:80px;"
                "margin: 5px; "
            )
            row = i // 5
            col = i % 5
            grid_layout.addWidget(label, row, col)

        scroll_area.setWidget(container)

        self.back_button = QPushButton("<---")
        self.back_button.clicked.connect(self.switch_to_main_page_callback)
        layout.addWidget(self.back_button)


# ------------------------------ WagerSearchPage ------------------------------ #
class WagerSearchPage(QWidget):
    def __init__(self, switch_to_main_page_callback):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)

        self.enemy_label = QLabel("Enemy Player ID:", self)
        self.enemy_label.setGeometry(289, 150 - 30, 100, 25)

        self.enemy_input = QLineEdit(self)
        self.enemy_input.setGeometry(398, 150 - 30, 120, 25)

        self.stake_label = QLabel("Stake:", self)
        self.stake_label.setGeometry(289, 204 - 30, 100, 25)

        self.stake_input = QLineEdit(self)
        self.stake_input.setGeometry(398, 204 - 30, 120, 25)

        self.search_button = QPushButton("Search", self)
        self.search_button.setGeometry(363, 300, 80, 30)

        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)


# ------------------------------ MainWidget ------------------------------ #
class MainWidget(QWidget):
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window = main_window_ref
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 1) TopBar
        self.top_bar = TopBar(self)
        layout.addWidget(self.top_bar)

        # 2) center QStackedWidget
        self.center_stack = QStackedWidget(self)
        layout.addWidget(self.center_stack)

        # create pages
        self.main_page = MainPage(
            self.show_wager_page,
            self.show_open_packs_page,
            self.show_inventory_page
        )
        self.wager_page = WagerSearchPage(self.show_main_page)
        self.open_packs_page = OpenPacksPage(self.show_main_page)
        self.inventory_page = InventoryPage(self.show_main_page)

        self.center_stack.addWidget(self.main_page)       # index 0
        self.center_stack.addWidget(self.wager_page)      # index 1
        self.center_stack.addWidget(self.open_packs_page) # index 2
        self.center_stack.addWidget(self.inventory_page)  # index 3

        self.center_stack.setCurrentWidget(self.main_page)

    # -------------- DIALOG METHODS -------------- #
    def show_withdraw_dialog(self):
        dialog = WithdrawDialog()
        if dialog.exec_() == QDialog.Accepted:
            amount_str = dialog.get_amount()
            if amount_str.isdigit():
                amount = int(amount_str)
                # Attempt to withdraw from server to local_coins
                self.main_window.client.withdraw(amount)
                # Update top bar display
                self.top_bar.update_display(self.main_window.client)
            else:
                print("Invalid amount entered.")

    def show_deposit_dialog(self):
        dialog = DepositDialog()
        if dialog.exec_() == QDialog.Accepted:
            amount_str = dialog.get_amount()
            if amount_str.isdigit():
                amount = int(amount_str)
                # Deposit local coins to server
                self.main_window.client.deposit(amount)
                self.top_bar.update_display(self.main_window.client)
            else:
                print("Invalid amount entered.")

    def show_send_coins_dialog(self):
        dialog = SendCoinsDialog()
        if dialog.exec_() == QDialog.Accepted:
            player_id_str, amount_str = dialog.get_data()
            if player_id_str.isdigit() and amount_str.isdigit():
                receiver_id = int(player_id_str)
                amount = int(amount_str)
                self.main_window.client.transfer(receiver_id, amount)
                self.top_bar.update_display(self.main_window.client)
            else:
                print("Invalid ID or amount.")

    def show_send_cards_dialog(self):
        dialog = SendCardsDialog()
        if dialog.exec_() == QDialog.Accepted:
            player_id_str, card_id_str = dialog.get_data()
            if player_id_str.isdigit() and card_id_str.isdigit():
                receiver_id = int(player_id_str)
                card_id = int(card_id_str)
                self.main_window.client.send_card(receiver_id, card_id)
                self.top_bar.update_display(self.main_window.client)
            else:
                print("Invalid ID or card ID.")

    # -------------- STACK-SWITCH METHODS -------------- #
    def show_main_page(self):
        self.center_stack.setCurrentWidget(self.main_page)

    def show_wager_page(self):
        self.center_stack.setCurrentWidget(self.wager_page)

    def show_open_packs_page(self):
        self.center_stack.setCurrentWidget(self.open_packs_page)

    def show_inventory_page(self):
        self.center_stack.setCurrentWidget(self.inventory_page)


# ------------------------------ MainWindow ------------------------------ #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Application')
        self.setGeometry(100, 100, width, height)
        self.setFixedSize(width, height)

        self.client = Client()

        self.stacked_widget = QStackedWidget(self)

        self.login_register_page = LoginRegisterUI(self)
        self.main_widget_page = MainWidget(self)

        self.stacked_widget.addWidget(self.login_register_page)  # index 0
        self.stacked_widget.addWidget(self.main_widget_page)      # index 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Start on login page
        self.stacked_widget.setCurrentIndex(0)

    def show_main_widget(self):
        """ After successful login or register, refresh top bar and switch to the main interface. """
        self.main_widget_page.top_bar.update_display(self.client)
        self.stacked_widget.setCurrentIndex(1)


# ------------------------------ Dialogs ------------------------------ #
class WithdrawDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Withdraw Amount")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        label = QLabel("Enter the amount to withdraw:", self)
        layout.addWidget(label)

        self.amount_input = QLineEdit(self)
        layout.addWidget(self.amount_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_amount(self):
        return self.amount_input.text()


class DepositDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deposit Amount")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        label = QLabel("Enter the amount to deposit:", self)
        layout.addWidget(label)

        self.amount_input = QLineEdit(self)
        layout.addWidget(self.amount_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_amount(self):
        return self.amount_input.text()


class SendCoinsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Send Coins")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        player_id_label = QLabel("Enter the Player ID:", self)
        layout.addWidget(player_id_label)

        self.player_id_input = QLineEdit(self)
        layout.addWidget(self.player_id_input)

        amount_label = QLabel("Enter the amount of coins to send:", self)
        layout.addWidget(amount_label)

        self.amount_input = QLineEdit(self)
        layout.addWidget(self.amount_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_data(self):
        player_id = self.player_id_input.text()
        amount = self.amount_input.text()
        return player_id, amount


class SendCardsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Send Cards")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()
        player_id_label = QLabel("Enter the Player ID:", self)
        layout.addWidget(player_id_label)

        self.player_id_input = QLineEdit(self)
        layout.addWidget(self.player_id_input)

        card_id_label = QLabel("Enter the Card ID:", self)
        layout.addWidget(card_id_label)

        self.card_id_input = QLineEdit(self)
        layout.addWidget(self.card_id_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_data(self):
        player_id = self.player_id_input.text()
        card_id = self.card_id_input.text()
        return player_id, card_id


# ------------------------------ main() ------------------------------ #
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
