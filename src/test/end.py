import logging
import time

from src.engine.analysis_engine import KatagoAnalysisEngine
from src.engine.board_recognizer import AdvancedBoardRecognizer
from src.engine.image_capture import ScreenCapture

# 配置日志格式：时间(yyyy-mm-dd hh:mm:ss) + 日志级别 + 消息
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%y%m%d %I:%M:%S'  # 匹配需求的时间格式
)

recognizer = AdvancedBoardRecognizer()
capture = ScreenCapture()
katago = KatagoAnalysisEngine()

if __name__ == '__main__':
    # 初始化组件并添加日志
    try:
        logging.info("程序启动，开始初始化组件...")
        recognizer.initialize()
        logging.info("棋盘识别器初始化完成")

        capture.initialize(config={
            "tool": "mss",
            "region": {"left": 625, "top": 69, "width": 1314, "height": 1314}
        })
        logging.info("屏幕捕获器初始化完成")

        katago.initialize(config={
            "katago_path": r"D:\project\model\KataGomo20250206\engine\gom15x_trt.exe",
            "model_path": r"D:\project\model\KataGomo20250206\weights\zhizi_renju28b_s1600.bin.gz",
            "config_path": r"D:\project\py\gomoku\src\engine\algorithm\katago\engine.cfg",  # 修复路径反斜杠转义
            "rule": "RENJU"
        })
        logging.info("KataGo引擎初始化完成")

        # 主循环
        logging.info("进入主循环...")
        while True:
            try:
                # 捕获屏幕帧
                image = capture.capture_frame()

                # 识别棋盘
                board, meta_info = recognizer.recognize(image)

                if board.is_effective_chessboard():
                    # 分析棋盘（复用已初始化的katago实例）
                    best, gtp, info = katago.analyze(board)

                    # 输出分析结果（使用info级别日志）
                    logging.info(f"最佳走法: {best}")
                    logging.info(f"GTP命令: {gtp}")
                    logging.info(f"分析详情: {info}")

                    time.sleep(10)
                else:
                    # 棋盘大小不符合时的日志
                    logging.warning(f"无法识别有效棋盘（当前尺寸: {board.get_size()}）")
                    time.sleep(2)

            except Exception as e:
                # 捕获循环内的异常，避免程序崩溃
                logging.error(f"循环执行出错: {str(e)}", exc_info=True)  # exc_info=True打印堆栈信息
                time.sleep(5)  # 出错后暂停一段时间再重试

    except KeyboardInterrupt:
        # 捕获Ctrl+C，优雅退出
        logging.info("用户中断程序，开始释放资源...")

    except Exception as e:
        # 捕获初始化阶段的致命错误
        logging.critical(f"组件初始化失败: {str(e)}", exc_info=True)

    finally:
        # 确保资源释放（无论程序正常退出还是异常退出）
        try:
            capture.release()
            logging.info("屏幕捕获器资源已释放")
        except:
            logging.warning("屏幕捕获器释放失败")

        try:
            katago.close()
            logging.info("KataGo引擎已关闭")
        except:
            logging.warning("KataGo引擎关闭失败")

        logging.info("程序已退出")
