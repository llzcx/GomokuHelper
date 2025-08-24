from abc import ABC, abstractmethod
from typing import Optional, Tuple

import cv2
import numpy as np

from src.engine.board import ChessBoard, BLACK, WHITE


class BoardRecognizer(ABC):
    """棋盘识别抽象基类"""

    @abstractmethod
    def initialize(self, model_path: Optional[str] = None, config: dict = None) -> bool:
        """初始化识别器"""
        pass

    @abstractmethod
    def recognize(self, image: np.ndarray) -> Tuple[Optional[ChessBoard], dict]:
        """
        识别棋盘状态

        返回:
            board_state: 15x15的numpy数组，0=空, 1=黑子, 2=白子
            meta_info: 包含识别置信度等元信息
        """
        pass

    @abstractmethod
    def get_recognizer_info(self) -> dict:
        """获取识别器信息"""
        pass


class AdvancedBoardRecognizer(BoardRecognizer):
    def __init__(self):
        self.initialized = False
        # 基础配置 - 基于提供的精确参数
        self.config = {}
        self.info = {
            "name": "Precise Parameter-based Board Recognizer",
            "version": "1.0",
            "parameters": self.config.copy()
        }
        # 预计算交叉点坐标
        self.intersection_points = None

    def initialize(self, model_path: Optional[str] = None, config: dict = None) -> bool:
        """初始化识别器，可更新配置并预计算交叉点坐标"""
        if config:
            self.config.update(config)
            self.info["parameters"] = self.config.copy()

        # 预计算所有交叉点的坐标
        self._calculate_intersection_points()
        self.initialized = True
        return True

    def _calculate_intersection_points(self):
        """基于精确参数计算15x15棋盘所有交叉点的坐标"""
        grid_size = self.config["grid_size"]
        cell_size = self.config["cell_size"]
        piece_radius = self.config["piece_size"] / 2

        # 第一个交叉点的坐标（左上角）
        start = piece_radius

        # 初始化坐标数组
        self.intersection_points = np.zeros((grid_size, grid_size, 2), dtype=np.int32)

        # 计算每个交叉点的(x, y)坐标
        for i in range(grid_size):
            for j in range(grid_size):
                x = int(start + j * cell_size)
                y = int(start + i * cell_size)
                self.intersection_points[i, j] = (x, y)

    def recognize(self, image: np.ndarray) -> Tuple[Optional[ChessBoard], dict]:
        if not self.initialized:
            return None, {"confidence": 0.0, "error": "Recognizer not initialized"}

        if image.shape[0] != self.config["image_size"] or image.shape[1] != self.config["image_size"]:
            return None, {"confidence": 0.0,
                          "error": f"Image size must be {self.config['image_size']}x{self.config['image_size']}"}

        try:
            # 转换为灰度图以便处理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

            # 初始化棋盘状态
            board_size = self.config["grid_size"]
            board_state = ChessBoard(size=board_size)
            total_confidence = 0.0
            piece_count = 0

            # 检查每个交叉点
            roi_radius = int(self.config["piece_size"] * 0.4)  # 取棋子尺寸的40%作为ROI半径
            for i in range(self.config["grid_size"]):
                for j in range(self.config["grid_size"]):
                    x, y = self.intersection_points[i, j]
                    # 获取交叉点周围的ROI
                    roi = self._get_roi(gray, (x, y), roi_radius)
                    if roi.size == 0:
                        continue

                    # 计算平均亮度（归一化到0-1）
                    avg_brightness = np.mean(roi) / 255.0

                    # 判断棋子类型
                    if avg_brightness < self.config["black_threshold"]:
                        board_state.place_piece(i, j, BLACK)  # 黑子
                        total_confidence += 0.95
                        piece_count += 1
                    elif avg_brightness > self.config["white_threshold"]:
                        board_state.place_piece(i, j, WHITE)  # 白子
                        total_confidence += 0.95
                        piece_count += 1
                    # 否则为空格子（0）

            # 计算平均置信度
            total_cells = board_size * board_size
            avg_confidence = total_confidence / total_cells if total_cells > 0 else 0

            meta_info = {
                "confidence": round(avg_confidence, 3),
                "piece_count": board_state.count_pieces(BLACK) + board_state.count_pieces(WHITE),
                "black_count": board_state.count_pieces(BLACK),
                "white_count": board_state.count_pieces(WHITE),
                "image_size": (image.shape[1], image.shape[0]),
                "parameters_used": self.config.copy()
            }

            return board_state, meta_info

        except Exception as e:
            return None, {"confidence": 0.0, "error": str(e)}

    def _get_roi(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> np.ndarray:
        """获取中心点周围的ROI区域，确保不超出图像边界"""
        x, y = center
        height, width = image.shape[:2]

        # 计算ROI边界，确保在图像范围内
        x1 = max(0, x - radius)
        x2 = min(width, x + radius + 1)
        y1 = max(0, y - radius)
        y2 = min(height, y + radius + 1)

        return image[y1:y2, x1:x2]

    def get_recognizer_info(self) -> dict:
        return self.info
