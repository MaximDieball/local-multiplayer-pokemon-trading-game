import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QStackedWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRect

width = 800
height = 500

class LoginRegisterUI(QWidget):
    def __init__(self, switch_to_main_interface_callback):
        super().__init__()
        self.init_ui(switch_to_main_interface_callback)

    def init_ui(self, switch_to_main_interface_callback):
        self.setFixedSize(width, height)  # Fixed size for the Login/Register page

        # Login Section
        login_label = QLabel("Login", self)
        login_label.setGeometry(QRect(int(int(width/2))-300, 30, 100, 30))

        login_name_label = QLabel("Name:", self)
        login_name_label.setGeometry(QRect(int(int(width/2))-400, 70, 60, 20))

        self.login_name_input = QLineEdit(self)
        self.login_name_input.setGeometry(QRect(int(width/2)-300, 70, 150, 20))

        login_password_label = QLabel("Password:", self)
        login_password_label.setGeometry(QRect(int(width/2)-400, 110, 60, 20))

        self.login_password_input = QLineEdit(self)
        self.login_password_input.setGeometry(QRect(int(width/2)-300, 110, 150, 20))
        self.login_password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login", self)
        login_button.setGeometry(QRect(int(width/2)-300, 150, 80, 30))
        login_button.clicked.connect(switch_to_main_interface_callback)

        # Register Section
        register_label = QLabel("Register", self)
        register_label.setGeometry(QRect(int(width/2)+100, 30, 100, 30))

        register_name_label = QLabel("Name:", self)
        register_name_label.setGeometry(QRect(int(width/2)+100, 70, 60, 20))

        self.register_name_input = QLineEdit(self)
        self.register_name_input.setGeometry(QRect(int(width/2)+100, 70, 150, 20))

        register_password_label = QLabel("Password:", self)
        register_password_label.setGeometry(QRect(int(width/2)+100, 110, 60, 20))

        self.register_password_input = QLineEdit(self)
        self.register_password_input.setGeometry(QRect(int(width/2)+100, 110, 150, 20))
        self.register_password_input.setEchoMode(QLineEdit.Password)

        register_button = QPushButton("Register", self)
        register_button.setGeometry(QRect(int(width/2)+100, 150, 80, 30))
        register_button.clicked.connect(switch_to_main_interface_callback)


class MainInterfaceUI(QWidget):
    def __init__(self, switch_to_wager_search_callback):
        super().__init__()
        self.init_ui(switch_to_wager_search_callback)

    def init_ui(self, switch_to_wager_search_callback):
        self.setFixedSize(width, height)  # Fixed size for the Main Interface page

        # Top Left Coin Image
        top_left_image = QLabel(self)
        top_left_pixmap = QPixmap("images/coin.png")  
        top_left_image.setPixmap(top_left_pixmap)
        top_left_image.setGeometry(QRect(0, 0, 60, 60))
        top_left_image.setScaledContents(True)

        # Top Left Coin Count
        text_box = QLabel("coin_count", self)
        text_box.setText("91234")
        text_box.setAlignment(Qt.AlignRight)
        text_box.setGeometry(QRect(60, 20, 50, 50))

        # Top Right Image
        top_right_image = QLabel(self)
        top_right_pixmap = QPixmap("images/profile.png") 
        top_right_image.setPixmap(top_right_pixmap)
        top_right_image.setGeometry(QRect(width - 100, 0, 60, 60))
        top_right_image.setScaledContents(True)

        # Top Buttons
        deposit_button = QPushButton("Deposit", self)
        deposit_button.setGeometry(QRect(150, 15, 80, 30))

        withdraw_button = QPushButton("Withdraw", self)
        withdraw_button.setGeometry(QRect(250, 15, 80, 30))

        send_button = QPushButton("Send", self)
        send_button.setGeometry(QRect(350, 15, 80, 30))

        # Pokeball Image
        main_image = QLabel(self)
        main_image_pixmap = QPixmap("images/pokeball.png")
        main_image.setPixmap(main_image_pixmap)
        main_image.setGeometry(QRect(50, 120, 200, 200))
        main_image.setScaledContents(True)

        # Profile Data Text Box
        text_box = QLabel("profile_data", self)
        text_box.setText('''
        ID : 1234
        Name : ADMIN
        Balance : 300
        RankedPoints : 100
        ''')
        text_box.setAlignment(Qt.AlignRight)
        text_box.setGeometry(QRect(width - 250, 60, 200, 200))

        # Middle Buttons
        open_packs_button = QPushButton("Open packs", self)
        open_packs_button.setGeometry(QRect(350, 100, 200, 100))

        inventory_button = QPushButton("Inventory", self)
        inventory_button.setGeometry(QRect(350, 200, 200, 100))

        fight_button = QPushButton("Fight", self)
        fight_button.setGeometry(QRect(350, 300, 200, 100))
        fight_button.clicked.connect(switch_to_wager_search_callback)


class WagerSearchUI(QWidget):
    def __init__(self, switch_to_main_search_callback):
        super().__init__()
        self.init_ui(switch_to_main_search_callback)

    def init_ui(self, switch_to_main_search_callback):
        self.setFixedSize(width, height)
        wager_label = QLabel("Wager", self)
        wager_label.setGeometry(QRect(180, 30, 100, 30))

        self.wager_label_input = QLineEdit(self)
        self.wager_label_input.setGeometry(QRect(220, 40, 150, 20))

        enemy_label = QLabel("Enemy_ID", self)
        enemy_label.setGeometry(QRect(155,60,100,93))

        self.enemy_label_input = QLineEdit(self)
        self.enemy_label_input.setGeometry(QRect(220,100,150,20))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Application')
        self.setGeometry(100, 100, width, height)  # Fixed window size
        self.setFixedSize(width, height)

        # Stacked Widget to switch between pages
        self.stacked_widget = QStackedWidget(self)

        # Create the Login/Register, Main Interface, and Wager Search pages
        self.login_register_page = LoginRegisterUI(self.show_main_interface)
        self.main_interface_page = MainInterfaceUI(self.show_wager_search)
        self.wager_search_page = WagerSearchUI(self.show_main_interface)

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.login_register_page)
        self.stacked_widget.addWidget(self.main_interface_page)
        self.stacked_widget.addWidget(self.wager_search_page)

        # Set the Login/Register page as the default
        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.stacked_widget.setCurrentWidget(self.login_register_page)

    def show_main_interface(self):
        # Switch to the Main Interface page
        self.stacked_widget.setCurrentWidget(self.main_interface_page)

    def show_wager_search(self):
        # Switch to the Wager Search page
        self.stacked_widget.setCurrentWidget(self.wager_search_page)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
