import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget

# Global variables for circle parameters
circle_radius = 50
outline_width = 2
outline_color = Qt.white


class GameOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        self.setGeometry(0, 0, screen_width, screen_height)  # Set the overlay size to match the screen
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw a transparent background
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawRect(self.rect())

        # Calculate the circle's center position
        circle_center_x = self.width() // 2
        circle_center_y = self.height() // 2

        # Draw the circle outline
        painter.setPen(QColor(outline_color))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawEllipse(circle_center_x - circle_radius, circle_center_y - circle_radius,
                            circle_radius * 2, circle_radius * 2)


def main():
    app = QApplication(sys.argv)
    overlay = GameOverlay()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
