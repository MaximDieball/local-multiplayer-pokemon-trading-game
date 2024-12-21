import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QStackedWidget, QVBoxLayout
from PyQt5.QtCore import QRect


class LoginRegisterUI(QWidget):
    def __init__(self, switch_to_main_interface_callback):
        super().__init__()
        self.init_ui(switch_to_main_interface_callback)

    def init_ui(self, switch_to_main_interface_callback):
        self.setFixedSize(500, 300)  # Fixed size for the Login/Register page

        # Login Section
        login_label = QLabel("Login", self)
        login_label.setGeometry(QRect(80, 30, 100, 30))

        login_name_label = QLabel("Name:", self)
        login_name_label.setGeometry(QRect(50, 70, 60, 20))

        self.login_name_input = QLineEdit(self)
        self.login_name_input.setGeometry(QRect(120, 70, 150, 20))

        login_password_label = QLabel("Password:", self)
        login_password_label.setGeometry(QRect(50, 110, 60, 20))

        self.login_password_input = QLineEdit(self)
        self.login_password_input.setGeometry(QRect(120, 110, 150, 20))
        self.login_password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login", self)
        login_button.setGeometry(QRect(120, 150, 80, 30))
        login_button.clicked.connect(switch_to_main_interface_callback)

        # Register Section
        register_label = QLabel("Register", self)
        register_label.setGeometry(QRect(330, 30, 100, 30))

        register_name_label = QLabel("Name:", self)
        register_name_label.setGeometry(QRect(300, 70, 60, 20))

        self.register_name_input = QLineEdit(self)
        self.register_name_input.setGeometry(QRect(370, 70, 150, 20))

        register_password_label = QLabel("Password:", self)
        register_password_label.setGeometry(QRect(300, 110, 60, 20))

        self.register_password_input = QLineEdit(self)
        self.register_password_input.setGeometry(QRect(370, 110, 150, 20))
        self.register_password_input.setEchoMode(QLineEdit.Password)

        register_button = QPushButton("Register", self)
        register_button.setGeometry(QRect(370, 150, 80, 30))
        register_button.clicked.connect(switch_to_main_interface_callback)


class MainInterfaceUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(700, 400)  # Fixed size for the Main Interface page

        # Top Left Image
        top_left_image = QLabel("Image", self)
        top_left_image.setGeometry(QRect(20, 20, 60, 60))

        # Top Right Image
        top_right_image = QLabel("Image", self)
        top_right_image.setGeometry(QRect(620, 20, 60, 60))

        # Top Buttons
        deposit_button = QPushButton("Deposit", self)
        deposit_button.setGeometry(QRect(220, 30, 80, 30))

        withdraw_button = QPushButton("Withdraw", self)
        withdraw_button.setGeometry(QRect(320, 30, 80, 30))

        send_button = QPushButton("Send", self)
        send_button.setGeometry(QRect(420, 30, 80, 30))

        # Main Image
        main_image = QLabel("Image", self)
        main_image.setGeometry(QRect(50, 120, 200, 200))

        # Text Box
        text_box = QLabel("Text box", self)
        text_box.setGeometry(QRect(450, 120, 200, 200))

        # Bottom Buttons
        open_packs_button = QPushButton("Open packs", self)
        open_packs_button.setGeometry(QRect(220, 350, 100, 30))

        inventory_button = QPushButton("Inventory", self)
        inventory_button.setGeometry(QRect(330, 350, 100, 30))

        fight_button = QPushButton("Fight", self)
        fight_button.setGeometry(QRect(440, 350, 100, 30))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Application')
        self.setGeometry(100, 100, 700, 400)  # Fixed window size
        self.setFixedSize(700, 400)

        # Stacked Widget to switch between pages
        self.stacked_widget = QStackedWidget(self)

        # Create the Login/Register and Main Interface pages
        self.login_register_page = LoginRegisterUI(self.show_main_interface)
        self.main_interface_page = MainInterfaceUI()

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.login_register_page)
        self.stacked_widget.addWidget(self.main_interface_page)

        # Set the Login/Register page as the default
        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)

    def show_main_interface(self):
        # Switch to the Main Interface page
        self.stacked_widget.setCurrentWidget(self.main_interface_page)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
