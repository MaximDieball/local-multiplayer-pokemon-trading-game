import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel
)
from PyQt5.QtCore import (
    QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize
)
from PyQt5.QtGui import QPixmap, QMovie


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flip Card Animation")

        # ------------------ NEW WINDOW SIZE ------------------ #
        self.setGeometry(100, 100, 800, 500)

        # Card fronts: 3 cards to flip
        self.card_front_paths = [
            "card1.jpg",
            "card2.jpg",
            "card3.jpg",
        ]
        self.current_card_index = 0

        # --------------- MAKE CARDS SMALLER (120×180) --------------- #
        self.card_width = 120
        self.card_height = 180

        # Bottom card stack (always visible)
        # Place it so the cards are smaller and centered-ish
        self.card_stack_label = QLabel(self)
        self.pixmap_back = QPixmap("back.png")
        self.card_stack_label.setPixmap(
            self.pixmap_back.scaled(self.card_width, self.card_height, aspectRatioMode=0)
        )
        # For 800×500, let's place at (340, 140) so it doesn't go offscreen
        self.card_stack_label.setGeometry(340, 140, self.card_width, self.card_height)

        # Main flipping card label
        self.card_label = QLabel(self)
        self.card_label.setPixmap(
            self.pixmap_back.scaled(self.card_width, self.card_height, aspectRatioMode=0)
        )
        self.card_label.setGeometry(340, 140, self.card_width, self.card_height)
        self.original_card_geometry = self.card_label.geometry()

        # Flip button near the bottom
        self.button = QPushButton("Flip Card", self)
        # Place around (360, 350) or so
        self.button.setGeometry(360, 350, 80, 30)
        self.button.clicked.connect(self.flip_next_card)

        # Animations
        self.animation1 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation1.setDuration(1000)
        self.animation1.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation2 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation2.setDuration(1000)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)

        self.has_flipped = False

        # Sparkles
        self.sparkle_label = QLabel(self)
        self.sparkle_label.lower()
        # A bit smaller area, near the top
        self.sparkle_label.setGeometry(300, 10, 200, 200)
        self.sparkle_movie = QMovie("sparkle.gif")
        self.sparkle_label.setMovie(self.sparkle_movie)
        self.sparkle_label.setVisible(False)

    def flip_next_card(self):
        """Called when the button is pressed. Flips the *next* card if available."""
        if self.current_card_index >= len(self.card_front_paths):
            print("No more cards to flip!")
            return

        if self.has_flipped:
            return

        # Reset card geometry to original stack
        self.card_label.setGeometry(self.original_card_geometry)
        self.card_label.raise_()

        self.has_flipped = True

        self.setup_animations()
        # Hide the bottom stack if we flip the last card
        if self.current_card_index == len(self.card_front_paths) - 1:
            self.card_stack_label.hide()

        self.animation1.start()

    def setup_animations(self):
        """Disconnect old signals, set new start/end geometry for shrink–expand."""
        self.animation1.stop()
        self.animation2.stop()

        try:
            self.animation1.finished.disconnect()
            self.animation1.valueChanged.disconnect()
        except TypeError:
            pass

        try:
            self.animation2.finished.disconnect()
            self.animation2.valueChanged.disconnect()
        except TypeError:
            pass

        current_geometry = self.card_label.geometry()

        # We'll move the card up ~80 px (instead of 310)
        # so it remains in view in an 800×500 window.
        shrink_geometry = QRect(
            current_geometry.x() + current_geometry.width() // 2,  # shift x to center
            current_geometry.y() - 80,                             # move up
            0,                                                     # shrink width to 0
            current_geometry.height()
        )
        expand_geometry = QRect(
            current_geometry.x(),
            current_geometry.y() - 80,
            current_geometry.width(),
            current_geometry.height()
        )

        self.animation1.setStartValue(current_geometry)
        self.animation1.setEndValue(shrink_geometry)
        self.animation1.valueChanged.connect(self.update_card_back)
        self.animation1.finished.connect(self.start_second_animation)

        self.animation2.setStartValue(shrink_geometry)
        self.animation2.setEndValue(expand_geometry)
        self.animation2.valueChanged.connect(self.update_card_front)
        self.animation2.finished.connect(self.animation_finished)

    def start_second_animation(self):
        self.animation2.start()
        QTimer.singleShot(300, self.show_sparkles)

    def animation_finished(self):
        """Called after the expand animation finishes. Increments card index."""
        self.has_flipped = False
        self.current_card_index += 1
        print(f"Flip finished. Next card index: {self.current_card_index}")

    def show_sparkles(self):
        # Let's scale the sparkles to, say, 150×150
        self.sparkle_movie.setScaledSize(QSize(150, 150))
        # Maybe move them slightly
        self.sparkle_label.move(320, 0)
        self.sparkle_label.setVisible(True)
        self.sparkle_movie.start()
        QTimer.singleShot(2000, lambda: self.sparkle_label.setVisible(False))

    def update_card_back(self, current_geometry):
        """Display the back while shrinking."""
        self.card_label.setPixmap(
            self.pixmap_back.scaled(
                max(1, current_geometry.width()),
                current_geometry.height(),
                aspectRatioMode=0
            )
        )

    def update_card_front(self, current_geometry):
        """Display the current card while expanding."""
        if self.current_card_index < len(self.card_front_paths):
            pixmap_front = QPixmap(self.card_front_paths[self.current_card_index])
        else:
            pixmap_front = QPixmap()

        self.card_label.setPixmap(
            pixmap_front.scaled(
                max(1, current_geometry.width()),
                current_geometry.height(),
                aspectRatioMode=0
            )
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
