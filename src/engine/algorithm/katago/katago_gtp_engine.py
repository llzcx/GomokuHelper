import logging
import subprocess
import threading
import time
from threading import Thread
from typing import Dict, Any

from src.engine.algorithm.algorithm import AlgorithmEngine
from src.engine.board import ChessBoard, BLACK, MoveItem
from src.engine.util import np_to_gtp, chess2color, parse_gtp_info, gtp_2_np, AnalyzedLRUCache


# ./engine/gom15x_trt.exe gtp -config ./engine.cfg -model ./weights/zhizi_renju28b_s1600.bin.gz -override-config
# basicRule=RENJU
class KataGoGTPEngine(AlgorithmEngine):

    def __init__(self, katago_path: str, config_path: str, model_path: str, additional_args=None, board_size=15, config: Dict[str, Any] = None):
        self.stdout_thread = None
        self.stderr_thread = None
        self.board_size = board_size
        self.visits_threshold = config.get("visits_threshold", 10000)
        self.cache = AnalyzedLRUCache(maxsize=1000)
        if additional_args is None:
            additional_args = []
        self.query_counter = 0
        katago = subprocess.Popen(
            [katago_path, "gtp", "-config", config_path, "-model", model_path, *additional_args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            universal_newlines=True,
            bufsize=1
        )
        self.cache_board = ChessBoard(size=self.board_size)
        self.katago = katago
        self.best_moves_shared = None
        self.res_lock = threading.Lock()
        self.running = True
        self.state_lock = threading.Lock()
        self.query_total = 0
        self.refresh_total = 0
        logging.info("KataGo GTP Engine is currently undergoing initialization...")
        time.sleep(20)
        self.async_handler()
        time.sleep(2)
        logging.info("KataGo GTP Engine Initialization successful!")

    def read_state(self):
        state = True
        with self.state_lock:
            state = self.running
        return state

    def set_state(self, state):
        with self.state_lock:
            self.running = state
        return state

    def close(self):
        self.set_state(False)
        self.katago.stdin.close()

    def query(self, initial_board: ChessBoard, initial_player='b'):
        logging.info(self.get_engine_info())
        # 获取棋盘尺寸
        board_size = initial_board.get_size()
        self.query_total += 1
        diff_list = []
        if initial_board.has_extra_pieces(self.cache_board):
            logging.info("=====The chessboard status is inconsistent and needs to be refreshed=====")
            self.cache_board.reset()
            logging.info(f"self.cache_board:\n{self.cache_board.render_numpy_board()}")
            logging.info(f"initial_board   :\n{initial_board.render_numpy_board()}")
            logging.info("=====The chessboard status is inconsistent and needs to be refreshed=====")
            diff_list = initial_board.diff(self.cache_board)
            self.reset()
            self.refresh_total += 1
        else:
            diff_list = initial_board.diff(self.cache_board)

        for diff_item in diff_list:
            chess, position = diff_item
            row_idx, col_idx = position
            self.cache_board.place_piece(row_idx, col_idx, chess)
            self.play(chess, row_idx, col_idx, board_size)

        if not self.cache_board.equals(initial_board):
            raise "System ERROR!!!"

        board_hash = self.cache_board.get_hash()
        val = self.cache.get(board_hash)
        if val is not None:
            current_play, best_move_list = val
            return current_play, best_move_list, {}

        current_play, best_move_list = self.kata_analyze(self.cache_board.determine_current_player(), 10)

        return current_play, best_move_list, {}

    def reset(self):
        self.exec_async("clear_board")

    def stop_kata_analyze(self):
        self.exec_async("stop")

    def play(self, chess, row, col, board_size):
        gtp = np_to_gtp(row, col, board_size)
        chess_color = chess2color(chess)
        self.exec_async(f"play {chess_color} {gtp}")

    def kata_analyze(self, next_step_chess, cal_time):
        chess_color = chess2color(next_step_chess)
        self.exec_async(f"kata-analyze {chess_color} {cal_time} pvVisits true")
        with self.res_lock:
            current = self.best_moves_shared
        return current

    def exec_async(self, query: str):
        logging.info(f"[EXEC Command] input: {query}")
        self.katago.stdin.write(query + "\n")
        self.katago.stdin.flush()

    def handler_stdout(self):
        while self.read_state():
            line = ""
            while self.read_state() and line == "":
                if self.katago.poll():
                    time.sleep(1)
                    raise Exception("Unexpected katago exit")
                line = self.katago.stdout.readline()
                line = line.strip()
            if len(line.strip()) == 0 or line.strip() == "=":
                continue
            if not line.startswith("info"):
                logging.error(f"Unexpected katago error: {line}")
                continue
            res_list = parse_gtp_info(line)
            best_move_list = []
            current_play = chess2color(self.cache_board.determine_current_player())
            for item in res_list[:7]:
                best_move = item.get('move')
                if best_move[0] == 'p':
                    continue
                row, col = gtp_2_np(best_move, self.cache_board.get_size())
                best_move_list.append(MoveItem(move=(row, col), gtp=best_move, visits=int(item.get('visits')),
                                               weight=item.get('weight'), winrate=float(item.get('winrate'))))
            if len(best_move_list) != 0 and int(best_move_list[0].visits) > self.visits_threshold:
                self.stop_kata_analyze()
                board_hash = self.cache_board.get_hash()
                self.cache[board_hash] = (current_play, best_move_list)

            with self.res_lock:
                self.best_moves_shared = (current_play, best_move_list)
        logging.info("handle stdout thread stop...")

    def handler_stderr(self):
        while self.read_state():
            line = ""
            while self.read_state() and line == "":
                if self.katago.poll():
                    time.sleep(1)
                    raise Exception("Unexpected katago exit")
                line = self.katago.stderr.readline()
                line = line.strip()
            logging.warn(f"[GTP Command ERROR] Wrong output: {line}")
        logging.info("handle stderr thread stop...")

    def async_handler(self):
        self.stdout_thread = Thread(target=self.handler_stdout)
        self.stdout_thread.start()
        self.stderr_thread = Thread(target=self.handler_stderr)
        self.stderr_thread.start()

    def get_engine_info(self):
        hit_rate = self.cache.get_hit_rate()

        if self.query_total == 0:
            refresh_rate = 0.0
        else:
            refresh_rate = self.refresh_total / self.query_total

        return (f"=============query cache hit rate: {hit_rate:.2f}%=============\n"
                f"=============query refresh count : {self.refresh_total}次=============\n"
                f"=============query refresh rate  : {refresh_rate:.2f}%=============")

