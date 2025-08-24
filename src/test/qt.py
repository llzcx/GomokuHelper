import sys
import random
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen


# 工作线程类，用于更新圆形坐标
class CircleUpdaterThread(QThread):
    # 定义信号，用于传递新的圆形坐标
    update_circle_signal = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            # 生成随机坐标
            x = random.randint(50, 350)
            y = random.randint(50, 250)

            # 发送坐标更新信号
            self.update_circle_signal.emit(x, y)

            # 等待一段时间
            time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()


# 主窗口部件，用于显示圆形
class CircleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.circle_x = 200  # 初始圆心x坐标
        self.circle_y = 150  # 初始圆心y坐标
        self.circle_radius = 30  # 圆的半径

        # 设置窗口大小和标题
        self.setFixedSize(400, 300)
        self.setWindowTitle("动态圆形显示")

    def paintEvent(self, event):
        # 绘制圆形
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿

        # 设置画笔和画刷
        pen = QPen(Qt.blue, 3)
        painter.setPen(pen)
        painter.setBrush(QColor(200, 200, 255))

        # 绘制圆形
        painter.drawEllipse(self.circle_x - self.circle_radius,
                            self.circle_y - self.circle_radius,
                            self.circle_radius * 2,
                            self.circle_radius * 2)

    def update_circle_position(self, x, y):
        # 更新圆形坐标
        self.circle_x = x
        self.circle_y = y
        self.update()  # 触发重绘


# 主窗口
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建圆形显示部件
        self.circle_widget = CircleWidget()
        self.setCentralWidget(self.circle_widget)

        # 创建并启动更新线程
        self.update_thread = CircleUpdaterThread()
        self.update_thread.update_circle_signal.connect(self.circle_widget.update_circle_position)
        self.update_thread.start()

    def closeEvent(self, event):
        # 窗口关闭时停止线程
        self.update_thread.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())