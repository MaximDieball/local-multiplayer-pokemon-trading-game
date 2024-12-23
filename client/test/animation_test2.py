import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGraphicsOpacityEffect
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flip Card Animation")
        self.setGeometry(100, 100, 600, 800)

        # card stack
        self.card_stack_label = QLabel(self)
        self.pixmap_back = QPixmap("back.png")
        self.card_stack_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_stack_label.setGeometry(200, 350, 200, 300)

        # Create and set up the card label
        self.card_label = QLabel(self)
        self.pixmap_front = QPixmap("card1.jpg")  # New image for the front of the card
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_label.setGeometry(200, 350, 200, 300)

        # Create and set up the button
        self.button = QPushButton("Flip Card", self)
        self.button.setGeometry(250, 750, 100, 30)
        self.button.clicked.connect(self.animate)

        # Initialize the first and second animations
        self.animation1 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation1.setDuration(1000)
        self.animation1.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation2 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation2.setDuration(1000)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)

        self.has_flipped = False  # Track if the card has flipped

        # Create sparkle effects
        self.sparkle_label = QLabel(self)
        self.sparkle_label.lower()  # Move sparkles to the bottom layer
        self.sparkle_label.lower()
        self.sparkle_label.setGeometry(150, 150, 400, 400)  # Adjust as needed
        self.sparkle_movie = QMovie("sparkle.gif")  # Add a sparkle GIF file
        self.sparkle_label.setMovie(self.sparkle_movie)
        self.sparkle_label.setVisible(False)

    def animate(self):
        if self.has_flipped:
            return  # Prevent re-flipping

        current_geometry = self.card_label.geometry()

        # Configure the first animation (shrink to zero width)
        shrink_geometry = QRect(
            current_geometry.x() + current_geometry.width() // 2,
            current_geometry.y() - 310,
            0,
            current_geometry.height()
        )
        self.animation1.setStartValue(current_geometry)
        self.animation1.setEndValue(shrink_geometry)
        self.animation1.valueChanged.connect(self.update_card_back)

        # Configure the second animation (expand to full width with the front image)
        expand_geometry = QRect(
            current_geometry.x(),
            current_geometry.y() - 310,
            current_geometry.width(),
            current_geometry.height()
        )
        self.animation2.setStartValue(shrink_geometry)
        self.animation2.setEndValue(expand_geometry)
        self.animation2.valueChanged.connect(self.update_card_front)

        # Connect the first animation's finished signal to start the second animation
        self.animation1.finished.connect(self.start_second_animation)

        # Start the first animation
        self.animation1.start()

        self.has_flipped = True  # Mark the card as flipped

    def start_second_animation(self):
        self.animation2.start()
        QTimer.singleShot(300, self.show_sparkles)

    def show_sparkles(self):
        self.sparkle_movie.setScaledSize(QSize(400, 400))  # Resize the GIF
        self.sparkle_label.move(100, 0)  # Adjust sparkle position
        self.sparkle_label.setVisible(True)
        self.sparkle_movie.start()

        # Hide the sparkles after a short duration
        QTimer.singleShot(2000, lambda: self.sparkle_label.setVisible(False))

    def update_card_back(self, current_geometry):
        # Dynamically scale the back side of the card to match the new geometry
        self.card_label.setPixmap(
            self.pixmap_back.scaled(max(1, current_geometry.width()), current_geometry.height(), aspectRatioMode=0)
        )

    def update_card_front(self, current_geometry):
        # Dynamically scale the front side of the card to match the new geometry
        self.card_label.setPixmap(
            self.pixmap_front.scaled(max(1, current_geometry.width()), current_geometry.height(), aspectRatioMode=0)
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
