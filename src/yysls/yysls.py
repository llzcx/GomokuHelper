import logging
import threading
import time

from src.engine.analysis_engine import KatagoEngine
from src.engine.board import ChessBoard
from src.engine.board_recognizer import AdvancedBoardRecognizer
from src.engine.image_capture import ScreenCapture
from src.engine.user_report import QTReport

grid_size = 15  # 15x15 Chessboard
cell_size = 89  # The size of each grid
piece_size = 69  # Chess size
image_size = 1314  # image size
left = 625  # Distance to the left of the chessboard
top = 69  # Distance from the top of the chessboard
katago_path = r"D:\project\model\KataGomo20250206\engine\gom15x_trt.exe"
model_path = r"D:\project\model\KataGomo20250206\weights\zhizi_renju28b_s1600.bin.gz"
config_path = r"..\engine\algorithm\katago\gtp_engine.cfg"
rule = "FREESTYLE"
#rule = "RENJU"
visits_threshold = 2000
chess_manual_size = 5000
#chess_manual_path = r"..\engine\algorithm\katago\chess_manual_dict_for_renju.pkl"
chess_manual_path = r"..\engine\algorithm\katago\chess_manual_dict_for_freestyle.pkl"
black_threshold = 0.2
white_threshold = 0.7

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%y%m%d %I:%M:%S'
)
recognizer = AdvancedBoardRecognizer()
capture = ScreenCapture()
katago = KatagoEngine()
report = QTReport()


def update_task():
    try:
        logging.info(f"Program startup, current mode is: {rule}，Start initializing components...")
        recognizer.initialize(config={
            "grid_size": grid_size,
            "cell_size": cell_size,
            "piece_size": piece_size,
            "image_size": image_size,
            "black_threshold": black_threshold,
            "white_threshold": white_threshold,
        })
        logging.info("Chessboard recognizer initialization completed!")

        capture.initialize(config={
            "tool": "mss",
            "region": {"left": left, "top": top, "width": image_size, "height": image_size}
        })
        logging.info("Screen capture initialization completed!")

        katago.initialize(config={
            "katago_path": katago_path,
            "model_path": model_path,
            "config_path": config_path,
            "rule": rule,
            "board_size": grid_size,
            "visits_threshold": visits_threshold,
            "chess_manual_size": chess_manual_size,
            "chess_manual_path": chess_manual_path,

        })
        logging.info("KataGo engine initialization completed")
        logging.info("Enter the main loop...")
        while True:
            try:
                image = capture.capture_frame()
                board, meta_info = recognizer.recognize(image)
                if board.is_effective_chessboard() and board.is_game_over() == 0:
                    player, moves, info = katago.analyze(board)
                    player2ch = "黑方" if player == "B" else "白方" if player == "W" else "PASS"
                    logging.info(f"============Current Chess Execution: {player2ch}============")
                    if player2ch != "PASS":
                        logging.info(f"Best way to go: {moves}")
                        report.update(image, board, moves, info)
                    time.sleep(2)
                else:
                    report.update(image, ChessBoard(size=15), [], {})
                    time.sleep(2)

            except Exception as e:
                logging.error(f"Loop execution error: {str(e)}", exc_info=True)
                time.sleep(5)

    except KeyboardInterrupt:
        logging.info("The user interrupts the program and starts releasing resources...")

    except Exception as e:
        logging.critical(f"Component initialization failed: {str(e)}", exc_info=True)

    finally:
        capture.release()
        katago.close()
        report.close()
        logging.info("The program has exited")


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
