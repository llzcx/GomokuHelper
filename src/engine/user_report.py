from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any
import numpy as np


class UserReport(ABC):
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


# 具体实现示例：控制台界面
class ConsoleReport(UserReport):
    def __init__(self):
        self.config = {}
        self.is_initialized = False

    def initialize(self, config: dict = None) -> bool:
        self.config = config or {}
        self.is_initialized = True
        print("五子棋辅助系统启动")
        return True

    def update(self, image, board_state, best_move, analysis_info):
        if not self.is_initialized:
            return False

        try:
            print(f"\n推荐落子位置: {best_move}")
            print(f"分析信息: {analysis_info}")
            # 简单打印棋盘状态
            print("当前棋盘:")
            for row in board_state:
                print(" ".join(str(cell) for cell in row))
            return True
        except Exception as e:
            print(f"界面更新失败: {e}")
            return False

    def get_user_input(self):
        # 控制台界面可以接收一些简单命令
        return None

    def close(self):
        print("五子棋辅助系统关闭")
        self.is_initialized = False


# 具体实现示例：屏幕叠加界面
class OverlayReport(UserReport):
    def __init__(self):
        self.config = {}
        self.is_initialized = False
        self.window = None

    def initialize(self, config: dict = None) -> bool:
        try:
            import cv2
            self.config = config or {}
            self.is_initialized = True
            cv2.namedWindow("Gobang Assistant", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Gobang Assistant", cv2.WND_PROP_TOPMOST, 1)
            return True
        except ImportError:
            print("OpenCV未安装，无法使用OverlayInterface")
            return False

    def update(self, image, board_state, best_move, analysis_info):
        if not self.is_initialized or image is None:
            return False

        try:
            import cv2
            # 在图像上绘制推荐落子位置
            h, w = image.shape[:2]
            cell_w, cell_h = w // 15, h // 15
            row, col = best_move
            center_x = col * cell_w + cell_w // 2
            center_y = row * cell_h + cell_h // 2

            # 绘制标记
            cv2.circle(image, (center_x, center_y), 10, (0, 255, 0), -1)
            cv2.putText(image, f"Best: ({row},{col})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 显示图像
            cv2.imshow("Gobang Assistant", image)
            cv2.waitKey(1)  # 短暂等待，刷新窗口
            return True
        except Exception as e:
            print(f"叠加界面更新失败: {e}")
            return False

    def get_user_input(self):
        # 可以处理键盘输入
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return {"command": "quit"}
        return None

    def close(self):
        if self.is_initialized:
            import cv2
            cv2.destroyAllWindows()
        self.is_initialized = False