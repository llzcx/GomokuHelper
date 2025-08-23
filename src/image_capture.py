from abc import ABC, abstractmethod
from typing import Optional, Any
import numpy as np


class ImageCapture(ABC):
    """图像采集抽象基类"""

    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """初始化采集器"""
        pass

    @abstractmethod
    def capture_frame(self) -> Optional[np.ndarray]:
        """捕获一帧图像"""
        pass

    @abstractmethod
    def get_capture_info(self) -> dict:
        """获取采集器信息"""
        pass

    @abstractmethod
    def release(self):
        """释放资源"""
        pass


# 具体实现示例：屏幕截图采集器
class ScreenCapture(ImageCapture):
    def __init__(self):
        self.monitor_region = None
        self.capture_tool = None

    def initialize(self, config: dict) -> bool:
        try:
            # 根据配置选择不同的截图库
            if config.get("tool", "mss") == "mss":
                import mss
                self.capture_tool = mss.mss()
            else:
                import pyautogui
                self.capture_tool = pyautogui

            self.monitor_region = config.get("region", {"top": 0, "left": 0, "width": 800, "height": 600})
            return True
        except Exception as e:
            print(f"ScreenCapture初始化失败: {e}")
            return False

    def capture_frame(self) -> Optional[np.ndarray]:
        try:
            if hasattr(self.capture_tool, "grab"):
                # 使用mss
                screenshot = self.capture_tool.grab(self.monitor_region)
                return np.array(screenshot)
            else:
                # 使用pyautogui
                screenshot = self.capture_tool.screenshot(region=(
                    self.monitor_region["left"],
                    self.monitor_region["top"],
                    self.monitor_region["width"],
                    self.monitor_region["height"]
                ))
                return np.array(screenshot)
        except Exception as e:
            print(f"截图失败: {e}")
            return None

    def get_capture_info(self) -> dict:
        return {
            "type": "screen_capture",
            "region": self.monitor_region,
            "tool": "mss" if hasattr(self.capture_tool, "grab") else "pyautogui"
        }

    def release(self):
        if hasattr(self.capture_tool, "close"):
            self.capture_tool.close()
