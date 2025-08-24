import sys
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any
import numpy as np
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QWidget

from src.engine.board import ChessBoard, BLACK


class UserReport:
    """用户界面抽象基类"""

    @abstractmethod
    def initialize(self, config: dict = None) -> bool:
        """初始化用户界面"""
        pass

    @abstractmethod
    def update(self,
               image: Optional[np.ndarray],
               board_state: np.ndarray,
               best_move: Tuple[int, int],
               analysis_info: dict) -> bool:
        """
        更新界面显示

        参数:
            image: 原始图像（可选）
            board_state: 识别出的棋盘状态
            best_move: 推荐的最佳落子位置
            analysis_info: 分析引擎返回的附加信息
        """
        pass

    @abstractmethod
    def get_user_input(self) -> Optional[dict]:
        """获取用户输入（如有）"""
        pass

    @abstractmethod
    def close(self):
        """关闭界面"""
        pass

    @abstractmethod
    def event_loop(self):
        """关闭界面"""
        pass


class QTReport(UserReport):
    config = {
        "top": 0,  # 棋盘距离屏幕顶部距离
        "left": 0,  # 棋盘距离屏幕左边距离
        "grid_size": 15,  # 棋盘大小（正方形）
        "cell_size": 0,  # 每个格子大小
        "piece_size": 0,  # 每个棋子的大小
        "image_size": 1314,  # 整个棋盘大小（正方形，像素为单位）
    }

    def __init__(self):
        self.analysis_info = None
        self.board_state = None
        self.event_loop_thread = None
        self.overlay = None
        self.best_move = None
        self.app = None
        # 检查是否已经有QApplication实例
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

    def initialize(self, config: dict = None) -> bool:
        """初始化配置并创建 overlay 窗口"""
        if config:
            self.config.update(config)

        self.overlay = OverlayWindow(self)
        return True

    def update(self,
               image: Optional[np.ndarray],
               board_state: ChessBoard,
               best_move: Tuple[int, int],
               analysis_info: dict) -> bool:
        """更新界面显示，绘制最佳落子位置"""
        if not self.overlay:
            self.initialize()
        self.board_state = board_state
        self.best_move = best_move
        self.analysis_info = analysis_info

        self.overlay.update()
        return True

    def get_user_input(self) -> Optional[dict]:
        return None

    def close(self):
        if self.overlay:
            self.overlay.close()
            self.overlay = None

    def event_loop(self):
        sys.exit(self.app.exec_())


class OverlayWindow(QWidget):
    def __init__(self, report: QTReport):
        super().__init__()
        self.report = report
        self.init_ui()

    def init_ui(self):
        # 设置窗口为无边框、置顶且背景透明
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # 工具窗口，任务栏不显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 根据棋盘配置设置窗口位置和大小
        self.setGeometry(
            self.report.config["left"],
            self.report.config["top"],
            self.report.config["image_size"],
            self.report.config["image_size"]
        )
        self.show()

    def paintEvent(self, event):
        if not self.report.best_move:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿，使圆圈更平滑

        # 获取最佳落子位置
        x, y = self.report.best_move

        # 计算棋子中心位置
        config = self.report.config
        center_x = config["piece_size"] / 2 + config["cell_size"] * x
        center_y = config["piece_size"] / 2 + config["cell_size"] * y

        # 计算圆圈半径（棋子大小的一半）
        radius = config["piece_size"] / 2

        # 设置圆圈样式：红色虚线
        pen = QPen(QColor(255, 0, 0, 200))  # 半透明红色
        pen.setWidth(3)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # 不填充内部
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))

        # 绘制圆圈
        painter.drawEllipse(
            QPoint(int(center_x), int(center_y)),
            int(radius),
            int(radius)
        )

        # 以下是新增的文本绘制逻辑
        # 设置文本颜色和字体
        text_pen = QPen(QColor(0, 0, 0))  # 黑色文本
        painter.setPen(text_pen)

        font = QFont()
        font.setPointSize(12)  # 设置字体大小
        painter.setFont(font)

        current_player_text = "执黑" if self.report.analysis_info["rootInfo"].get('currentPlayer') == BLACK else "执白"
        text = self.report.board_state.render_numpy_board() + "\n" + current_player_text
        rect = QRect(40, 40, 200, 100)  # x, y, width, height
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop,text)


def update_task():
    # 创建棋盘状态
    board = ChessBoard(size=15)

    # 主程序可以继续执行其他任务
    for i in range(5):
        report.update(None, board, (i, 7), {})
        print(f"主程序继续运行... {i + 1}")
        time.sleep(1)

    print("程序执行完毕")


if __name__ == "__main__":
    print("程序开始执行")
    report = QTReport()
    config = {
        "top": 69,
        "left": 625,
        "cell_size": 89,
        "piece_size": 69,
        "image_size": 1314,
    }
    report.initialize(config)

    my_thread = threading.Thread(target=update_task)
    my_thread.start()

    print("开启event loop")
    report.event_loop()
