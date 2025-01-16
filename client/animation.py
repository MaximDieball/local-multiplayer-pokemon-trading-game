import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize, Qt
from PyQt5.QtGui import QPixmap, QMovie

class MainWindow(QMainWindow):
    def __init__(self, card_paths):
        super().__init__()
        self.setWindowTitle("Flip Card Animation")
        self.setGeometry(100, 100, 600, 800)

        # 1) Resolve absolute paths for our image files
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # back.png
        back_path = os.path.join(script_dir, "test", "back.png")
        print(back_path)

        # sparkle.gif
        sparkle_path = os.path.join(script_dir, "test", "sparkle.gif")

        # Resolve the full paths to each card in card_paths
        # so if card_paths = ["test/card1.jpg", "test/card2.jpg", ...],
        # we ensure they're converted to absolute file paths
        self.card_paths = [
            os.path.join(script_dir, path)
            for path in card_paths
        ]

        # 2) Create the "card stack" label (which shows the back of a stack of cards)
        self.card_stack_label = QLabel(self)
        self.pixmap_back = QPixmap(back_path)
        self.card_stack_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_stack_label.setGeometry(200, 350, 200, 300)

        # 3) Create the "card_label" that will animate flipping from back to front
        self.card_label = QLabel(self)
        self.pixmap_front = None
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_label.setGeometry(200, 350, 200, 300)
        self.beginning_card_geometry = self.card_label.geometry()

        # 4) First and second animations (for the flip)
        self.animation1 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation1.setDuration(1000)
        self.animation1.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation2 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation2.setDuration(1000)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)

        self.has_flipped = False
        self.animation_running = False

        # 5) Sparkle effect
        self.sparkle_label = QLabel(self)
        self.sparkle_label.lower()
        self.sparkle_label.setGeometry(150, 150, 400, 400)
        self.sparkle_movie = QMovie(sparkle_path)
        self.sparkle_label.setMovie(self.sparkle_movie)
        self.sparkle_label.setVisible(False)

    def mousePressEvent(self, event):
        # Flip the next card on left click
        if event.button() == Qt.LeftButton:
            self.click()

    def click(self):
        if self.card_paths:
            if not self.has_flipped and not self.animation_running:
                self.animation_running = True
                # Use the first path in self.card_paths for the "front" image
                self.pixmap_front = QPixmap(self.card_paths[0])
                self.animation()
                self.card_paths.pop(0)

                # If that was the last card, clear the card stack label
                if not self.card_paths:
                    self.card_stack_label.clear()

            elif not self.animation_running:
                # User clicked again after finishing flipping => reset
                self.reset_card()
                self.has_flipped = False

    def reset_card(self):
        print("reset")
        self.card_label.setGeometry(self.beginning_card_geometry)
        self.card_label.setPixmap(self.pixmap_back.scaled(200, 300, aspectRatioMode=0))
        self.card_label.move(200, 350)

    def animation(self):
        current_geometry = self.card_label.geometry()

        # 1) Shrink to zero width (flip halfway)
        shrink_geometry = QRect(
            current_geometry.x() + current_geometry.width() // 2,
            current_geometry.y() - 310,
            0,
            current_geometry.height()
        )
        self.animation1.setStartValue(current_geometry)
        self.animation1.setEndValue(shrink_geometry)
        self.animation1.valueChanged.connect(self.update_card_back)

        # 2) Expand back to full width with the front image
        expand_geometry = QRect(
            current_geometry.x(),
            current_geometry.y() - 310,
            current_geometry.width(),
            current_geometry.height()
        )
        self.animation2.setStartValue(shrink_geometry)
        self.animation2.setEndValue(expand_geometry)
        self.animation2.valueChanged.connect(self.update_card_front)

        # Chain animations
        self.animation1.finished.connect(self.start_second_animation)
        self.animation2.finished.connect(lambda: setattr(self, 'animation_running', False))

        # Start the first animation
        self.animation1.start()

    def start_second_animation(self):
        self.animation2.start()
        QTimer.singleShot(300, self.show_sparkles)

    def show_sparkles(self):
        self.sparkle_movie.setScaledSize(QSize(400, 400))
        self.sparkle_label.move(100, 0)
        self.sparkle_label.setVisible(True)
        self.sparkle_movie.start()

        # Hide sparkles after 2 seconds
        QTimer.singleShot(2000, lambda: self.sparkle_label.setVisible(False))
        self.has_flipped = True

    def update_card_back(self, current_geometry):
        # Scale the back image as the card shrinks
        self.card_label.setPixmap(
            self.pixmap_back.scaled(
                max(1, current_geometry.width()),
                current_geometry.height(),
                aspectRatioMode=0
            )
        )

    def update_card_front(self, current_geometry):
        # Scale the front image as it expands
        self.card_label.setPixmap(
            self.pixmap_front.scaled(
                max(1, current_geometry.width()),
                current_geometry.height(),
                aspectRatioMode=0
            )
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Example usage:
    # The card_paths list should be *relative* to this Python file,
    # but we convert them to absolute in the constructor above.
    # So if inside the "test" folder you have "card1.jpg", "card2.jpg", "card3.jpg",
    # you can pass them like this:
    card_list = ["test/card1.jpg", "test/card2.jpg", "test/card3.jpg"]
    window = MainWindow(card_list)
    window.show()
    sys.exit(app.exec_())
