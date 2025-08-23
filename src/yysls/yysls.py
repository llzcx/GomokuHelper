import cv2
import numpy as np

from src.engine.image_capture import ScreenCapture
from PIL import Image
from typing import Tuple, Optional


if __name__ == '__main__':
    capture = ScreenCapture()
    config = {
        "tool": "mss",
        "region": {"top": 0, "left": 0, "width": 2560, "height": 1440}
    }
    capture.initialize(config)
