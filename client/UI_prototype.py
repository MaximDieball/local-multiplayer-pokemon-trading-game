import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QDialog, QDialogButtonBox,
    QHBoxLayout, QFormLayout
)
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt, QRect

width = 800
height = 500


# ------------------------------ LoginRegisterUI ------------------------------ #
class LoginRegisterUI(QWidget):
    def __init__(self, on_login_success_callback):
        super().__init__()
        self.init_ui(on_login_success_callback)

    def init_ui(self, on_login_success_callback):
        # Keep your original geometry for the login/register UI
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
        login_button.clicked.connect(on_login_success_callback)

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
        register_button.clicked.connect(on_login_success_callback)


# ------------------------------ TopBar ------------------------------ #
class TopBar(QWidget):
    """
    always visible top bar
    showing coin image, coin count, deposit/withdraw/send buttons,
    top-right profile image, user data.
    """

    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        # Force a fixed height for the top bar
        self.setFixedHeight(80)
        self.init_ui()

    def init_ui(self):
        # We’ll do everything with absolute coordinates in this top bar
        # The width is inherited from the parent, but we can read it at runtime
        bar_width = self.parent_widget.width()
        self.setFixedWidth(bar_width)

        # Coin image
        self.coin_label = QLabel(self)
        coin_pixmap = QPixmap("images/coin.png")
        self.coin_label.setPixmap(coin_pixmap)
        self.coin_label.setScaledContents(True)
        self.coin_label.setGeometry(20, 10, 60, 60)

        # Coin count
        self.coin_count_label = QLabel("91234", self)
        self.coin_count_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.coin_count_label.setGeometry(90, 25, 60, 30)

        # Deposit button
        self.deposit_button = QPushButton("Deposit", self)
        self.deposit_button.setGeometry(150 + 40, 25, 80, 30)
        self.deposit_button.clicked.connect(self.parent_widget.show_deposit_dialog)

        # Withdraw button
        self.withdraw_button = QPushButton("Withdraw", self)
        self.withdraw_button.setGeometry(240 + 40, 25, 80, 30)
        self.withdraw_button.clicked.connect(self.parent_widget.show_withdraw_dialog)

        # Send coins button
        self.send_coins_button = QPushButton("Send coins", self)
        self.send_coins_button.setGeometry(330 + 40, 25, 80, 30)
        self.send_coins_button.clicked.connect(self.parent_widget.show_send_coins_dialog)

        # Send cards button
        self.send_cards_button = QPushButton("Send cards", self)
        self.send_cards_button.setGeometry(420 + 40, 25, 80, 30)
        self.send_cards_button.clicked.connect(self.parent_widget.show_send_cards_dialog)

        # User data label
        # Possibly multiline, so let's give it a bigger height
        self.user_data_label = QLabel("""
                                        ID : 1234
                                        Name : ADMIN
                                        Balance : 300
                                        RankedPoints : 100
                                        """, self)
        self.user_data_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.user_data_label.setGeometry(560, 5, 150, 70)

        # Profile image
        self.profile_label = QLabel(self)
        profile_pixmap = QPixmap("images/profile.png")
        self.profile_label.setPixmap(profile_pixmap)
        self.profile_label.setScaledContents(True)
        self.profile_label.setGeometry(720, 10, 60, 60)


# ------------------------------ MainPage ------------------------------ #
class MainPage(QWidget):
    """
    main page
    with (pokeball, open packs, inventory, wager)
    """
    def __init__(self, switch_to_wager_page_callback):
        super().__init__()
        self.switch_to_wager_page_callback = switch_to_wager_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)  # minus the top bar's height

        # Pokeball Image
        self.pokeball_label = QLabel(self)
        pokeball_pixmap = QPixmap("images/pokeball.png")
        self.pokeball_label.setPixmap(pokeball_pixmap)
        self.pokeball_label.setScaledContents(True)
        # (x=50, y=40, width=200, height=200)
        self.pokeball_label.setGeometry(QRect(50, 40, 200, 200))

        # Pointer Image
        self.pointer_label = QLabel(self)
        pointer_pixmap = QPixmap("images/pointer.png")
        # Rotate by 45 degrees
        transform = QTransform()
        transform.rotate(-45)
        rotated_pointer = pointer_pixmap.transformed(transform, Qt.SmoothTransformation)
        self.pointer_label.setPixmap(rotated_pointer)
        self.pointer_label.setScaledContents(True)
        # Place it just to the right of the Pokéball, e.g., (x=260, y=40), 50x50
        self.pointer_label.setGeometry(QRect(180, 180, 50, 50))

        # Open packs
        self.open_packs_button = QPushButton("Open packs", self)
        self.open_packs_button.setGeometry(QRect(350, 20, 200, 100))

        # Inventory
        self.inventory_button = QPushButton("Inventory", self)
        self.inventory_button.setGeometry(QRect(350, 120, 200, 100))

        # Wager
        self.wager_button = QPushButton("Wager", self)
        self.wager_button.setGeometry(QRect(350, 220, 200, 100))
        self.wager_button.clicked.connect(self.switch_to_wager_page_callback)


# ------------------------------ WagerSearchPage ------------------------------ #
class WagerSearchPage(QWidget):
    """
    The page that asks for Enemy Player ID, Stake, has a Search button,
    and a Go Back button.
    """

    def __init__(self, switch_to_main_page_callback):
        super().__init__()
        self.switch_to_main_page_callback = switch_to_main_page_callback
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height - 80)  # minus top bar height

        # Enemy Player ID
        self.enemy_label = QLabel("Enemy Player ID:", self)
        self.enemy_label.setGeometry(289, 150 - 30, 90, 25)

        self.enemy_input = QLineEdit(self)
        self.enemy_input.setGeometry(378, 150 - 30, 120, 25)

        # Stake
        self.stake_label = QLabel("Stake:", self)
        self.stake_label.setGeometry(289, 204 - 30, 90, 25)

        self.stake_input = QLineEdit(self)
        self.stake_input.setGeometry(378, 204 - 30, 120, 25)

        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.setGeometry(363, 300, 80, 30)

        # Go Back
        self.back_button = QPushButton("<---", self)
        self.back_button.setGeometry(9, 320, 80, 30)
        self.back_button.clicked.connect(self.switch_to_main_page_callback)


# ------------------------------ MainWidget ------------------------------ #
class MainWidget(QWidget):
    """
    This widget holds:
      - always visible top-bar (coins count, withdraw button, deposit button, send buttons, account data).
      - QStackedWidget showing changing pages
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(width, height)

        # Overall layout: vertical
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 1) TopBar
        self.top_bar = TopBar(self)
        layout.addWidget(self.top_bar)

        # 2) Center QStackedWidget for main page vs. wager search
        self.center_stack = QStackedWidget(self)
        layout.addWidget(self.center_stack)

        # Create the two pages
        self.main_page = MainPage(self.show_wager_page)
        self.wager_page = WagerSearchPage(self.show_main_page)

        self.center_stack.addWidget(self.main_page)  # index 0
        self.center_stack.addWidget(self.wager_page)  # index 1

        self.center_stack.setCurrentWidget(self.main_page)

    # -------------- DIALOG METHODS -------------- #
    def show_withdraw_dialog(self):
        dialog = WithdrawDialog()
        if dialog.exec_() == QDialog.Accepted:
            amount = dialog.get_amount()
            print(f"Withdrawing {amount} coins")

    def show_deposit_dialog(self):
        dialog = DepositDialog()
        if dialog.exec_() == QDialog.Accepted:
            amount = dialog.get_amount()
            print(f"Depositing {amount} coins")

    def show_send_coins_dialog(self):
        dialog = SendCoinsDialog()
        if dialog.exec_() == QDialog.Accepted:
            player_id, amount = dialog.get_data()
            print(f"Sending {amount} coins to player ID {player_id}")

    def show_send_cards_dialog(self):
        dialog = SendCardsDialog()
        if dialog.exec_() == QDialog.Accepted:
            player_id, card_id = dialog.get_data()
            print(f"Sending card {card_id} to player ID {player_id}")

    # -------------- STACK-SWITCH METHODS -------------- #
    def show_main_page(self):
        self.center_stack.setCurrentWidget(self.main_page)

    def show_wager_page(self):
        self.center_stack.setCurrentWidget(self.wager_page)


# ------------------------------ MainWindow ------------------------------ #
class MainWindow(QWidget):
    """
    The MainWindow has a QStackedWidget that toggles between:
      - The LoginRegisterUI (page 0)
      - The MainWidget (page 1), which contains TopBar + center stack
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Application')
        self.setGeometry(100, 100, width, height)
        self.setFixedSize(width, height)

        # Stacked widget at the top level
        self.stacked_widget = QStackedWidget(self)

        # Create login/register page
        self.login_register_page = LoginRegisterUI(self.show_main_widget)
        # Create main widget (top bar + center content)
        self.main_widget_page = MainWidget()

        self.stacked_widget.addWidget(self.login_register_page)  # index 0
        self.stacked_widget.addWidget(self.main_widget_page)  # index 1

        # Use a layout for the MainWindow so the stacked widget fills it
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Start on login page
        self.stacked_widget.setCurrentIndex(0)

    def show_main_widget(self):
        """ Called after successful login. """
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


# -------------- NEW: SendCoinsDialog and SendCardsDialog -------------- #
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
