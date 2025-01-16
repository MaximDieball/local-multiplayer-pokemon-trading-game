import sys
import os
import socket
import json
import zlib

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QDialog, QDialogButtonBox,
    QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PyQt5.QtGui import QPixmap, QMovie, QTransform

# Global window dimensions
width = 800
height = 500

# -------------- Utility: function to build absolute paths -------------- #
def resource_path(*relative_parts):
    """
    Returns an absolute path based on the directory of this script.
    Example: resource_path("images", "back.png") -> absolute path to images/back.png
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, *relative_parts)

# ------------------------------ Pack Animation Window ------------------------------ #
class PackAnimationWindow(QMainWindow):
    """
    A window that flips each card image from a provided list of file paths.
    The user clicks to flip the top card from "back.png" to the front image.
    Sparkles appear briefly after the flip. Each click reveals the next card.
    """
    def __init__(self, card_paths):
        super().__init__()
        self.setWindowTitle("Pack Opening")
        self.setGeometry(100, 100, 600, 800)

        # The "stack" of cards in the background
        back_path = resource_path("images", "back.png")
        print(back_path)
        self.card_stack_label = QLabel(self)
        self.pixmap_back = QPixmap(back_path)
        self.card_stack_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_stack_label.setGeometry(200, 350, 200, 300)

        # The list of card images to reveal
        self.card_paths = card_paths  # These should already be absolute paths
        print("Card paths:", self.card_paths)

        # The flipping card label
        self.card_label = QLabel(self)
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_label.setGeometry(200, 350, 200, 300)
        self.beginning_card_geometry = self.card_label.geometry()

        # Two animations to create the flip effect
        self.animation1 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation1.setDuration(1000)
        self.animation1.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation2 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation2.setDuration(1000)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)

        self.has_flipped = False
        self.animation_running = False
        self.pixmap_front = None

        # Sparkle overlay
        sparkle_path = resource_path("images", "sparkle.gif")
        self.sparkle_label = QLabel(self)
        self.sparkle_label.lower()
        self.sparkle_label.setGeometry(150, 150, 400, 400)
        self.sparkle_movie = QMovie(sparkle_path)
        self.sparkle_label.setMovie(self.sparkle_movie)
        self.sparkle_label.setVisible(False)

    def mousePressEvent(self, event):
        # Trigger the flip on left-click
        if event.button() == Qt.LeftButton:
            self.click()

    def click(self):
        if self.card_paths:
            # If not currently animating, flip the top card
            if not self.has_flipped and not self.animation_running:
                self.animation_running = True
                # Load the front card image
                front_path = self.card_paths.pop(0)
                self.pixmap_front = QPixmap(front_path)

                self.animation()  # Start the flip

                # If this was the last card, remove the stack label
                if not self.card_paths:
                    self.card_stack_label.clear()

            elif not self.animation_running:
                # If the user clicks again after flipping, reset the card
                self.reset_card()
                self.has_flipped = False

    def reset_card(self):
        self.card_label.setGeometry(self.beginning_card_geometry)
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_label.move(200, 350)

    def animation(self):
        current_geometry = self.card_label.geometry()

        # 1) Shrink to zero width
        shrink_geometry = QRect(
            current_geometry.x() + current_geometry.width() // 2,
            current_geometry.y() - 310,
            0,
            current_geometry.height()
        )
        self.animation1.setStartValue(current_geometry)
        self.animation1.setEndValue(shrink_geometry)
        self.animation1.valueChanged.connect(self.update_card_back)

        # 2) Expand to full width with the front
        expand_geometry = QRect(
            current_geometry.x(),
            current_geometry.y() - 310,
            current_geometry.width(),
            current_geometry.height()
        )
        self.animation2.setStartValue(shrink_geometry)
        self.animation2.setEndValue(expand_geometry)
        self.animation2.valueChanged.connect(self.update_card_front)

        self.animation1.finished.connect(self.start_second_animation)
        self.animation2.finished.connect(lambda: setattr(self, 'animation_running', False))

        # Start shrinking
        self.animation1.start()

    def start_second_animation(self):
        self.animation2.start()
        QTimer.singleShot(300, self.show_sparkles)

    def show_sparkles(self):
        self.sparkle_movie.setScaledSize(QSize(400, 400))
        self.sparkle_label.move(100, 0)
        self.sparkle_label.setVisible(True)
        self.sparkle_movie.start()

        QTimer.singleShot(2000, lambda: self.sparkle_label.setVisible(False))
        self.has_flipped = True

    def update_card_back(self, current_geometry):
        # Scale the "back" image as it shrinks
        self.card_label.setPixmap(
            self.pixmap_back.scaled(max(1, current_geometry.width()), current_geometry.height(), aspectRatioMode=0)
        )

    def update_card_front(self, current_geometry):
        # Scale the "front" image as it expands
        self.card_label.setPixmap(
            self.pixmap_front.scaled(max(1, current_geometry.width()), current_geometry.height(), aspectRatioMode=0)
        )

# ------------------------------ Client ------------------------------ #
class Client:
    """
    Maintains connection logic with the server.
    Distinguishes local_coins vs. server-side user_data["Balance"].
    """
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port

        # Server-side user info
        self.user_data = {
            "ID": None,
            "Username": None,
            "Balance": None,
            "RankPoints": None
        }

        # Local on-hand coins
        self.local_coins = 3000

    def send_dict_as_json_to_server(self, dict_data):
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
        self.user_data = response
        return response

    def register(self, username, password):
        dict_data = {
            "type": "register",
            "username": username,
            "password": password
        }
        response = self.send_dict_as_json_to_server(dict_data)
        return response

    def update_user_data(self):
        """ Refreshes user_data from the server. """
        if self.user_data["ID"] is None:
            return None
        dict_data = {
            "type": "getData",
            "id": self.user_data["ID"]
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response:
            self.user_data = response
        return response

    def deposit(self, amount):
        if amount <= 0 or self.local_coins < amount:
            print(f"Deposit failed: not enough local coins, or invalid amount. (Have {self.local_coins})")
            return None
        dict_data = {
            "type": "deposit",
            "id": self.user_data["ID"],
            "amount": amount
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response is not None:
            self.local_coins -= amount
            self.update_user_data()
        return response

    def withdraw(self, amount):
        if amount <= 0 or (self.user_data["Balance"] is not None and self.user_data["Balance"] < amount):
            print(f"Withdraw failed: not enough balance or invalid amount. (Have {self.user_data['Balance']})")
            return None
        dict_data = {
            "type": "withdraw",
            "id": self.user_data["ID"],
            "amount": amount
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response is not None:
            self.local_coins += amount
            self.update_user_data()
        return response

    def transfer(self, receiver_id, amount):
        if amount <= 0 or (self.user_data["Balance"] < amount):
            print(f"Transfer failed: not enough server balance. (Have {self.user_data['Balance']})")
            return None
        dict_data = {
            "type": "transfer",
            "sender_id": self.user_data["ID"],
            "receiver_id": receiver_id,
            "amount": amount
        }
        response = self.send_dict_as_json_to_server(dict_data)
        if response is True:
            self.update_user_data()
        else:
            print("Server reported transfer failed:", response)
        return response

    def send_card(self, receiver_id, card_id):
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
            print("Server reported send_card failed:", response)
        return response


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
        return self.player_id_input.text(), self.amount_input.text()


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
        return self.player_id_input.text(), self.card_id_input.text()


# ------------------------------ TopBar ------------------------------ #
class TopBar(QWidget):
    """
    Always visible top bar:
      - local coins on the left
      - deposit/withdraw/send coins/send cards
      - user data (ID, Name, server-side Balance, RankPoints) on the right
    """
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.setFixedHeight(80)
        self.init_ui()

    def init_ui(self):
        bar_width = self.parent_widget.width()
        self.setFixedWidth(bar_width)

        coin_path = resource_path("images", "coin.png")
        profile_path = resource_path("images", "profile.png")

        # Local coin image
        self.coin_label = QLabel(self)
        coin_pixmap = QPixmap(coin_path)
        self.coin_label.setPixmap(coin_pixmap)
        self.coin_label.setScaledContents(True)
        self.coin_label.setGeometry(20, 10, 60, 60)

        # Local coin count
        self.local_coins_label = QLabel("Local: ???", self)
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

        # Server user data label
        self.user_data_label = QLabel("""
ID: ?
Name: ?
Balance: ?
RankPoints: ?
""", self)
        self.user_data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_data_label.setGeometry(560, 5, 150, 70)

        # Profile image
        self.profile_label = QLabel(self)
        profile_pixmap = QPixmap(profile_path)
        self.profile_label.setPixmap(profile_pixmap)
        self.profile_label.setScaledContents(True)
        self.profile_label.setGeometry(720, 10, 60, 60)

    def update_display(self, client):
        """
        Update local coins & server user_data
        """
        self.local_coins_label.setText(f"Local: {client.local_coins}")
        if client.user_data["ID"] is not None:
            uid = client.user_data["ID"]
            uname = client.user_data["Username"]
            bal = client.user_data["Balance"]
            rp = client.user_data["RankPoints"]
            text = f"ID: {uid}\nName: {uname}\nBalance: {bal}\nRankedPoints: {rp}"
        else:
            text = """ID: ?\nName: ?\nBalance: ?\nRankedPoints: ?"""

        self.user_data_label.setText(text)


# ------------------------------ MainPage ------------------------------ #
class MainPage(QWidget):
    """
    Main landing page with:
      - Pokeball
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

        # load images
        pokeball_path = resource_path("images", "pokeball.png")
        pointer_path = resource_path("images", "pointer.png")

        # Pokeball Image
        self.pokeball_label = QLabel(self)
        pokeball_pixmap = QPixmap(pokeball_path)
        self.pokeball_label.setPixmap(pokeball_pixmap)
        self.pokeball_label.setScaledContents(True)
        self.pokeball_label.setGeometry(QRect(50, 40, 200, 200))

        # Pointer Image
        self.pointer_label = QLabel(self)
        pointer_pixmap = QPixmap(pointer_path)
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
    """
    Page with three pack buttons and a back button.
    Upon clicking a pack, we:
      - Check local_coins
      - Deduct the cost
      - Send "openPack" to server
      - Get a list of card info
      - Convert to absolute file paths from PokemonCards -> Launch PackAnimationWindow
    """
    def __init__(self, switch_to_main_page_callback, main_window_ref):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.main_window_ref = main_window_ref
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)

        # Pack 1
        self.pack1_button = QPushButton("Pack 1", self)
        self.pack1_button.setGeometry(200, 100, 80, 130)
        self.pack1_button.clicked.connect(lambda: self.open_pack(1, 200))

        # Pack 2
        self.pack2_button = QPushButton("Pack 2", self)
        self.pack2_button.setGeometry(320, 100, 80, 130)
        self.pack2_button.clicked.connect(lambda: self.open_pack(2, 600))

        # Pack 3
        self.pack3_button = QPushButton("Pack 3", self)
        self.pack3_button.setGeometry(440, 100, 80, 130)
        self.pack3_button.clicked.connect(lambda: self.open_pack(3, 3000))

        # Back
        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)

    def open_pack(self, pack_id, cost): #TODO change from gpt
        print(f"openpack({pack_id}, {cost})")
        client = self.main_window_ref.client

        # 1) Check local_coins
        if client.local_coins < cost:
            print("Not enough local coins to buy this pack!")
            return

        # Subtract local_coins for the pack
        client.local_coins -= cost

        # 2) Actually call the server
        dict_data = {
            "type": "openPack",
            "user_id": client.user_data["ID"],
            "pack_id": pack_id
        }
        server_response = client.send_dict_as_json_to_server(dict_data)

        if not server_response:
            print("Open pack returned no cards or an error.")
            return

        # 3) Convert each card to an absolute path from "PokemonCards"
        card_image_paths = []
        for card in server_response:
            # Suppose card[1] is the Name, e.g. "Pikachu"
            card_name = card[1]
            # Build the absolute path. "PokemonCards/Pikachu.jpeg"
            card_abs_path = resource_path("PokemonCards", f"{card_name}.jpeg")
            card_image_paths.append(card_abs_path)

        # 4) Launch the animation window
        self.anim_window = PackAnimationWindow(card_image_paths)
        self.anim_window.show()

        # Refresh the top bar so local_coins is updated
        self.main_window_ref.main_widget_page.top_bar.update_display(client)


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

        # Just placeholders
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
    """
    The main widget after login, containing:
      - A TopBar
      - A QStackedWidget with pages (MainPage, OpenPacksPage, InventoryPage, WagerSearchPage)
    """
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window_ref = main_window_ref
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 1) TopBar
        self.top_bar = TopBar(self)
        layout.addWidget(self.top_bar)

        # 2) Center QStackedWidget
        self.center_stack = QStackedWidget(self)
        layout.addWidget(self.center_stack)

        # Create pages
        self.main_page = MainPage(
            self.show_wager_page,
            self.show_open_packs_page,
            self.show_inventory_page
        )
        self.wager_page = WagerSearchPage(self.show_main_page)
        self.open_packs_page = OpenPacksPage(self.show_main_page, self.main_window_ref)
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
                self.main_window_ref.client.withdraw(amount)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid amount entered.")

    def show_deposit_dialog(self):
        dialog = DepositDialog()
        if dialog.exec_() == QDialog.Accepted:
            amount_str = dialog.get_amount()
            if amount_str.isdigit():
                amount = int(amount_str)
                self.main_window_ref.client.deposit(amount)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid amount entered.")

    def show_send_coins_dialog(self):
        dialog = SendCoinsDialog()
        if dialog.exec_() == QDialog.Accepted:
            player_id_str, amount_str = dialog.get_data()
            if player_id_str.isdigit() and amount_str.isdigit():
                receiver_id = int(player_id_str)
                amount = int(amount_str)
                self.main_window_ref.client.transfer(receiver_id, amount)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid ID or amount.")

    def show_send_cards_dialog(self):
        dialog = SendCardsDialog()
        if dialog.exec_() == QDialog.Accepted:
            player_id_str, card_id_str = dialog.get_data()
            if player_id_str.isdigit() and card_id_str.isdigit():
                receiver_id = int(player_id_str)
                card_id = int(card_id_str)
                self.main_window_ref.client.send_card(receiver_id, card_id)
                self.top_bar.update_display(self.main_window_ref.client)
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


# ------------------------------ LoginRegisterUI ------------------------------ #
class LoginRegisterUI(QWidget):
    """
    The login/register page. On success, calls main_window_ref.show_main_widget().
    """
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window_ref = main_window_ref
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

        response = self.main_window_ref.client.login(username, password)
        if response["ID"] is not None:
            self.main_window_ref.show_main_widget()
        else:
            print("Login failed!")

    def handle_register(self):
        username = self.register_name_input.text()
        password = self.register_password_input.text()

        if not username or not password:
            print("Username or password is empty!")
            return

        reg_response = self.main_window_ref.client.register(username, password)
        if reg_response is True or reg_response == 1:
            # auto-login
            login_response = self.main_window_ref.client.login(username, password)
            if login_response["ID"] is not None:
                self.main_window_ref.show_main_widget()
            else:
                print("Login after registration failed!")
        else:
            print("Registration failed or username taken!")


# ------------------------------ MainWindow ------------------------------ #
class MainWindow(QWidget):
    """
    The top-level window. Contains:
      - A QStackedWidget with the login/register page at index 0
      - The main widget (with top bar & pages) at index 1
    """
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

        # Start on the login page
        self.stacked_widget.setCurrentIndex(0)

    def show_main_widget(self):
        """
        After successful login or register, switch to the main interface and refresh display.
        """
        self.main_widget_page.top_bar.update_display(self.client)
        self.stacked_widget.setCurrentIndex(1)


# ------------------------------ main() ------------------------------ #
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
