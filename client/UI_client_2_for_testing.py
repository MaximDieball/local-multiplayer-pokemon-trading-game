import sys
import os
import socket
import json
import zlib
import random
import threading
from PyQt5.QtCore import pyqtSignal, QObject
import sqlite3
import functools

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QDialog, QDialogButtonBox,
    QGridLayout, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PyQt5.QtGui import QPixmap, QMovie, QTransform, QImage, QIcon


##############################################################################
# Global StyleSheets
##############################################################################


def resource_path(*relative_parts):
    """
    Returns an absolute path based on the directory of this script.
    Example: resource_path("images", "back.png") -> absolute path to images/back.png
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, *relative_parts)


################################################################################
# PackAnimationWindow
################################################################################

class PackAnimationWindow(QMainWindow):
    """
    A window that flips each card image from a provided list of file paths.
    The user clicks to flip the top card from "back.png" to the front image.
    Sparkles appear briefly after the flip. Each click reveals the next card.
    """

    def __init__(self, card_paths):
        print("PackAnimationWindow INNIT")
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
        self.sparkle_label.setVisible(False)  # hide sparkles

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


################################################################################
# Client
################################################################################

class Client:
    def __init__(self, host='192.168.42.1', port=17777, wager_port=27777):
        self.host = host
        self.port = port
        self.wager_port = wager_port
        self.user_data = {"ID": None, "Username": None, "Balance": None, "RankPoints": None}
        self.deck = []
        self.local_coins = 20

    def set_host(self, new_host):
        """
        Sets a new host IP address for the client.
        """
        self.host = new_host
        print(f"Client host updated to: {self.host}")

    def remove_card_from_deck(self, card_name):
        if card_name in self.deck:
            self.deck.remove(card_name)

    def add_card_to_deck(self, card_name):
        if card_name not in self.deck and len(self.deck) < 6:
            self.deck.append(card_name)
        else:
            print("ERROR: deck is too long or card is already in deck")

    def send_dict_as_json_to_server(self, dict_data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))

        json_data = json.dumps(dict_data)
        s.sendall(json_data.encode('utf-8'))

        compressed_response = s.recv(4096)
        response_data = json.loads(zlib.decompress(compressed_response).decode('utf-8'))

        s.close()
        return response_data

    def login(self, username, password):
        dict_data = {"type": "login", "username": username, "password": password}
        resp = self.send_dict_as_json_to_server(dict_data)
        self.user_data = resp
        return resp

    def register(self, username, password):
        dict_data = {"type": "register", "username": username, "password": password}
        return self.send_dict_as_json_to_server(dict_data)

    def update_user_data(self):
        if self.user_data["ID"] is None:
            return None
        dict_data = {"type": "getData", "id": self.user_data["ID"]}
        resp = self.send_dict_as_json_to_server(dict_data)
        if resp:
            self.user_data = resp
        return resp

    def deposit(self, amount):
        if amount <= 0 or self.local_coins < amount:
            print(f"Deposit failed: not enough local coins, or invalid amount. (Have {self.local_coins})")
            return None
        dict_data = {"type": "deposit", "id": self.user_data["ID"], "amount": amount}
        resp = self.send_dict_as_json_to_server(dict_data)
        if resp is not None:
            self.local_coins -= amount
            self.update_user_data()
        return resp

    def withdraw(self, amount):
        if amount <= 0 or (self.user_data["Balance"] is not None and self.user_data["Balance"] < amount):
            print("Withdraw failed: not enough balance or invalid amount.")
            return None
        dict_data = {"type": "withdraw", "id": self.user_data["ID"], "amount": amount}
        resp = self.send_dict_as_json_to_server(dict_data)
        if resp is not None:
            self.local_coins += amount
            self.update_user_data()
        return resp

    def transfer(self, receiver_id, amount):
        if amount <= 0 or (self.user_data["Balance"] < amount):
            print("Transfer failed: not enough server balance.")
            return None
        dict_data = {
            "type": "transfer",
            "sender_id": self.user_data["ID"],
            "receiver_id": receiver_id,
            "amount": amount
        }
        resp = self.send_dict_as_json_to_server(dict_data)
        if resp is True:
            self.update_user_data()
        else:
            print("Server reported transfer failed:", resp)
        return resp

    def send_card(self, receiver_id, card_id):
        dict_data = {
            "type": "sendCard",
            "user_id": self.user_data["ID"],
            "receiver_id": receiver_id,
            "card_id": card_id
        }
        resp = self.send_dict_as_json_to_server(dict_data)
        if resp is True:
            self.update_user_data()
        else:
            print("Server reported send_card failed:", resp)
        return resp


################################################################################
# Dialogs
################################################################################

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


class CardDataDialog(QDialog):
    def __init__(self, data, client, inventory_page):
        super().__init__()
        self.setWindowTitle("CardData")
        self.setFixedSize(500, 300)

        self.client = client
        self.inventory_page = inventory_page

        layout = QVBoxLayout()
        data_label = QLabel(
            f"<b>ID:</b> {data[0]}<br>"
            f"<b>Name:</b> {data[1]}<br>"
            f"<b>Type:</b> {data[2]}<br>"
            f"<b>Attack One:</b> {data[3]}<br>"
            f"<b>Attack Two:</b> {data[5] if data[5] != '-' else 'N/A'}<br>"
            f"<b>HP:</b> {data[12]}<br>"
            f"<b>Energy Cost (A1):</b> {data[7]}<br>"
            f"<b>Damage (A1):</b> {data[4]}<br>"
            f"<b>Energy Cost (A2):</b> {data[8] if data[8] != 0 else 'N/A'}<br>"
            f"<b>Damage (A2):</b> {data[6] if data[6] != 0 else 'N/A'}<br>"
            f"<b>Weakness:</b> {data[9]}<br>"
            f"<b>Resistance:</b> {data[10]}<br>"
            f"<b>Retreat Cost:</b> {data[11]}<br>"
            f"<b>Rarity:</b> {data[13]}",
            self
        )
        layout.addWidget(data_label)
        self.setLayout(layout)

        card_name = data[1]
        if card_name in client.deck:
            remove_btn = QPushButton("remove from deck", self)
            remove_btn.clicked.connect(lambda: [client.remove_card_from_deck(card_name), self.close()])
            layout.addWidget(remove_btn)
        else:
            add_btn = QPushButton("add to deck", self)
            add_btn.clicked.connect(lambda: [client.add_card_to_deck(card_name), self.close()])
            layout.addWidget(add_btn)

    def closeEvent(self, event):
        self.inventory_page.refresh_inventory()
        super().closeEvent(event)


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


################################################################################
# TopBar
################################################################################

class TopBar(QWidget):
    """
    The top bar of the main application window displaying user information and actions.
    Includes local coins, deposit/withdraw buttons, send coins/cards buttons, and user data.
    """

    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.setFixedHeight(80)
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components of the top bar.
        """
        bar_width = self.parent_widget.width()
        self.setFixedWidth(bar_width)

        coin_path = resource_path("images", "coin.png")
        profile_path = resource_path("images", "profile.png")

        # Coin icon
        self.coin_label = QLabel(self)
        coin_pixmap = QPixmap(coin_path)
        self.coin_label.setPixmap(coin_pixmap)
        self.coin_label.setScaledContents(True)
        self.coin_label.setGeometry(20, 10, 60, 60)

        # Local coins display
        self.local_coins_label = QLabel("Local: ???", self)
        self.local_coins_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.local_coins_label.setGeometry(90, 25, 100, 30)

        # Deposit button
        self.deposit_button = QPushButton("Deposit", self)
        self.deposit_button.setGeometry(190, 25, 80, 30)
        self.deposit_button.clicked.connect(self.parent_widget.show_deposit_dialog)

        # Withdraw button
        self.withdraw_button = QPushButton("Withdraw", self)
        self.withdraw_button.setGeometry(280, 25, 80, 30)
        self.withdraw_button.clicked.connect(self.parent_widget.show_withdraw_dialog)

        # Send coins button
        self.send_coins_button = QPushButton("Send coins", self)
        self.send_coins_button.setGeometry(370, 25, 80, 30)
        self.send_coins_button.clicked.connect(self.parent_widget.show_send_coins_dialog)

        # Send cards button
        self.send_cards_button = QPushButton("Send cards", self)
        self.send_cards_button.setGeometry(460, 25, 80, 30)
        self.send_cards_button.clicked.connect(self.parent_widget.show_send_cards_dialog)

        # User data display
        self.user_data_label = QLabel("""
                                    ID: ?
                                    Name: ?
                                    Balance: ?
                                    RankPoints: ?
                                    """, self)
        self.user_data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_data_label.setGeometry(560, 5, 150, 70)

        # Profile icon
        self.profile_label = QLabel(self)
        profile_pixmap = QPixmap(profile_path)
        self.profile_label.setPixmap(profile_pixmap)
        self.profile_label.setScaledContents(True)
        self.profile_label.setGeometry(720, 10, 60, 60)

    def update_display(self, client):
        """
        Updates the top bar display with the latest client data.
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


################################################################################
# MainPage
################################################################################

class MainPage(QWidget):
    """
    The main landing page of the application with options to open packs, view inventory, or engage in wagers.
    """

    def __init__(self, switch_to_wager_page_callback, switch_to_open_packs_page_callback,
                 switch_to_inventory_page_callback):
        super().__init__()
        self.switch_to_wager_page_callback = switch_to_wager_page_callback
        self.switch_to_open_packs_page_callback = switch_to_open_packs_page_callback
        self.switch_to_inventory_page_callback = switch_to_inventory_page_callback
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components of the main page.
        """
        self.setFixedSize(800, 420)

        # Pokeball image
        pokeball_path = resource_path("images", "pokeball.png")
        pointer_path = resource_path("images", "pointer.png")

        self.pokeball_label = QLabel(self)
        pokeball_pixmap = QPixmap(pokeball_path)
        self.pokeball_label.setPixmap(pokeball_pixmap)
        self.pokeball_label.setScaledContents(True)
        self.pokeball_label.setGeometry(QRect(50, 40, 200, 200))
        self.pokeball_original_geom = self.pokeball_label.geometry()

        # Pointer image
        self.pointer_label = QLabel(self)
        pointer_pixmap = QPixmap(pointer_path)
        transform = QTransform()
        transform.rotate(-45)
        rotated_pointer = pointer_pixmap.transformed(transform, Qt.SmoothTransformation)
        self.pointer_label.setPixmap(rotated_pointer)
        self.pointer_label.setScaledContents(True)
        self.pointer_label.setGeometry(QRect(180, 180, 50, 50))

        # Open packs button
        self.open_packs_button = QPushButton("Open packs", self)
        self.open_packs_button.setGeometry(QRect(350, 20, 200, 100))
        self.open_packs_button.clicked.connect(self.switch_to_open_packs_page_callback)

        # Inventory button
        self.inventory_button = QPushButton("Inventory", self)
        self.inventory_button.setGeometry(QRect(350, 120, 200, 100))
        self.inventory_button.clicked.connect(self.switch_to_inventory_page_callback)

        # Wager button
        self.wager_button = QPushButton("Wager", self)
        self.wager_button.setGeometry(QRect(350, 220, 200, 100))
        self.wager_button.clicked.connect(self.switch_to_wager_page_callback)

        # Connect the pokeball click event
        self.pokeball_label.mousePressEvent = self.pokeball_clicked

    def pokeball_clicked(self, event):
        """
        Handles the event when the pokeball image is clicked.
        Increments local coins and updates the display with an animation.
        """
        if event.button() == Qt.LeftButton:
            mw = self.parentWidget().parentWidget()  # Access MainWindow
            client = mw.client
            client.local_coins += 1
            self.animate_pokeball()
            mw.top_bar.update_display(client)
        QLabel.mousePressEvent(self.pokeball_label, event)

    def animate_pokeball(self):
        """
        Animates the pokeball image by shrinking and then restoring its size.
        """
        orig_rect = self.pokeball_original_geom
        x, y, w, h = orig_rect.x(), orig_rect.y(), orig_rect.width(), orig_rect.height()

        shrink_factor = 0.9
        shrink_w = int(w * shrink_factor)
        shrink_h = int(h * shrink_factor)
        cx = x + w // 2
        cy = y + h // 2
        new_x = cx - (shrink_w // 2)
        new_y = cy - (shrink_h // 2)

        self.pokeball_label.setGeometry(new_x, new_y, shrink_w, shrink_h)

        # Animation to restore the pokeball to its original size
        self.anim_restore = QPropertyAnimation(self.pokeball_label, b"geometry")
        self.anim_restore.setDuration(200)
        self.anim_restore.setStartValue(QRect(new_x, new_y, shrink_w, shrink_h))
        self.anim_restore.setEndValue(orig_rect)
        self.anim_restore.setEasingCurve(QEasingCurve.OutBack)
        self.anim_restore.start()


################################################################################
# OpenPacksPage
################################################################################

class OpenPacksPage(QWidget):
    """
    Page allowing users to open different types of Pokémon card packs.
    Each pack type has an associated coin cost.
    """

    def __init__(self, switch_to_main_page_callback, main_window_ref):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.main_window_ref = main_window_ref
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components of the Open Packs page.
        """
        self.setFixedSize(800, 420)

        # Default Pack button
        self.pack1_button = QPushButton("Default Pack\n100 Coins", self)
        self.pack1_button.setGeometry(QRect(200, 80, 120, 200))
        self.pack1_button.clicked.connect(lambda: self.open_pack(1, 100))

        # SUPER Pack button
        self.pack2_button = QPushButton("SUPER Pack\n300 Coins", self)
        self.pack2_button.setGeometry(QRect(350, 80, 120, 200))
        self.pack2_button.clicked.connect(lambda: self.open_pack(2, 300))

        # HOLO Pack button
        self.pack3_button = QPushButton("HOLO Pack\n600 Coins", self)
        self.pack3_button.setGeometry(QRect(500, 80, 120, 200))
        self.pack3_button.clicked.connect(lambda: self.open_pack(3, 600))

        # Back button to return to the main page
        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)

    def open_pack(self, pack_id, cost):
        """
        Handles the logic for opening a pack of a specific type and cost.
        """
        print(f"open_pack({pack_id}, {cost})")
        c = self.main_window_ref.client
        if c.local_coins < cost:
            print("Not enough local coins!")
            QMessageBox.warning(
                self,
                "Insufficient Coins",
                "You do not have enough local coins to open this pack.",
                QMessageBox.Ok
            )
            return
        c.local_coins -= cost
        dict_data = {"type": "openPack", "user_id": c.user_data["ID"], "pack_id": pack_id}
        sr = c.send_dict_as_json_to_server(dict_data)
        if not sr:
            print("Open pack returned no cards or error.")
            QMessageBox.warning(
                self,
                "Error",
                "Failed to open the pack. Please try again later.",
                QMessageBox.Ok
            )
            return

        # Sort the received pack based on rarity
        sorted_pack = []
        print("Sorting pack based on rarity...")
        for card in sr:
            if card[11] == "Common":
                sorted_pack.append(card)
        for card in sr:
            if card[11] == "Uncommon":
                sorted_pack.append(card)
        for card in sr:
            if card[11] == "Rare":
                sorted_pack.append(card)
        for card in sr:
            if card[11] == "HoloRare":
                sorted_pack.append(card)

        # Collect paths to card images
        paths = []
        for card in sorted_pack:
            cn = card[1]
            path = resource_path("PokemonCards", f"{cn}.jpeg")
            paths.append(path)

        # Display the pack opening animation
        self.anim_window = PackAnimationWindow(paths)
        self.anim_window.show()
        self.main_window_ref.main_widget_page.top_bar.update_display(c)


################################################################################
# CardLabel
################################################################################

class CardLabel(QLabel):
    """
    Custom QLabel to represent a Pokémon card in the inventory.
    Handles display differences for duplicate cards and interactions.
    """

    def __init__(self, is_duplicate, card_info, client, pixmap, inventory_page, parent=None):
        super().__init__(parent)
        self.card_info = card_info
        self.client = client
        self.inventory_page = inventory_page

        # Display the card image; grayscale if duplicate
        if not is_duplicate:
            self.setPixmap(pixmap)
        else:
            img = pixmap.toImage()
            gray = img.convertToFormat(QImage.Format_Grayscale8)
            p2 = QPixmap.fromImage(gray)
            self.setPixmap(p2)

        # Highlight card if it's in the deck
        if card_info[1] in client.deck and not is_duplicate:
            self.setStyleSheet("border: 3px solid blue; background: white; margin: 5px;")
        else:
            self.setStyleSheet("border: 1px solid gray; background: white; margin: 5px;")

    def mousePressEvent(self, event):
        """
        Handles mouse click events on the card.
        Opens the CardDataDialog for the selected card.
        """
        if event.button() == Qt.LeftButton:
            dlg = CardDataDialog(self.card_info, self.client, self.inventory_page)
            dlg.exec_()
        super().mousePressEvent(event)


################################################################################
# InventoryPage
################################################################################

class InventoryPage(QWidget):
    """
    Page displaying the user's inventory of Pokémon cards.
    Allows users to view and manage their cards.
    """

    def __init__(self, switch_to_main_page_callback, card_data, client):
        super().__init__()
        self.client = client
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.card_data = card_data
        self.setFixedSize(800, 420)

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Scroll area to accommodate many cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.container.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.container)

        self.build_grid()

        # Back button to return to the main page
        self.back_button = QPushButton("<---")
        self.back_button.setMaximumWidth(80)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)
        self.main_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)

    def build_grid(self):
        """
        Constructs the grid layout of cards in the inventory.
        Sorts cards by rarity and displays them accordingly.
        """
        # Clear existing widgets in the grid
        for i in reversed(range(self.grid_layout.count())):
            wdg = self.grid_layout.itemAt(i).widget()
            if wdg:
                wdg.setParent(None)
                wdg.deleteLater()

        rarity_rank = {"Common": 0, "Uncommon": 1, "Rare": 2, "HoloRare": 3}

        def sort_key(card):
            """
            Sorting key based on card rarity and name.
            """
            return (rarity_rank.get(card[11], 99), card[1])

        sorted_cards = sorted(self.card_data, key=sort_key)
        seen_names = set()
        row, col = 0, 0

        # Iterate through sorted cards and add them to the grid
        for cinfo in sorted_cards:
            cname = cinfo[1]
            ppath = resource_path("PokemonCards", f"{cname}.jpeg")
            pix = QPixmap(ppath).scaled(119, 149, Qt.KeepAspectRatio)
            is_dup = cname in seen_names
            if not is_dup:
                seen_names.add(cname)

            clabel = CardLabel(is_dup, cinfo, self.client, pix, self)
            clabel.setMinimumSize(120, 160)
            clabel.setMaximumSize(120, 160)
            self.grid_layout.addWidget(clabel, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def refresh_inventory(self):
        """
        Refreshes the inventory display to reflect any changes.
        """
        self.build_grid()


################################################################################
# WagerSearchPage
################################################################################

class WagerSearchPage(QWidget):
    """
    Page allowing users to search for opponents to engage in wagers.
    Users can specify the enemy player ID.
    """

    def __init__(self, switch_to_main_page_callback, wager_client):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.init_ui()
        self.wager_client = wager_client

    def init_ui(self):
        """
        Initializes the UI components of the Wager Search page.
        """
        self.setFixedSize(800, 420)

        # Enemy Player ID input
        self.enemy_label = QLabel("Enemy Player ID:", self)
        self.enemy_label.setGeometry(289, 120, 100, 25)

        self.enemy_input = QLineEdit(self)
        self.enemy_input.setGeometry(398, 120, 120, 25)

        # Search button to initiate the wager
        self.search_button = QPushButton("Search", self)
        self.search_button.setGeometry(363, 270, 80, 30)
        self.search_button.clicked.connect(self.start_search)

        # Back button to return to the main page
        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.stop_search_and_go_back_to_main_page)

    def start_search(self):
        """
        Initiates the search for an opponent based on the entered enemy ID.
        """
        enemy_id_str = self.enemy_input.text().strip()

        # Validate inputs
        if not enemy_id_str.isdigit():
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter valid numeric values for Enemy ID",
                QMessageBox.Ok
            )
            return

        enemy_id = int(enemy_id_str)

        # Initiate the search through the WagerClient
        self.wager_client.connect()
        self.wager_client.stop_search()

        self.wager_client.search(enemy_id)
        self.search_button.setText("Confirm")

    def stop_search_and_go_back_to_main_page(self):
        """
        Stops the search and navigates back to the main page.
        """
        self.wager_client.stop_search()
        self.switch_to_main_page_callback()


################################################################################
# MainWidget
################################################################################

class MainWidget(QWidget):
    """
    The central widget of the application containing the top bar and stacked pages.
    Manages navigation between different pages and handles user interactions.
    """

    def __init__(self, main_window_ref, client):
        super().__init__()
        self.main_window_ref = main_window_ref
        self.client = client

        # Initialize WagerClient and connect signals
        self.wager_client = WagerClient(self.client, self.client.host)
        self.wager_client.startSignal.connect(self.show_wager_window)
        self.wager_client.matchResultSignal.connect(self.handle_match_result)  # Updated signal

        self.setFixedSize(800, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Top bar displaying user info and actions
        self.top_bar = TopBar(self)
        layout.addWidget(self.top_bar)

        # Stacked widget to manage different pages
        self.center_stack = QStackedWidget(self)
        layout.addWidget(self.center_stack)

        # Initialize different pages
        self.main_page = MainPage(
            self.show_wager_page,
            self.show_open_packs_page,
            self.show_inventory_page
        )
        self.wager_page = WagerSearchPage(self.show_main_page, self.wager_client)
        self.open_packs_page = OpenPacksPage(self.show_main_page, self.main_window_ref)
        self.inventory_page = InventoryPage(self.show_main_page, [], self.client)

        # Add pages to the stack
        self.center_stack.addWidget(self.main_page)
        self.center_stack.addWidget(self.wager_page)
        self.center_stack.addWidget(self.open_packs_page)
        self.center_stack.addWidget(self.inventory_page)

        # Set the initial page
        self.center_stack.setCurrentWidget(self.main_page)

    def show_wager_window(self):
        """
        Displays the WagerWindow for engaging in wagers.
        """
        print("show_wager_window")
        self.show_main_page()
        # Create the WagerWindow and pass in the WagerClient and deck
        self.wager_window = WagerWindow(self.wager_client, self.client.deck)
        self.wager_window.show()
        print("Connecting enemyCardChangeSignal to WagerWindow")
        # Connect the WagerClient's enemyCardChangeSignal to the WagerWindow's slot
        self.wager_client.enemyCardChangeSignal.connect(self.wager_window.change_enemy_card)

    def show_withdraw_dialog(self):
        """
        Opens the WithdrawDialog for the user to input withdrawal amount.
        """
        dlg = WithdrawDialog()
        if dlg.exec_() == QDialog.Accepted:
            amt_str = dlg.get_amount()
            if amt_str.isdigit():
                amt = int(amt_str)
                self.main_window_ref.client.withdraw(amt)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid amount entered.")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter a valid numeric amount.",
                    QMessageBox.Ok
                )

    def show_deposit_dialog(self):
        """
        Opens the DepositDialog for the user to input deposit amount.
        """
        dlg = DepositDialog()
        if dlg.exec_() == QDialog.Accepted:
            amt_str = dlg.get_amount()
            if amt_str.isdigit():
                amt = int(amt_str)
                self.main_window_ref.client.deposit(amt)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid amount entered.")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter a valid numeric amount.",
                    QMessageBox.Ok
                )

    def show_send_coins_dialog(self):
        """
        Opens the SendCoinsDialog for the user to send coins to another player.
        """
        dlg = SendCoinsDialog()
        if dlg.exec_() == QDialog.Accepted:
            pid_str, amt_str = dlg.get_data()
            if pid_str.isdigit() and amt_str.isdigit():
                rid = int(pid_str)
                a = int(amt_str)
                self.main_window_ref.client.transfer(rid, a)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid ID or amount.")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter valid numeric values for ID and amount.",
                    QMessageBox.Ok
                )

    def show_send_cards_dialog(self):
        """
        Opens the SendCardsDialog for the user to send cards to another player.
        """
        dlg = SendCardsDialog()
        if dlg.exec_() == QDialog.Accepted:
            pid_str, cid_str = dlg.get_data()
            if pid_str.isdigit() and cid_str.isdigit():
                rid = int(pid_str)
                cid = int(cid_str)
                self.main_window_ref.client.send_card(rid, cid)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid ID or card ID.")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter valid numeric values for ID and Card ID.",
                    QMessageBox.Ok
                )

    def show_main_page(self):
        """
        Navigates back to the main page.
        """
        self.center_stack.setCurrentWidget(self.main_page)

    def show_wager_page(self):
        """
        Navigates to the Wager Search page if the deck is complete.
        Otherwise, alerts the user to complete the deck.
        """
        if len(self.client.deck) == 6:
            self.center_stack.setCurrentWidget(self.wager_page)
        else:
            QMessageBox.information(
                self,
                "Deck Incomplete",
                "You need 6 Pokémon in your Deck to play!",
                QMessageBox.Ok
            )

    def show_open_packs_page(self):
        """
        Navigates to the Open Packs page.
        """
        self.center_stack.setCurrentWidget(self.open_packs_page)

    def show_inventory_page(self):
        """
        Fetches and displays the user's inventory of Pokémon cards.
        """
        uid = self.main_window_ref.client.user_data["ID"]
        if uid is None:
            print("No user logged in, cannot fetch inventory.")
            QMessageBox.warning(
                self,
                "Not Logged In",
                "You must be logged in to view your inventory.",
                QMessageBox.Ok
            )
            return

        dict_data = {"type": "inventory", "user_id": uid}
        sr = self.main_window_ref.client.send_dict_as_json_to_server(dict_data)
        if not sr:
            print("No inventory data returned or error.")
            QMessageBox.warning(
                self,
                "Error",
                "Failed to retrieve inventory data. \n OPEN PACKS FIRST",
                QMessageBox.Ok
            )
            return

        # Refresh the inventory page with new data
        idx = self.center_stack.indexOf(self.inventory_page)
        if idx != -1:
            self.center_stack.removeWidget(self.inventory_page)
            self.inventory_page.deleteLater()

        self.inventory_page = InventoryPage(self.show_main_page, sr, self.client)
        self.center_stack.addWidget(self.inventory_page)
        self.center_stack.setCurrentWidget(self.inventory_page)

    def handle_match_result(self, win):
        """
        Handles the match result by displaying appropriate messages and closing the wager window.
        """
        if win:
            QMessageBox.information(
                self.wager_window,
                "Victory",
                "Congratulations! You won the match!",
                QMessageBox.Ok
            )
        # self.wager_window.close()


################################################################################
# LoginRegisterUI
################################################################################

class LoginRegisterUI(QWidget):
    """
    The login and registration interface allowing users to authenticate or create a new account.
    Also provides an input field to change the server IP address.
    """

    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window_ref = main_window_ref
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components of the Login/Register page.
        """
        w, h = 800, 400
        self.setFixedSize(w, h)

        half_width = w // 2
        left_x = half_width - 220
        right_x = half_width + 20

        # 1. Server IP Input Field
        server_ip_label = QLabel("Server IP:", self)
        server_ip_label.setGeometry(QRect(half_width - 100, 370, 80, 30))

        self.server_ip_input = QLineEdit(self)
        self.server_ip_input.setGeometry(QRect(half_width - 20, 370, 160, 30))
        self.server_ip_input.setText("127.0.0.1")  # Default IP

        # 2. LOGIN Section
        login_label = QLabel("Login", self)
        login_label.setGeometry(QRect(left_x, 70, 100, 30))

        login_name_label = QLabel("Name:", self)
        login_name_label.setGeometry(QRect(left_x, 110, 60, 20))

        self.login_name_input = QLineEdit(self)
        self.login_name_input.setGeometry(QRect(left_x + 65, 110, 150, 20))

        login_password_label = QLabel("Password:", self)
        login_password_label.setGeometry(QRect(left_x, 150, 60, 20))

        self.login_password_input = QLineEdit(self)
        self.login_password_input.setGeometry(QRect(left_x + 65, 150, 150, 20))
        self.login_password_input.setEchoMode(QLineEdit.Password)  # Hide password input

        login_button = QPushButton("Login", self)
        login_button.setGeometry(QRect(left_x, 190, 80, 30))
        login_button.clicked.connect(self.handle_login)

        # 3. REGISTER Section
        register_label = QLabel("Register", self)
        register_label.setGeometry(QRect(right_x, 70, 100, 30))

        register_name_label = QLabel("Name:", self)
        register_name_label.setGeometry(QRect(right_x, 110, 60, 20))

        self.register_name_input = QLineEdit(self)
        self.register_name_input.setGeometry(QRect(right_x + 65, 110, 150, 20))

        register_password_label = QLabel("Password:", self)
        register_password_label.setGeometry(QRect(right_x, 150, 60, 20))

        self.register_password_input = QLineEdit(self)
        self.register_password_input.setGeometry(QRect(right_x + 65, 150, 150, 20))
        self.register_password_input.setEchoMode(QLineEdit.Password)  # Hide password input

        register_button = QPushButton("Register", self)
        register_button.setGeometry(QRect(right_x, 190, 80, 30))
        register_button.clicked.connect(self.handle_register)

    def handle_login(self):
        """
        Handles the login process by validating inputs and communicating with the server.
        """
        server_ip = self.server_ip_input.text().strip()
        username = self.login_name_input.text().strip()
        password = self.login_password_input.text().strip()

        # Check for empty fields
        if not server_ip or not username or not password:
            print("Server IP, username, or password is empty!")
            QMessageBox.warning(
                self,
                "Input Error",
                "Please fill in all fields.",
                QMessageBox.Ok
            )
            return

        # Validate server IP format
        if not self.validate_ip(server_ip):
            print("Invalid Server IP address!")
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter a valid IP address.",
                QMessageBox.Ok
            )
            return

        # Update the client's host with the entered IP address
        self.main_window_ref.client.host = server_ip

        # Attempt to log in
        resp = self.main_window_ref.client.login(username, password)
        if resp and resp.get("ID") is not None:
            self.main_window_ref.show_main_widget()
        else:
            print("Login failed!")
            QMessageBox.warning(
                self,
                "Login Failed",
                "Invalid username or password.",
                QMessageBox.Ok
            )

    def handle_register(self):
        """
        Handles the registration process by validating inputs and communicating with the server.
        """
        server_ip = self.server_ip_input.text().strip()
        username = self.register_name_input.text().strip()
        password = self.register_password_input.text().strip()

        # Check for empty fields
        if not server_ip or not username or not password:
            print("Server IP, username, or password is empty!")
            QMessageBox.warning(
                self,
                "Input Error",
                "Please fill in all fields.",
                QMessageBox.Ok
            )
            return

        # Validate server IP format
        if not self.validate_ip(server_ip):
            print("Invalid Server IP address!")
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter a valid IP address.",
                QMessageBox.Ok
            )
            return

        # Update the client's host with the entered IP address
        self.main_window_ref.client.host = server_ip

        # Attempt to register
        reg_resp = self.main_window_ref.client.register(username, password)
        if reg_resp is True or reg_resp == 1:
            # Automatically log in after successful registration
            login_resp = self.main_window_ref.client.login(username, password)
            if login_resp and login_resp.get("ID") is not None:
                self.main_window_ref.show_main_widget()
            else:
                print("Login after registration failed!")
                QMessageBox.warning(
                    self,
                    "Login Failed",
                    "Unable to login after registration.",
                    QMessageBox.Ok
                )
        else:
            print("Registration failed or username taken!")
            QMessageBox.warning(
                self,
                "Registration Failed",
                "Username may already be taken.",
                QMessageBox.Ok
            )

    def validate_ip(self, ip_str):
        """
        Validates the format of an IPv4 address.
        Returns True if valid, False otherwise.
        """
        parts = ip_str.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            i = int(part)
            if i < 0 or i > 255:
                return False
        return True


################################################################################
# MainWindow
################################################################################

class MainWindow(QWidget):
    """
    The main application window managing the login/register interface and the main widget.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pokémon Wager Application')
        self.setGeometry(100, 100, 800, 500)
        self.setFixedSize(800, 500)

        self.client = Client()  # Initialize the client

        self.stacked_widget = QStackedWidget(self)

        # Initialize the login/register and main widget pages
        self.login_register_page = LoginRegisterUI(self)
        self.main_widget_page = MainWidget(self, self.client)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.login_register_page)
        self.stacked_widget.addWidget(self.main_widget_page)

        # Set up the main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Display the login/register page initially
        self.stacked_widget.setCurrentIndex(0)

    def show_main_widget(self):
        """
        Switches the view to the main widget page after successful login/register.
        """
        self.main_widget_page.top_bar.update_display(self.client)
        self.stacked_widget.setCurrentIndex(1)


################################################################################
# LoginRegisterUI
################################################################################

class LoginRegisterUI(QWidget):
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

        # 1. Add Server IP Input
        server_ip_label = QLabel("Server IP:", self)
        server_ip_label.setGeometry(QRect(half_width - 100, 370, 80, 30))

        self.server_ip_input = QLineEdit(self)
        self.server_ip_input.setGeometry(QRect(half_width - 20, 370, 160, 30))
        self.server_ip_input.setText("127.0.0.1")  # Default IP

        # 2. LOGIN Section
        login_label = QLabel("Login", self)
        login_label.setGeometry(QRect(left_x, 70, 100, 30))

        login_name_label = QLabel("Name:", self)
        login_name_label.setGeometry(QRect(left_x, 110, 60, 20))

        self.login_name_input = QLineEdit(self)
        self.login_name_input.setGeometry(QRect(left_x + 65, 110, 150, 20))

        login_password_label = QLabel("Password:", self)
        login_password_label.setGeometry(QRect(left_x, 150, 60, 20))

        self.login_password_input = QLineEdit(self)
        self.login_password_input.setGeometry(QRect(left_x + 65, 150, 150, 20))
        self.login_password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login", self)
        login_button.setGeometry(QRect(left_x, 190, 80, 30))
        login_button.clicked.connect(self.handle_login)

        # 3. REGISTER Section
        register_label = QLabel("Register", self)
        register_label.setGeometry(QRect(right_x, 70, 100, 30))

        register_name_label = QLabel("Name:", self)
        register_name_label.setGeometry(QRect(right_x, 110, 60, 20))

        self.register_name_input = QLineEdit(self)
        self.register_name_input.setGeometry(QRect(right_x + 65, 110, 150, 20))

        register_password_label = QLabel("Password:", self)
        register_password_label.setGeometry(QRect(right_x, 150, 60, 20))

        self.register_password_input = QLineEdit(self)
        self.register_password_input.setGeometry(QRect(right_x + 65, 150, 150, 20))
        self.register_password_input.setEchoMode(QLineEdit.Password)

        register_button = QPushButton("Register", self)
        register_button.setGeometry(QRect(right_x, 190, 80, 30))
        register_button.clicked.connect(self.handle_register)

    def handle_login(self):
        server_ip = self.server_ip_input.text().strip()
        username = self.login_name_input.text().strip()
        password = self.login_password_input.text().strip()

        if not server_ip or not username or not password:
            print("Server IP, username, or password is empty!")
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.", QMessageBox.Ok)
            return

        # Validate server_ip
        if not self.validate_ip(server_ip):
            print("Invalid Server IP address!")
            QMessageBox.warning(self, "Input Error", "Please enter a valid IP address.", QMessageBox.Ok)
            return

        # Set the client's host to the entered server_ip
        self.main_window_ref.client.host = server_ip

        resp = self.main_window_ref.client.login(username, password)
        if resp.get("ID") is not None:
            self.main_window_ref.show_main_widget()
        else:
            print("Login failed!")
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.", QMessageBox.Ok)

    def handle_register(self):
        server_ip = self.server_ip_input.text().strip()
        username = self.register_name_input.text().strip()
        password = self.register_password_input.text().strip()

        if not server_ip or not username or not password:
            print("Server IP, username, or password is empty!")
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.", QMessageBox.Ok)
            return

        # Validate server_ip
        if not self.validate_ip(server_ip):
            print("Invalid Server IP address!")
            QMessageBox.warning(self, "Input Error", "Please enter a valid IP address.", QMessageBox.Ok)
            return

        # Set the client's host to the entered server_ip
        self.main_window_ref.client.host = server_ip

        reg_resp = self.main_window_ref.client.register(username, password)
        if reg_resp is True or reg_resp == 1:
            login_resp = self.main_window_ref.client.login(username, password)
            if login_resp.get("ID") is not None:
                self.main_window_ref.show_main_widget()
            else:
                print("Login after registration failed!")
                QMessageBox.warning(self, "Login Failed", "Unable to login after registration.", QMessageBox.Ok)
        else:
            print("Registration failed or username taken!")
            QMessageBox.warning(self, "Registration Failed", "Username may already be taken.", QMessageBox.Ok)

    def validate_ip(self, ip_str):
        """
        Validates an IPv4 address.
        Returns True if valid, False otherwise.
        Chat GPT function
        """
        parts = ip_str.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            i = int(part)
            if i < 0 or i > 255:
                return False
        return True


################################################################################
# MainWindow
################################################################################

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Application')
        self.setGeometry(100, 100, 800, 500)
        self.setFixedSize(800, 500)

        self.client = Client()

        self.stacked_widget = QStackedWidget(self)

        self.login_register_page = LoginRegisterUI(self)
        self.main_widget_page = MainWidget(self, self.client)

        self.stacked_widget.addWidget(self.login_register_page)
        self.stacked_widget.addWidget(self.main_widget_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.stacked_widget.setCurrentIndex(0)

    def show_main_widget(self):
        self.main_widget_page.top_bar.update_display(self.client)
        self.stacked_widget.setCurrentIndex(1)


################################################################################
# WagerWindow
################################################################################

class WagerWindow(QMainWindow):
    """
    A separate window for handling wagering interactions between players.
    Displays the player's and enemy's Pokémon, manages attacks, and handles match outcomes.
    """

    def __init__(self, wager_client, deck, parent=None):
        super().__init__(parent)
        self.deck = deck  # Player's current deck of 6 Pokémon
        self.deck_health = []  # Health points corresponding to each Pokémon in the deck
        self.setWindowTitle("Wager Window")
        self.setGeometry(100, 100, 900, 600)
        self.wager_client = wager_client

        # Track turn status and available energy
        self.my_turn = False
        self.energy = 3
        self.current_card = None

        # 1) Exit button in the top-left corner
        self.exit_button = QPushButton("<--", self)
        self.exit_button.setGeometry(QRect(10, 10, 50, 30))
        self.exit_button.clicked.connect(self.close_window)

        # Do nothing Button
        self.exit_button = QPushButton("Do Nothing", self)
        self.exit_button.setGeometry(QRect(110, 300, 70, 30))
        self.exit_button.clicked.connect(self.do_nothing)

        # Energy label to display current energy
        self.energy_label = QLabel(f"{self.energy} Energy", self)
        self.energy_label.setGeometry(QRect(110, 250, 100, 32))
        self.energy_label.setStyleSheet("font-weight: bold")

        # 3) Player's currently active Pokémon card
        self.player_card_button = QPushButton("", self)
        self.player_card_button.setGeometry(QRect(400, 250, 100, 150))

        # Player's HP label positioned at the top-right of the card
        self.current_hp = None
        self.player_hp_label = QLabel(f"{self.current_hp} HP", self)
        self.player_hp_label.setGeometry(QRect(520, 250, 50, 20))

        # 4) Enemy's active Pokémon card
        self.enemy_card_button = QPushButton("", self)
        self.enemy_card_button.setGeometry(QRect(400, 50, 100, 150))

        # 5) Attack buttons positioned to the right of the player's card
        self.current_attack1_name = "None"
        self.current_attack1_price = 99
        self.current_attack1_damage = 99
        self.attack1_button = QPushButton(
            f"{self.current_attack1_name}   {self.current_attack1_price}-Energy   {self.current_attack1_damage}-Damage",
            self)
        self.attack1_button.setGeometry(QRect(550, 250, 250, 50))
        self.attack1_button.clicked.connect(self.attack1)

        self.current_attack2_name = "None"
        self.current_attack2_price = 99
        self.current_attack2_damage = 99
        self.attack2_button = QPushButton(
            f"{self.current_attack2_name}   {self.current_attack2_price}-Energy   {self.current_attack2_damage}-Damage",
            self)
        self.attack2_button.setGeometry(QRect(550, 320, 250, 50))
        self.attack2_button.clicked.connect(self.attack2)

        # Initially disable attack buttons until it's the player's turn
        self.attack1_button.setEnabled(False)
        self.attack2_button.setEnabled(False)

        # Connect WagerClient's moveSignal to handle incoming moves
        self.wager_client.moveSignal.connect(self.on_move_packet)

        # Connect WagerClient's matchResultSignal to handle match outcomes
        self.wager_client.matchResultSignal.connect(self.handle_match_result)  # Updated signal

        # 6) Bottom area with buttons for selecting Pokémon to use
        self.bank_card_buttons = []  # List to store buttons and corresponding card names
        start_x = 100
        start_y = 400
        button_width = 100
        button_height = 150
        spacing = 20

        for i in range(6):
            # Create a button for each Pokémon card
            btn = QPushButton(self)
            x = start_x + i * (button_width + spacing)
            btn.setGeometry(QRect(x, start_y, button_width, button_height))
            if i < len(self.deck):
                card_name = self.deck[i]
                print(card_name)
                # Load card image from the "PokemonCards" folder
                card_path = resource_path("PokemonCards", f"{card_name}.jpeg")
                pix = QPixmap(card_path).scaled(button_width, button_height, Qt.KeepAspectRatio)
                print(card_path)

                icon = QIcon(pix)
                btn.setIcon(icon)
                btn.setIconSize(pix.rect().size())

                # Connect the button to change the active Pokémon
                btn.clicked.connect(lambda _, cn=card_name: self.change_current_card(cn, True))

                # Disable buttons until it's the player's turn
                btn.setEnabled(False)

                # Store the health of each Pokémon in the deck_health list
                health = self.load_card_data_by_name(card_name)["Leben"]
                self.deck_health.append(health)

                # Add the button and card name to the list
                self.bank_card_buttons.append([btn, card_name])
            else:
                # Label buttons as "Empty" if there are fewer than 6 cards
                btn.setText("Empty")

        # Randomly select a starter Pokémon from the deck
        print("Picking a random starter Pokémon...")
        if self.deck:
            self.chosen_starter = random.choice(self.deck)
            print("Chosen starter:", self.chosen_starter)
            # Notify the server of the chosen starter
            self.wager_client.set_starter(self.chosen_starter)
            # Display the chosen starter
            self.change_current_card(self.chosen_starter)
        else:
            self.chosen_starter = None
            print("WagerWindow: No cards in deck to choose a starter.")

        print("Finished WagerWindow setup")
        self.show()

    def attack1(self):
        """
        Executes the first attack if the player has enough energy.
        """
        if self.energy - self.current_attack1_price >= 0:
            self.my_turn = False
            self.wager_client.attack(self.current_attack1_name, self.current_attack1_damage)
            self.energy -= self.current_attack1_price
            print(f"Performed Attack 1: {self.current_attack1_name} for {self.current_attack1_damage} damage.")
        else:
            print("Not enough energy for Attack 1.")
            QMessageBox.warning(
                self,
                "Insufficient Energy",
                "You do not have enough energy for this attack.",
                QMessageBox.Ok
            )
        self.update_buttons_state()
        self.update_ui_after_move()

    def attack2(self):
        """
        Executes the second attack if the player has enough energy.
        """
        if self.energy - self.current_attack2_price >= 0:
            self.my_turn = False
            self.wager_client.attack(self.current_attack2_name, self.current_attack2_damage)
            self.energy -= self.current_attack2_price
            print(f"Performed Attack 2: {self.current_attack2_name} for {self.current_attack2_damage} damage.")
        else:
            print("Not enough energy for Attack 2.")
            QMessageBox.warning(
                self,
                "Insufficient Energy",
                "You do not have enough energy for this attack.",
                QMessageBox.Ok
            )
        self.update_buttons_state()
        self.update_ui_after_move()

    def change_current_card(self, name, end_turn=False):
        """
        Changes the active Pokémon to the selected one and updates the UI accordingly.
        """
        # Display the selected starter on the player_card_button
        path = resource_path("PokemonCards", f"{name}.jpeg")
        print("Selected card path:", path)
        pix = QPixmap(path).scaled(100, 150, Qt.KeepAspectRatio)
        self.player_card_button.setIcon(QIcon(pix))
        self.player_card_button.setIconSize(QSize(100, 150))
        self.current_card = name
        health_index = self.deck.index(self.current_card)
        self.current_hp = self.deck_health[health_index]
        self.player_hp_label.setText(f"{self.current_hp} HP")
        self.update_ui_after_move()

        if end_turn:
            self.my_turn = False
            self.wager_client.switch(name)
            self.update_buttons_state()
            self.update_ui_after_move()

    def do_nothing(self):
        self.my_turn = False
        self.wager_client.do_nothing()
        self.update_buttons_state()
        self.update_ui_after_move()

    def update_ui_after_move(self):
        """
        Updates the UI elements based on the current state after a move.
        """
        print("WagerWindow: Updating UI after move.")
        data = self.load_card_data_by_name(self.current_card)
        self.energy_label.setText(f"{self.energy} Energy")
        if data:
            if self.current_card in self.deck:  # Check if the current Pokémon is still in the deck
                deck_index = self.deck.index(self.current_card)
                self.deck_health[deck_index] = self.current_hp  # Update health in deck_health

            # Update attack details based on the current card's data
            self.current_attack1_name = data.get("A1Name", "None")
            self.current_attack1_damage = data.get("A1Schaden", 0)
            self.current_attack1_price = data.get("A1Energie", 0)

            self.current_attack2_name = data.get("A2Name", "None")
            self.current_attack2_damage = data.get("A2Schaden", 0)
            self.current_attack2_price = data.get("A2Energie", 0)

            # Handle cases where there is no second attack
            if not self.current_attack2_name or self.current_attack2_name == "None":
                self.current_attack2_damage = 0
                self.current_attack2_price = 0

            # Update attack buttons with new information
            self.attack1_button.setText(
                f"{self.current_attack1_name}   {self.current_attack1_price}-Energy   {self.current_attack1_damage}-Damage"
            )

            if self.current_attack2_name and self.current_attack2_name != "None":
                self.attack2_button.setText(
                    f"{self.current_attack2_name}   {self.current_attack2_price}-Energy   {self.current_attack2_damage}-Damage"
                )
            else:
                self.attack2_button.setText("No Attack")
        else:
            print(f"WagerWindow: Failed to load card data for '{self.current_card}'.")
            # Disable attack buttons if card data is missing
            self.attack1_button.setText("No Attack")
            self.attack2_button.setText("No Attack")
            self.attack1_button.setEnabled(False)
            self.attack2_button.setEnabled(False)

        # Update player's HP display
        self.player_hp_label.setText(f"{self.current_hp} HP")

    def load_card_data_by_name(self, card_name):
        """
        Loads card data from the local SQLite database based on the card name.
        Returns a dictionary with card details or None if not found.
        """
        db_path = resource_path("pokemon_cards.db")  # Ensure the database is in the correct folder
        if not os.path.exists(db_path):
            print(f"WagerClient: Database not found at {db_path}")
            return None

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM Cards WHERE Name = ?", (card_name,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                print(f"WagerClient: No card found for: {card_name}")
                return None

            # Map the database row to a dictionary with meaningful keys
            data = {
                "ID": row[0],
                "Name": row[1],
                "Type": row[2],
                "A1Name": row[3],
                "A1Schaden": row[4] if isinstance(row[4], int) else 0,
                "A2Name": row[5] if row[5] != "-" else "",
                "A2Schaden": row[6] if isinstance(row[6], int) else 0,
                "A1Energie": row[7] if isinstance(row[7], int) else 0,
                "A2Energie": row[8] if isinstance(row[8], int) else 0,
                "Schwäche": row[9],
                "Resistenz": row[10],
                "RückzugsKosten": row[11] if isinstance(row[11], int) else 0,
                "Leben": row[12] if isinstance(row[12], int) else 0,
                "Seltenheit": row[13]
            }
            return data
        except Exception as e:
            print(f"WagerClient: Error fetching card data: {e}")
            return None

    def on_move_packet(self, packet: dict):
        """
        Handles incoming move packets from the server.
        Updates the game state based on the enemy's actions.
        """
        enemy_move = packet.get("enemyMove")
        if enemy_move is None:
            # It's now the player's turn
            print("WagerWindow: It's now your turn!")
            self.my_turn = True
            self.energy += 1  # Add 1 energy
            self.energy_label.setText(f"{self.energy} Energy")
            self.update_ui_after_move()
            self.update_buttons_state()
        else:
            match enemy_move:
                case "switch":
                    new_card = packet.get("name")
                    if new_card:
                        self.change_enemy_card(new_card)
                    QMessageBox.information(
                        self,
                        "SWITCH",
                        "The Enemy Player Changed Their Pokémon!",
                        QMessageBox.Ok
                    )
                case "attack":
                    damage = int(packet.get("damage", 0))

                    self.current_hp -= damage
                    self.player_hp_label.setText(f"{self.current_hp} HP")
                    print(f"WagerWindow: Took {damage} damage. Current HP: {self.current_hp}")
                    QMessageBox.information(
                        self,
                        "DAMAGE",
                        f"You got hit with {packet.get('name')} and took {damage} damage!",
                        QMessageBox.Ok
                    )
                    # Check if the player's Pokémon has fainted
                    if self.current_hp < 1:
                        if self.current_card in self.deck:
                            deck_index = self.deck.index(self.current_card)
                            del self.deck_health[deck_index]
                            self.deck.remove(self.current_card)
                            print("POKEMON FAINTED!")
                            self.player_hp_label.setText("000")
                        if len(self.deck) < 1:
                            self.defeat()
            # Opponent's turn ends, mark it as the player's turn
            print("WagerWindow: Opponent's move processed. It's now your turn.")
            self.my_turn = True
            self.energy += 2  # Add 2 energy
            self.energy_label.setText(f"{self.energy} Energy")
            self.update_ui_after_move()
            self.update_buttons_state()

    def defeat(self):
        print("defeat")
        packet = {"type": "defeat", "player_id": self.client.user_data["ID"]}
        self.wager_client.send_dict_as_json_to_wager_server(packet)
        QMessageBox.information(
            self,
            "Defeat",
            "All your Pokémon have fainted. You have been defeated!",
            QMessageBox.Ok
        )
        self.close()  # Ensure the window is closed properly

    def handle_match_result(self, win):
        print("win")
        """
        Handles the match result based on the server's response.
        Displays appropriate messages and closes the wager window.
        """
        if win:
            QMessageBox.information(
                self,
                "Victory",
                "Congratulations! You won the match!",
                QMessageBox.Ok
            )
        else:
            QMessageBox.information(
                self,
                "Defeat",
                "All your Pokémon have fainted. You have been defeated!",
                QMessageBox.Ok
            )

    def update_buttons_state(self):
        """
        Enables or disables attack and card selection buttons based on the turn status.
        """
        # Enable attack buttons only if it's the player's turn and Pokémon is alive
        if self.current_hp > 0:
            self.attack1_button.setEnabled(self.my_turn)
            self.attack2_button.setEnabled(self.my_turn)
        else:
            self.attack1_button.setEnabled(False)
            self.attack2_button.setEnabled(False)

        # Enable card selection buttons only if it's the player's turn
        for button, card_name in self.bank_card_buttons:
            if card_name in self.deck:
                button.setEnabled(self.my_turn)

    def change_enemy_card(self, enemy_card_name):
        """
        Updates the enemy's active Pokémon card display.
        """
        card_path = resource_path("PokemonCards", f"{enemy_card_name}.jpeg")
        pix = QPixmap(card_path).scaled(100, 150, Qt.KeepAspectRatio)
        self.enemy_card_button.setIcon(QIcon(pix))
        self.enemy_card_button.setIconSize(QSize(100, 150))
        print(f"Enemy starter is now shown: {enemy_card_name}")
        print(card_path)

    def close_window(self):
        """
        Handles the closing of the WagerWindow.
        """
        self.close()


################################################################################
# WagerClient
################################################################################

class WagerClient(QObject):
    """
    Handles all wagering-related server communications.
    Manages signals for starting the wager, updating enemy cards, handling moves, and match results.
    """
    startSignal = pyqtSignal()  # Signal to indicate the start of a wager
    enemyCardChangeSignal = pyqtSignal(str)  # Signal to update the enemy's starter Pokémon
    moveSignal = pyqtSignal(dict)  # Signal carrying move packets from the server
    matchResultSignal = pyqtSignal(bool)  # Signal indicating the match result (win or loss)

    def __init__(self, client, host="192.168.42.1", port=27777):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.client = client

    def connect(self):
        """
        Connects to the Wager server and starts the message-reading thread.
        Sends a connection packet with the player's ID.
        """
        self.host = self.client.host
        print("new host fix ", self.host)
        try:
            if not self.sock:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print(f"Connected to Wager server at {self.host}:{self.port}")

                # Start a background thread to read server messages
                t = threading.Thread(target=self.read_loop, daemon=True)
                t.start()

                # Share player ID for server identification
                packet = {"type": "connect", "player_id": self.client.user_data["ID"]}
                self.send_dict_as_json_to_wager_server(packet)

        except Exception as e:
            print(f"[Error connecting]: {e}")

    def read_loop(self):
        """
        Continuously reads messages from the server, processes them, and emits appropriate signals.
        """
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    print("Server closed the connection.")
                    break

                decompressed = zlib.decompress(data).decode("utf-8")
                packet = json.loads(decompressed)
                print(f"\n[SERVER MESSAGE]: {packet}")

                match packet.get("type"):
                    case "start":
                        print("Wager started.")
                        self.stop_search()
                        self.startSignal.emit()

                    case "enemyStarter":
                        # Server notifies of the opponent's chosen starter
                        enemy_starter = packet.get("EnemyStarter")
                        if enemy_starter:
                            print(f"Enemy starter is {enemy_starter}")
                            self.enemyCardChangeSignal.emit(enemy_starter)

                    case "move":
                        # Emit moveSignal with the entire move packet
                        self.moveSignal.emit(packet)

                    case "matchResult":
                        # Emit matchResultSignal with the win status
                        win = packet.get("win", False)
                        print(f"Match Result - Win: {win}")
                        self.matchResultSignal.emit(win)

            except (zlib.error, json.JSONDecodeError) as e:
                print(f"[Error decoding message]: {e}")
                break  # Optionally handle reconnection or cleanup here

            except ConnectionResetError as e:
                print(f"[ConnectionResetError]: {e}")
                print(f"Match Result - Win: {True}")
                self.matchResultSignal.emit(True)
                break

    def set_starter(self, starter_name: str):
        """
        Sends the chosen starter Pokémon to the server.
        """
        print(f"Setting starter Pokémon: {starter_name}")
        packet = {
            "type": "setStarter",
            "player_id": self.client.user_data["ID"],
            "name": starter_name
        }
        self.send_dict_as_json_to_wager_server(packet)

    def attack(self, name, damage):
        """
        Sends an attack action to the server with the attack name and damage.
        """
        print("Performing Attack")
        packet = {
            "type": "move",
            "enemyMove": "attack",
            "name": name,
            "damage": damage,
            "player_id": self.client.user_data["ID"]
        }
        self.send_dict_as_json_to_wager_server(packet)

    def switch(self, name):
        """
        Sends a switch action to the server to change the active Pokémon.
        """
        print("Switching Pokémon")
        packet = {
            "type": "move",
            "enemyMove": "switch",
            "name": name,
            "player_id": self.client.user_data["ID"]
        }
        self.send_dict_as_json_to_wager_server(packet)

    def do_nothing(self):
        packet = {
            "type": "move",
            "enemyMove": None,
            "player_id": self.client.user_data["ID"]
        }
        self.send_dict_as_json_to_wager_server(packet)

    def send_dict_as_json_to_wager_server(self, dict_data):
        """
        Sends a JSON-encoded and compressed dictionary to the Wager server.
        """
        try:
            raw = json.dumps(dict_data).encode("utf-8")
            compressed = zlib.compress(raw)
            self.sock.sendall(compressed)
            print(f"Sent to Wager server: {dict_data}")
        except Exception as e:
            print(f"[Error sending packet to Wager server]: {e}")

    def search(self, enemy_id):
        """
        Initiates a search for an opponent with the specified enemy ID.
        """
        player_id = self.client.user_data["ID"]
        packet = {"type": "search", "player_id": player_id, "enemy_id": enemy_id}
        self.send_dict_as_json_to_wager_server(packet)

    def stop_search(self):
        """
        Sends a packet to the server to stop searching for an opponent.
        """
        player_id = self.client.user_data["ID"]
        packet = {"type": "stopSearch", "player_id": player_id}
        self.send_dict_as_json_to_wager_server(packet)


def main():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
