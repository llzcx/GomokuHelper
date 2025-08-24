import logging
import threading
import time

from src.engine.analysis_engine import KatagoAnalysisEngine
from src.engine.board_recognizer import AdvancedBoardRecognizer
from src.engine.image_capture import ScreenCapture
from src.engine.user_report import QTReport

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%y%m%d %I:%M:%S'
)
grid_size = 15  # 15x15棋盘
cell_size = 89  # 每个格子的尺寸
piece_size = 69  # 棋子尺寸
image_size = 1314  # 图片尺寸
left = 625  # 棋盘距离左边距离
top = 69  # 棋盘距离顶部距离
katago_path = r"D:\project\model\KataGomo20250206\engine\gom15x_trt.exe"
model_path = r"D:\project\model\KataGomo20250206\weights\zhizi_renju28b_s1600.bin.gz"
config_path = r"D:\project\py\gomoku\src\engine\algorithm\katago\engine.cfg"
#rule = "FREESTYLE"
rule = "RENJU"
recognizer = AdvancedBoardRecognizer()
capture = ScreenCapture()
katago = KatagoAnalysisEngine()
report = QTReport()

def update_task():
    # 初始化组件并添加日志
    try:
        logging.info("程序启动，开始初始化组件...")
        recognizer.initialize(config={
            "grid_size": grid_size,
            "cell_size": cell_size,
            "piece_size": piece_size,
            "image_size": image_size,
            "black_threshold": 0.2,  # 黑色阈值
            "white_threshold": 0.7  # 白色阈值
        })
        logging.info("棋盘识别器初始化完成")

        capture.initialize(config={
            "tool": "mss",
            "region": {"left": left, "top": top, "width": image_size, "height": image_size}
        })
        logging.info("屏幕捕获器初始化完成")

        katago.initialize(config={
            "katago_path": katago_path,
            "model_path": model_path,
            "config_path": config_path,
            "rule": rule
        })
        logging.info("KataGo引擎初始化完成")
        logging.info("进入主循环...")
        while True:
            try:
                image = capture.capture_frame()
                board, meta_info = recognizer.recognize(image)
                if board.is_effective_chessboard():
                    player ,moves, info = katago.analyze(board)
                    player2ch = "黑方" if player == "B" else "白方"
                    logging.info(f"当前执棋: {player2ch}")
                    logging.info(f"最佳走法: {moves}")
                    logging.info(f"分析详情: {info}")
                    report.update(image, board, moves, info)
                    time.sleep(2)
                else:
                    time.sleep(2)

            except Exception as e:
                logging.error(f"循环执行出错: {str(e)}", exc_info=True)  # exc_info=True打印堆栈信息
                time.sleep(5)  # 出错后暂停一段时间再重试

    except KeyboardInterrupt:
        logging.info("用户中断程序，开始释放资源...")

    except Exception as e:
        logging.critical(f"组件初始化失败: {str(e)}", exc_info=True)

    finally:
        capture.release()
        katago.close()
        report.close()
        logging.info("程序已退出")


if __name__ == '__main__':
    try:
        report.initialize(config={
            "top": top,
            "left": left,
            "grid_size": grid_size,
            "cell_size": cell_size,
            "piece_size": piece_size,
            "image_size": image_size,
        })
        my_thread = threading.Thread(target=update_task)
        my_thread.start()
        report.event_loop()
    finally:
        report.close()
