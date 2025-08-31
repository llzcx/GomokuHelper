import json
import logging
import sys
import threading
import time
import traceback
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, List
import numpy as np
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QWidget

from src.engine.board import ChessBoard, BLACK, WHITE, MoveItem
from src.engine.util import get_win_rate_color


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
        self.board_state = None
        self.analysis_info = {}
        self.board_state: ChessBoard
        self.event_loop_thread = None
        self.overlay = None
        self.best_moves: List[MoveItem] = []
        self.app = None
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

    def initialize(self, config: dict = None) -> bool:
        if config:
            self.config.update(config)

        self.overlay = OverlayWindow(self)
        return True

    def update(self,
               image: Optional[np.ndarray],
               board_state: ChessBoard,
               best_move: List[MoveItem],
               analysis_info: dict) -> bool:
        if not self.overlay:
            self.initialize()
        self.board_state = board_state
        self.best_moves = best_move
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
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setGeometry(
            self.report.config["left"],
            self.report.config["top"],
            int(self.report.config["image_size"] * 1.5),
            self.report.config["image_size"]
        )
        self.show()

    def paintEvent(self, event):
        if len(self.report.best_moves) == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for item in self.report.best_moves:
            x, y = item.move
            config = self.report.config
            center_x = config["piece_size"] / 2 + config["cell_size"] * x
            center_y = config["piece_size"] / 2 + config["cell_size"] * y
            radius = config["piece_size"] / 2

            pen = QPen(get_win_rate_color(item.winrate))
            pen.setWidth(3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)

            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))

            painter.drawEllipse(
                QPoint(int(center_y), int(center_x)),
                int(radius),
                int(radius)
            )

            text_pen = QPen(QColor(0, 255, 0, 255))
            painter.setPen(text_pen)

            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)

            text = f"{item.visits}\n{item.winrate:.2%}"

            text_rect = QRectF(
                center_y - radius,
                center_x - radius,
                radius * 2,
                radius * 2
            )

            painter.drawText(
                text_rect,
                Qt.AlignCenter,
                text
            )

        left = self.report.config["image_size"]
        top = 0
        try:
            text_pen = QPen(QColor(0, 0, 0))
            painter.setPen(text_pen)

            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)

            player_info = "黑方" if self.report.board_state.determine_current_player() == BLACK else "白方"

            board_text = self.report.board_state.render_numpy_board()

            gtp_text = ""
            for item in self.report.best_moves:
                gtp_text = gtp_text + str(item) + "\n"

            text = f"{board_text}\n当前执棋: {player_info}\n{gtp_text}"

            text_rect = painter.boundingRect(QRect(left, top, 400, 300),
                                             Qt.AlignLeft | Qt.AlignTop,
                                             text)

            rect_width = text_rect.width() + 20
            rect_height = text_rect.height() + 20
            rect = QRect(left, top, rect_width, rect_height)

            painter.fillRect(rect, QColor(255, 255, 255, 200))
            painter.drawRect(rect)

            painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, text)

        except Exception as e:
            traceback.print_exc()
            logging.info(f"Text drawing error: {str(e)}")