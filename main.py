from src.analysis_engine import RuleBasedEngine, SearchBasedEngine
from src.board_recognizer import TraditionalRecognizer, YOLORecognizer
from src.image_capture import ScreenCapture
from src.user_report import ConsoleReport, OverlayReport


class GobangAssistant:
    """五子棋辅助系统控制器"""

    def __init__(self):
        self.image_capture = None
        self.board_recognizer = None
        self.analysis_engine = None
        self.user_interface = None
        self.is_running = False
        self.config = {
            "capture": {"type": "screen", "region": {"top": 0, "left": 0, "width": 800, "height": 600}},
            "recognizer": {"type": "traditional"},
            "engine": {"type": "rule_based"},
            "ui": {"type": "console"},
            "player": 1  # 默认玩家为黑方
        }

    def initialize(self, config: dict = None) -> bool:
        """初始化系统"""
        if config:
            self.config.update(config)

        # 初始化图像采集模块
        capture_type = self.config["capture"].get("type", "screen")
        if capture_type == "screen":
            self.image_capture = ScreenCapture()
        # 可以添加其他采集器类型

        if not self.image_capture.initialize(self.config["capture"]):
            print("图像采集模块初始化失败")
            return False

        # 初始化棋盘识别模块
        recognizer_type = self.config["recognizer"].get("type", "traditional")
        if recognizer_type == "traditional":
            self.board_recognizer = TraditionalRecognizer()
        elif recognizer_type == "yolo":
            self.board_recognizer = YOLORecognizer()
        # 可以添加其他识别器类型

        if not self.board_recognizer.initialize(config=self.config["recognizer"]):
            print("棋盘识别模块初始化失败")
            return False

        # 初始化分析引擎模块
        engine_type = self.config["engine"].get("type", "rule_based")
        if engine_type == "rule_based":
            self.analysis_engine = RuleBasedEngine()
        elif engine_type == "search_based":
            self.analysis_engine = SearchBasedEngine()
        # 可以添加其他引擎类型

        if not self.analysis_engine.initialize(config=self.config["engine"]):
            print("分析引擎模块初始化失败")
            return False

        # 初始化用户界面模块
        ui_type = self.config["ui"].get("type", "console")
        if ui_type == "console":
            self.user_interface = ConsoleReport()
        elif ui_type == "overlay":
            self.user_interface = OverlayReport()
        # 可以添加其他界面类型

        if not self.user_interface.initialize(config=self.config["ui"]):
            print("用户界面模块初始化失败")
            return False

        self.is_running = True
        return True

    def run(self):
        """运行主循环"""
        if not self.is_running:
            print("系统未初始化")
            return

        print("五子棋辅助系统开始运行")

        try:
            while self.is_running:
                # 1. 采集图像
                image = self.image_capture.capture_frame()
                if image is None:
                    continue

                # 2. 识别棋盘
                board_state, recognizer_info = self.board_recognizer.recognize(image)
                if board_state is None:
                    print(f"棋盘识别失败: {recognizer_info.get('error', '未知错误')}")
                    continue

                # 3. 分析棋盘
                best_move, analysis_info = self.analysis_engine.analyze(
                    board_state, self.config["player"])
                if best_move is None:
                    print(f"分析失败: {analysis_info.get('error', '未知错误')}")
                    continue

                # 4. 更新界面
                self.user_interface.update(image, board_state, best_move, analysis_info)

                # 5. 处理用户输入
                user_input = self.user_interface.get_user_input()
                if user_input and user_input.get("command") == "quit":
                    break

        except KeyboardInterrupt:
            print("用户中断程序")
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭系统"""
        print("正在关闭系统...")
        if self.image_capture:
            self.image_capture.release()
        if self.user_interface:
            self.user_interface.close()
        self.is_running = False
        print("系统已关闭")


# 使用示例
if __name__ == "__main__":
    assistant = GobangAssistant()

    # 配置系统
    config = {
        "capture": {
            "type": "screen",
            "region": {"top": 300, "left": 700, "width": 500, "height": 500},
            "tool": "mss"
        },
        "recognizer": {
            "type": "traditional"
        },
        "engine": {
            "type": "rule_based"
        },
        "ui": {
            "type": "overlay"
        },
        "player": 1
    }

    if assistant.initialize(config):
        assistant.run()