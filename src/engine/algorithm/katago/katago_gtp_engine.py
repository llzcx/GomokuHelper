import json
import subprocess
import threading
import time
from datetime import datetime
from threading import Thread
from typing import Tuple, List, Union, Literal, Any, Dict

import numpy as np
import sgfmill.ascii_boards
import sgfmill.boards

from src.engine.algorithm.algorithm import AlgorithmEngine
from src.engine.board import ChessBoard, BLACK, WHITE, MoveItem
from src.engine.util import np_to_gtp, chess2color, parse_gtp_info, gtp_2_np


# ./engine/gom15x_trt.exe gtp -config ./engine.cfg -model ./weights/zhizi_renju28b_s1600.bin.gz -override-config
# basicRule=RENJU
class KataGoGTPEngine(AlgorithmEngine):

    def __init__(self, katago_path: str, config_path: str, model_path: str, additional_args=None):
        self.stdout_thread = None
        self.stderr_thread = None
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
        self.cache_board = None
        self.katago = katago
        self.shared_str = ""
        self.res_lock = threading.Lock()
        self.running = True
        self.state_lock = threading.Lock()
        print("KataGo GTP Engine is currently undergoing initialization...")
        time.sleep(20)
        self.async_handler()
        time.sleep(2)
        print("KataGo GTP Engine Initialization successful!...")

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
        # 获取棋盘尺寸
        board_size = initial_board.get_size()

        diff_list = []
        if self.cache_board is None or initial_board.has_extra_pieces(self.cache_board):
            print("=====The chessboard status is inconsistent and needs to be refreshed=====")
            self.cache_board = ChessBoard(size=initial_board.size)
            print(f"self.cache_board:\n{self.cache_board.render_numpy_board()}")
            print(f"initial_board   :\n{initial_board.render_numpy_board()}")
            print("=====The chessboard status is inconsistent and needs to be refreshed=====")
            diff_list = initial_board.diff(self.cache_board)
            self.reset()
        else:
            diff_list = initial_board.diff(self.cache_board)

        for diff_item in diff_list:
            chess, position = diff_item
            row_idx, col_idx = position
            self.cache_board.place_piece(row_idx, col_idx, chess)
            self.play(chess, row_idx, col_idx, board_size)

        if not self.cache_board.equals(initial_board):
            raise "System ERROR!!!"

        res_list = self.kata_analyze(self.cache_board.determine_current_player(), 10)
        current_play = chess2color(self.cache_board.determine_current_player())
        best_move_list = []
        for item in res_list[:7]:
            best_move = item.get('move')
            if best_move[0] == 'p':
                continue
            row, col = gtp_2_np(best_move, board_size)
            best_move_list.append(MoveItem(move=(row, col), gtp=best_move, visits=int(item.get('visits')),
                                           weight=item.get('weight'), winrate=float(item.get('winrate'))))
        return current_play, best_move_list, res_list

    def reset(self):
        self.exec_async("clear_board")

    def play(self, chess, row, col, board_size):
        gtp = np_to_gtp(row, col, board_size)
        chess_color = chess2color(chess)
        self.exec_async(f"play {chess_color} {gtp}")

    def kata_analyze(self, next_step_chess, cal_time):
        chess_color = chess2color(next_step_chess)
        self.exec_async(f"kata-analyze {chess_color} {cal_time} pvVisits true")
        current = ""
        with self.res_lock:
            current = self.shared_str
        return parse_gtp_info(current)

    def exec_async(self, query: str):
        print(f"[EXEC Command] input: {query}")
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
            with self.res_lock:
                self.shared_str = line
        print("handler_stdout stop...")

    def handler_stderr(self):
        while self.read_state():
            line = ""
            while self.read_state() and line == "":
                if self.katago.poll():
                    time.sleep(1)
                    raise Exception("Unexpected katago exit")
                line = self.katago.stderr.readline()
                line = line.strip()
            print(f"[GTP Command ERROR] Wrong output: {line}")
        print("handler_stderr stop...")

    def async_handler(self):
        self.stdout_thread = Thread(target=self.handler_stdout)
        self.stdout_thread.start()
        self.stderr_thread = Thread(target=self.handler_stderr)
        self.stderr_thread.start()


if __name__ == "__main__":
    katago_path = "D:\project\model\KataGomo20250206\engine\gom15x_trt.exe"
    model_path = "D:\project\model\KataGomo20250206\weights\zhizi_renju28b_s1600.bin.gz"
    config_path = "gtp_engine.cfg"

    str1 = "basicRule=FREESTYLE"
    str2 = "basicRule=RENJU"
    str3 = "basicRule=STANDARD"

    katago = KataGoGTPEngine(katago_path, config_path, model_path,
                             additional_args=["-override-config", str2])
    board = ChessBoard(size=15)
    komi = 0
    moves = [("b", (3, 3))]
    board.place_piece(3, 3, BLACK)

    print("等待初始化...")
    time.sleep(20)
    katago.async_handler()
    print("初始化成功...")


    def print_func():
        while True:
            time.sleep(2)
            with katago.res_lock:
                print(katago.shared_str)


    get_value_thread = Thread(target=print_func)
    get_value_thread.start()
    while True:
        try:
            user_input = input("请输入内容（输入'exit'退出）：")
            if user_input.lower() == 'exit':
                print("程序即将退出...")
                katago.close()
                break

            katago.exec_async(user_input)
            print("------------------------")  # 分隔线

        except KeyboardInterrupt:
            # 处理Ctrl+C中断
            print("\n检测到中断信号，程序退出。")
            break
        except Exception as e:
            # 处理其他可能的异常
            print(f"发生错误：{e}")
            print("请重新输入...")
