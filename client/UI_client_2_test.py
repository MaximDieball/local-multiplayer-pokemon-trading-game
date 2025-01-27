import sys
import os
import socket
import json
import zlib
import random
import threading
from PyQt5.QtCore import pyqtSignal, QObject

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QDialog, QDialogButtonBox,
    QGridLayout, QScrollArea
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
    def __init__(self, card_paths):
        print("PackAnimationWindow INNIT")
        super().__init__()
        self.setWindowTitle("Pack Opening")
        self.setGeometry(100, 100, 600, 800)

        # The "stack" of cards
        back_path = resource_path("images", "back.png")
        print(back_path)
        self.card_stack_label = QLabel(self)
        self.pixmap_back = QPixmap(back_path)
        self.card_stack_label.setPixmap(self.pixmap_back.scaled(200, 300, Qt.KeepAspectRatio))
        self.card_stack_label.setGeometry(200, 350, 200, 300)

        self.card_paths = card_paths
        print("Card paths:", self.card_paths)

        # The flipping card label
        self.card_label = QLabel(self)
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, Qt.KeepAspectRatio))
        self.card_label.setGeometry(200, 350, 200, 300)
        self.beginning_card_geometry = self.card_label.geometry()

        # Animations
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
        if event.button() == Qt.LeftButton:
            self.click()

    def click(self):
        if self.card_paths:
            if not self.has_flipped and not self.animation_running:
                self.animation_running = True
                front_path = self.card_paths.pop(0)
                self.pixmap_front = QPixmap(front_path)
                self.animation()
                if not self.card_paths:
                    self.card_stack_label.clear()
            elif not self.animation_running:
                self.reset_card()
                self.has_flipped = False

    def reset_card(self):
        self.card_label.setGeometry(self.beginning_card_geometry)
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, Qt.KeepAspectRatio))
        self.card_label.move(200, 350)
        self.sparkle_label.setVisible(False)

    def animation(self):
        current_geometry = self.card_label.geometry()
        # shrink
        shrink_geometry = QRect(
            current_geometry.x() + current_geometry.width() // 2,
            current_geometry.y() - 310,
            0,
            current_geometry.height()
        )
        self.animation1.setStartValue(current_geometry)
        self.animation1.setEndValue(shrink_geometry)
        self.animation1.valueChanged.connect(self.update_card_back)

        # expand
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
        self.card_label.setPixmap(
            self.pixmap_back.scaled(max(1, current_geometry.width()), current_geometry.height(), Qt.KeepAspectRatio)
        )

    def update_card_front(self, current_geometry):
        self.card_label.setPixmap(
            self.pixmap_front.scaled(max(1, current_geometry.width()), current_geometry.height(), Qt.KeepAspectRatio)
        )


################################################################################
# Client
################################################################################

class Client:
    def __init__(self, host='127.0.0.1', port=17777, wager_port=27777):
        self.host = host
        self.port = port
        self.wager_port = wager_port
        self.user_data = {"ID": None, "Username": None, "Balance": None, "RankPoints": None}
        self.deck = []
        self.local_coins = 9999999

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
        self.setFixedSize(500, 100)

        self.client = client
        self.inventory_page = inventory_page

        layout = QVBoxLayout()
        data_label = QLabel(f"{data}\n{client.deck}", self)
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

        self.coin_label = QLabel(self)
        coin_pixmap = QPixmap(coin_path)
        self.coin_label.setPixmap(coin_pixmap)
        self.coin_label.setScaledContents(True)
        self.coin_label.setGeometry(20, 10, 60, 60)

        self.local_coins_label = QLabel("Local: ???", self)
        self.local_coins_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.local_coins_label.setGeometry(90, 25, 100, 30)

        self.deposit_button = QPushButton("Deposit", self)
        self.deposit_button.setGeometry(190, 25, 80, 30)
        self.deposit_button.clicked.connect(self.parent_widget.show_deposit_dialog)

        self.withdraw_button = QPushButton("Withdraw", self)
        self.withdraw_button.setGeometry(280, 25, 80, 30)
        self.withdraw_button.clicked.connect(self.parent_widget.show_withdraw_dialog)

        self.send_coins_button = QPushButton("Send coins", self)
        self.send_coins_button.setGeometry(370, 25, 80, 30)
        self.send_coins_button.clicked.connect(self.parent_widget.show_send_coins_dialog)

        self.send_cards_button = QPushButton("Send cards", self)
        self.send_cards_button.setGeometry(460, 25, 80, 30)
        self.send_cards_button.clicked.connect(self.parent_widget.show_send_cards_dialog)

        self.user_data_label = QLabel("""
                                        ID: ?
                                        Name: ?
                                        Balance: ?
                                        RankPoints: ?
                                        """, self)
        self.user_data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_data_label.setGeometry(560, 5, 150, 70)

        self.profile_label = QLabel(self)
        profile_pixmap = QPixmap(profile_path)
        self.profile_label.setPixmap(profile_pixmap)
        self.profile_label.setScaledContents(True)
        self.profile_label.setGeometry(720, 10, 60, 60)

    def update_display(self, client):
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
    def __init__(self, switch_to_wager_page_callback, switch_to_open_packs_page_callback,
                 switch_to_inventory_page_callback):
        super().__init__()
        self.switch_to_wager_page_callback = switch_to_wager_page_callback
        self.switch_to_open_packs_page_callback = switch_to_open_packs_page_callback
        self.switch_to_inventory_page_callback = switch_to_inventory_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(800, 420)

        # Pokeball
        pokeball_path = resource_path("images", "pokeball.png")
        pointer_path = resource_path("images", "pointer.png")

        self.pokeball_label = QLabel(self)
        pokeball_pixmap = QPixmap(pokeball_path)
        self.pokeball_label.setPixmap(pokeball_pixmap)
        self.pokeball_label.setScaledContents(True)
        self.pokeball_label.setGeometry(QRect(50, 40, 200, 200))
        self.pokeball_original_geom = self.pokeball_label.geometry()

        self.pointer_label = QLabel(self)
        pointer_pixmap = QPixmap(pointer_path)
        transform = QTransform()
        transform.rotate(-45)
        rotated_pointer = pointer_pixmap.transformed(transform, Qt.SmoothTransformation)
        self.pointer_label.setPixmap(rotated_pointer)
        self.pointer_label.setScaledContents(True)
        self.pointer_label.setGeometry(QRect(180, 180, 50, 50))

        self.open_packs_button = QPushButton("Open packs", self)
        self.open_packs_button.setGeometry(QRect(350, 20, 200, 100))
        self.open_packs_button.clicked.connect(self.switch_to_open_packs_page_callback)

        self.inventory_button = QPushButton("Inventory", self)
        self.inventory_button.setGeometry(QRect(350, 120, 200, 100))
        self.inventory_button.clicked.connect(self.switch_to_inventory_page_callback)

        self.wager_button = QPushButton("Wager", self)
        self.wager_button.setGeometry(QRect(350, 220, 200, 100))
        self.wager_button.clicked.connect(self.switch_to_wager_page_callback)

        self.pokeball_label.mousePressEvent = self.pokeball_clicked

    def pokeball_clicked(self, event):
        if event.button() == Qt.LeftButton:
            mw = self.parentWidget().parentWidget()
            client = mw.client
            client.local_coins += 1
            self.animate_pokeball()
            mw.top_bar.update_display(client)
        QLabel.mousePressEvent(self.pokeball_label, event)

    def animate_pokeball(self):
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
    def __init__(self, switch_to_main_page_callback, main_window_ref):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.main_window_ref = main_window_ref
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(800, 420)

        self.pack1_button = QPushButton("Default Pack\n200 Coins", self)
        self.pack1_button.setGeometry(200, 80, 120, 200)
        self.pack1_button.clicked.connect(lambda: self.open_pack(1, 200))

        self.pack2_button = QPushButton("SUPER Pack\n600 Coins", self)
        self.pack2_button.setGeometry(350, 80, 120, 200)
        self.pack2_button.clicked.connect(lambda: self.open_pack(2, 600))

        self.pack3_button = QPushButton("HOLO Pack\n3000 Coins", self)
        self.pack3_button.setGeometry(500, 80, 120, 200)
        self.pack3_button.clicked.connect(lambda: self.open_pack(3, 3000))

        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)

    def open_pack(self, pack_id, cost):
        print(f"open_pack({pack_id}, {cost})")
        c = self.main_window_ref.client
        if c.local_coins < cost:
            print("Not enough local coins!")
            return
        c.local_coins -= cost
        dict_data = {"type": "openPack", "user_id": c.user_data["ID"], "pack_id": pack_id}
        sr = c.send_dict_as_json_to_server(dict_data)
        if not sr:
            print("Open pack returned no cards or error.")
            return

        sorted_pack = []
        print("4")
        for card in sr:
            print(card[11])
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

        paths = []
        for card in sorted_pack:
            cn = card[1]
            path = resource_path("PokemonCards", f"{cn}.jpeg")
            paths.append(path)

        self.anim_window = PackAnimationWindow(paths)
        self.anim_window.show()
        self.main_window_ref.main_widget_page.top_bar.update_display(c)


################################################################################
# CardLabel
################################################################################

class CardLabel(QLabel):
    def __init__(self, is_duplicate, card_info, client, pixmap, inventory_page, parent=None):
        super().__init__(parent)
        self.card_info = card_info
        self.client = client
        self.inventory_page = inventory_page

        if not is_duplicate:
            self.setPixmap(pixmap)
        else:
            img = pixmap.toImage()
            gray = img.convertToFormat(QImage.Format_Grayscale8)
            p2 = QPixmap.fromImage(gray)
            self.setPixmap(p2)

        if card_info[1] in client.deck and not is_duplicate:
            self.setStyleSheet("border: 3px solid blue; background: white; margin: 5px;")
        else:
            self.setStyleSheet("border: 1px solid gray; background: white; margin: 5px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            dlg = CardDataDialog(self.card_info, self.client, self.inventory_page)
            dlg.exec_()
        super().mousePressEvent(event)


################################################################################
# InventoryPage
################################################################################

class InventoryPage(QWidget):
    def __init__(self, switch_to_main_page_callback, card_data, client):
        super().__init__()
        self.client = client
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.card_data = card_data
        self.setFixedSize(800, 420)

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.container.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.container)

        self.build_grid()

        self.back_button = QPushButton("<---")
        self.back_button.setMaximumWidth(80)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)
        self.main_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)

    def build_grid(self):
        # remove old
        for i in reversed(range(self.grid_layout.count())):
            wdg = self.grid_layout.itemAt(i).widget()
            if wdg:
                wdg.setParent(None)
                wdg.deleteLater()

        rarity_rank = {"Common": 0, "Uncommon": 1, "Rare": 2, "HoloRare": 3}

        def sort_key(card):
            return (rarity_rank.get(card[11], 99), card[1])

        sorted_cards = sorted(self.card_data, key=sort_key)
        seen_names = set()
        row, col = 0, 0

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
        self.build_grid()


################################################################################
# WagerSearchPage
################################################################################

class WagerSearchPage(QWidget):
    def __init__(self, switch_to_main_page_callback, wager_client):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.init_ui()
        self.wager_client = wager_client

    def init_ui(self):
        self.setFixedSize(800, 420)

        self.enemy_label = QLabel("Enemy Player ID:", self)
        self.enemy_label.setGeometry(289, 120, 100, 25)

        self.enemy_input = QLineEdit(self)
        self.enemy_input.setGeometry(398, 120, 120, 25)

        self.stake_label = QLabel("Stake:", self)
        self.stake_label.setGeometry(289, 174, 100, 25)

        self.stake_input = QLineEdit(self)
        self.stake_input.setGeometry(398, 174, 120, 25)

        self.search_button = QPushButton("Search", self)
        self.search_button.setGeometry(363, 270, 80, 30)
        self.search_button.clicked.connect(self.start_search)

        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.stop_search_and_go_back_to_main_page)

    def start_search(self):
        self.wager_client.connect()
        self.wager_client.stop_search()

        self.wager_client.search(int(self.enemy_input.text()))

    def stop_search_and_go_back_to_main_page(self):
        self.wager_client.stop_search()
        self.switch_to_main_page_callback()


################################################################################
# MainWidget
################################################################################

class MainWidget(QWidget):
    def __init__(self, main_window_ref, client):
        super().__init__()
        self.main_window_ref = main_window_ref
        self.client = client
        # create wager_client and set signals to open the wager window
        self.wager_client = WagerClient(self.client)
        self.wager_client.startSignal.connect(self.show_wager_window)

        self.setFixedSize(800, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.top_bar = TopBar(self)
        layout.addWidget(self.top_bar)

        self.center_stack = QStackedWidget(self)
        layout.addWidget(self.center_stack)

        self.main_page = MainPage(
            self.show_wager_page,
            self.show_open_packs_page,
            self.show_inventory_page
        )
        self.wager_page = WagerSearchPage(self.show_main_page, self.wager_client)
        self.open_packs_page = OpenPacksPage(self.show_main_page, self.main_window_ref)
        self.inventory_page = InventoryPage(self.show_main_page, [], self.client)

        self.center_stack.addWidget(self.main_page)
        self.center_stack.addWidget(self.wager_page)
        self.center_stack.addWidget(self.open_packs_page)
        self.center_stack.addWidget(self.inventory_page)

        self.center_stack.setCurrentWidget(self.main_page)

    def show_wager_window(self):
        print("show_wager_window")
        # Create the window and pass in the WagerClient + deck
        self.wager_window = WagerWindow(self.wager_client, self.client.deck)
        self.wager_window.show()
        print("trying to connect starter signal")
        # Connect the WagerClient's enemyStarterSignal to a slot in WagerWindow
        self.wager_client.enemyStarterSignal.connect(self.wager_window.on_enemy_starter)

    def show_withdraw_dialog(self):
        dlg = WithdrawDialog()
        if dlg.exec_() == QDialog.Accepted:
            amt_str = dlg.get_amount()
            if amt_str.isdigit():
                amt = int(amt_str)
                self.main_window_ref.client.withdraw(amt)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid amount entered.")

    def show_deposit_dialog(self):
        dlg = DepositDialog()
        if dlg.exec_() == QDialog.Accepted:
            amt_str = dlg.get_amount()
            if amt_str.isdigit():
                amt = int(amt_str)
                self.main_window_ref.client.deposit(amt)
                self.top_bar.update_display(self.main_window_ref.client)
            else:
                print("Invalid amount entered.")

    def show_send_coins_dialog(self):
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

    def show_send_cards_dialog(self):
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

    def show_main_page(self):
        self.center_stack.setCurrentWidget(self.main_page)

    def show_wager_page(self):
        # if len(self.client.deck) == 6:
        self.center_stack.setCurrentWidget(self.wager_page)

    def show_open_packs_page(self):
        self.center_stack.setCurrentWidget(self.open_packs_page)

    def show_inventory_page(self):
        uid = self.main_window_ref.client.user_data["ID"]
        if uid is None:
            print("No user logged in, cannot fetch inventory.")
            return

        dict_data = {"type": "inventory", "user_id": uid}
        sr = self.main_window_ref.client.send_dict_as_json_to_server(dict_data)
        if not sr:
            print("No inventory data returned or error.")
            return

        idx = self.center_stack.indexOf(self.inventory_page)
        if idx != -1:
            self.center_stack.removeWidget(self.inventory_page)
            self.inventory_page.deleteLater()

        self.inventory_page = InventoryPage(self.show_main_page, sr, self.client)
        self.center_stack.addWidget(self.inventory_page)
        self.center_stack.setCurrentWidget(self.inventory_page)


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

        # LOGIN
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

        # REGISTER
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

        resp = self.main_window_ref.client.login(username, password)
        if resp["ID"] is not None:
            self.main_window_ref.show_main_widget()
        else:
            print("Login failed!")

    def handle_register(self):
        username = self.register_name_input.text()
        password = self.register_password_input.text()
        if not username or not password:
            print("username or password is empty")
            return

        reg_resp = self.main_window_ref.client.register(username, password)
        if reg_resp is True or reg_resp == 1:
            login_resp = self.main_window_ref.client.login(username, password)
            if login_resp["ID"] is not None:
                self.main_window_ref.show_main_widget()
            else:
                print("Login after registration failed!")
        else:
            print("Registration failed or username taken!")


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
    def __init__(self, wager_client, deck, parent=None):
        super().__init__(parent)
        self.deck = deck  # store the player's 6 cards
        self.setWindowTitle("Wager Window")
        self.setGeometry(100, 100, 900, 600)
        self.wager_client = wager_client

        # 1) Exit button in top-left
        self.exit_button = QPushButton("<--", self)
        self.exit_button.setGeometry(QRect(10, 10, 50, 30))
        # self.exit_button.clicked.connect(...)  # connect to some exit logic

        # 2) Energy icon + label on left side
        # Example icon: resource_path("energy.png") if you have one
        self.energy_icon_label = QLabel(self)
        energy_pixmap = QPixmap(resource_path("energy.png"))
        self.energy_icon_label.setPixmap(energy_pixmap.scaled(32, 32, Qt.KeepAspectRatio))
        self.energy_icon_label.setGeometry(QRect(10, 70, 32, 32))

        self.energy_label = QLabel("3 Energie", self)
        self.energy_label.setGeometry(QRect(110, 250, 100, 32))

        # 3) Player's currently used Pokemon card (middle-lower area)
        #    We'll put it near the bottom, around x=250, y=300
        self.player_type_label = QLabel("Water", self)
        self.player_type_label.setGeometry(QRect(350, 250, 60, 20))  # left of the card

        self.player_card_button = QPushButton("", self)
        self.player_card_button.setGeometry(QRect(400, 250, 100, 150))

        # top-right of that card = HP label
        self.player_hp_label = QLabel("99 HP", self)
        self.player_hp_label.setGeometry(QRect(520, 250, 50, 20))

        # 4) Enemy's Pokemon card (middle-upper area)
        #    We'll put it near the top, around x=400, y=50
        self.enemy_type_label = QLabel("Water", self)
        self.enemy_type_label.setGeometry(QRect(350, 50, 60, 20))  # left of the card

        self.enemy_card_button = QPushButton("", self)
        self.enemy_card_button.setGeometry(QRect(400, 50, 100, 150))

        self.enemy_hp_label = QLabel("99 HP", self)
        self.enemy_hp_label.setGeometry(QRect(520, 250, 50, 20))

        # 5) Attack 1 & Attack 2 buttons, to the right of the player's card
        #    For example at x=380,y=300 and x=380,y=350
        self.attack1_button = QPushButton("Attack1   2-Energie   25-Damage   X1", self)
        self.attack1_button.setGeometry(QRect(550, 250, 250, 50))

        self.attack2_button = QPushButton("Attack2   2-Energie   25-Damage   X1", self)
        self.attack2_button.setGeometry(QRect(550, 320, 250, 50))

        # 6) At the bottom: 6 Buttons for Pokemon cards the user can choose
        #    We'll place them horizontally across the bottom
        self.bottom_card_buttons = []
        start_x = 100
        start_y = 400
        button_width = 100
        button_height = 150
        spacing = 20

        for i in range(6):
            # Create a button
            btn = QPushButton(self)
            x = start_x + i * (button_width + spacing)
            btn.setGeometry(QRect(x, start_y, button_width, button_height))
            # If this index is valid for the deck, show the card image (or name)
            if i < len(self.deck):
                card_name = self.deck[i]
                print(card_name)
                # Load card image from your "PokemonCards" folder
                card_path = resource_path("PokemonCards", f"{card_name}.jpeg")
                pix = QPixmap(card_path).scaled(button_width, button_height, Qt.KeepAspectRatio)
                print(card_path)

                icon = QIcon(pix)
                btn.setIcon(icon)
                btn.setIconSize(pix.rect().size())
            else:
                # If for some reason deck is shorter than 6, label as "Empty":
                btn.setText("Empty")

            self.bottom_card_buttons.append(btn)

        # =========================
        # PICK A RANDOM STARTER
        # =========================
        print("pick a random starter")
        if self.deck:
            self.chosen_starter = random.choice(self.deck)
            print("chosen starter: ", self.chosen_starter)
            # Show chosen starter on player_card_button
            chosen_path = resource_path("PokemonCards", f"{self.chosen_starter}.jpeg")
            print("chosen_path ", chosen_path)
            chosen_pix = QPixmap(chosen_path).scaled(100, 150, Qt.KeepAspectRatio)
            self.player_card_button.setIcon(QIcon(chosen_pix))
            self.player_card_button.setIconSize(QSize(100, 150))
            print("trying to set_starter")
            # Notify the server of our starter
            self.wager_client.set_starter(self.chosen_starter)
        else:
            self.chosen_starter = None

        print("finished WagerWindow setup")
        self.show()

    def on_enemy_starter(self, enemy_starter_name: str):
        """
        Called when the server notifies us of the opponent's starter.
        We'll update the Enemy Card button.
        """
        card_path = resource_path("PokemonCards", f"{enemy_starter_name}.jpeg")
        pix = QPixmap(card_path).scaled(100, 150, Qt.KeepAspectRatio)
        self.enemy_card_button.setIcon(QIcon(pix))
        self.enemy_card_button.setIconSize(QSize(100, 150))
        print(f"Enemy starter is now shown: {enemy_starter_name}")
        print(card_path)


################################################################################
# WagerClient
################################################################################

class WagerClient(QObject):
    startSignal = pyqtSignal()
    enemyStarterSignal = pyqtSignal(str)  # <-- add this signal for enemy starter

    def __init__(self, client, host="127.0.0.1", port=27777):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.client = client

    def connect(self):
        """Connect to the Wager server and start a read thread."""
        try:
            if not self.sock:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print(f"Connected to server at {self.host}:{self.port}")

                # Start a background thread to read server messages
                t = threading.Thread(target=self.read_loop, daemon=True)
                t.start()

                # share player id / for the server to connect player id and connection
                packet = {"type": "connect", "player_id": self.client.user_data["ID"]}
                self.send_dict_as_json_to_wager_server(packet)

        except Exception as e:
            print(f"[Error connecting]: {e}")

    def read_loop(self):
        while True:
            data = self.sock.recv(4096)
            if not data:
                print("Server closed the connection.")
                break

            decompressed = zlib.decompress(data).decode("utf-8")
            packet = json.loads(decompressed)
            print(f"\n[SERVER MESSAGE]: {packet}")

            match packet["type"]:
                case "start":
                    print("start")
                    self.stop_search()
                    self.startSignal.emit()

                case "enemyStarter":
                    # The server tells us the opponent's chosen starter
                    enemy_starter = packet["EnemyStarter"]
                    print(f"Enemy starter is {enemy_starter}")
                    self.enemyStarterSignal.emit(enemy_starter)

    def set_starter(self, starter_name: str):
        """Send our chosen starter to the server."""
        print(starter_name)
        print(self.client.user_data["ID"])
        packet = {
            "type": "setStarter",
            "player_id": self.client.user_data["ID"],
            "name": starter_name
        }
        print(packet)
        self.send_dict_as_json_to_wager_server(packet)

    def send_dict_as_json_to_wager_server(self, dict_data):
        """Send a JSON packet to the server, compressed."""
        try:
            raw = json.dumps(dict_data).encode("utf-8")
            compressed = zlib.compress(raw)
            self.sock.sendall(compressed)
        except Exception as e:
            print(f"[Error sending packet]: {e}")

    def run_cli(self):
        """Run a simple CLI loop using match for commands."""
        print("Commands:\n"
              "  hello <player_id>\n"
              "  search <enemy_id>\n"
              "  setStarter <name>\n"
              "  move <move_name>\n"
              "  defeat\n"
              "  quit\n")
        while True:
            cmd = input("command:").strip()
            if not cmd:
                continue
            parts = cmd.split(maxsplit=1)
            main_cmd = parts[0].lower()
            argument = ""
            if len(parts) > 1:
                argument = parts[1]

            match main_cmd:
                case "quit":
                    print("Quitting client.")
                    break
                case "connect":
                    if argument.isdigit():
                        self.player_id = int(argument)
                        packet = {"type": "hello", "player_id": self.player_id}
                        self.send_packet(packet)
                    else:
                        print("Usage: hello <player_id>")
                case "search":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        if argument.isdigit():
                            enemy_id = int(argument)
                            packet = {"type": "search", "player_id": self.player_id, "enemy_id": enemy_id}
                            self.send_packet(packet)
                        else:
                            print("Usage: search <enemy_id>")
                case "setstarter":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        if argument:
                            packet = {"type": "setStarter", "player_id": self.player_id, "name": argument}
                            self.send_packet(packet)
                        else:
                            print("Usage: setStarter <name>")
                case "move":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        if argument:
                            packet = {"type": "move", "player_id": self.player_id, "move": argument}
                            self.send_packet(packet)
                        else:
                            print("Usage: move <move_name>")
                case "defeat":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        packet = {"type": "defeat", "player_id": self.player_id}
                        self.send_packet(packet)
                case _:
                    print("Unknown or malformed command.")
        self.sock.close()
        print("Client socket closed.")

    def search(self, enemy_id):
        player_id = self.client.user_data["ID"]
        packet = {"type": "search", "player_id": player_id, "enemy_id": enemy_id}
        self.send_dict_as_json_to_wager_server(packet)

    def stop_search(self):
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
