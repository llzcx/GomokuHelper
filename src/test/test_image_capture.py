import unittest
from unittest.mock import patch, MagicMock, call
import numpy as np

from src.image_capture import ImageCapture, ScreenCapture


class TestImageCapture(unittest.TestCase):
    """测试 ImageCapture 抽象基类"""

    def test_abstract_methods(self):
        """测试抽象方法存在性"""
        # 尝试实例化抽象类应该会失败
        with self.assertRaises(TypeError):
            ImageCapture()

        # 检查所有抽象方法都存在
        self.assertTrue(hasattr(ImageCapture, 'initialize'))
        self.assertTrue(hasattr(ImageCapture, 'capture_frame'))
        self.assertTrue(hasattr(ImageCapture, 'get_capture_info'))
        self.assertTrue(hasattr(ImageCapture, 'release'))


class TestScreenCapture(unittest.TestCase):
    """测试 ScreenCapture 具体实现"""

    def setUp(self):
        """测试前设置"""
        self.screen_capture = ScreenCapture()

    def test_initial_state(self):
        """测试初始状态"""
        self.assertIsNone(self.screen_capture.monitor_region)
        self.assertIsNone(self.screen_capture.capture_tool)

    @patch('your_module.mss.mss')  # 替换为实际模块名
    def test_initialize_with_mss_success(self, mock_mss):
        """测试使用 mss 工具成功初始化"""
        # 准备模拟对象
        mock_mss_instance = MagicMock()
        mock_mss.return_value = mock_mss_instance

        # 执行初始化
        config = {"tool": "mss", "region": {"top": 0, "left": 0, "width": 800, "height": 600}}
        result = self.screen_capture.initialize(config)

        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.screen_capture.monitor_region, config["region"])
        self.assertEqual(self.screen_capture.capture_tool, mock_mss_instance)
        mock_mss.assert_called_once()

