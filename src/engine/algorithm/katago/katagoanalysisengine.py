import json
import subprocess
import time
from datetime import datetime
from threading import Thread
from typing import Tuple, List, Union, Literal, Any, Dict

import numpy as np
import sgfmill.ascii_boards
import sgfmill.boards

from src.engine.board import ChessBoard, BLACK, WHITE

Color = Union[Literal["b"], Literal["w"]]
Move = Union[None, Literal["pass"], Tuple[int, int]]


def sgfmill_to_str(move_: Move) -> str:
    if move_ is None:
        return "pass"
    if move_ == "pass":
        return "pass"
    (y, x) = move_
    return "ABCDEFGHJKLMNOPQRSTUVWXYZ"[x] + str(y + 1)


class KataGoAnalysisEngine:

    def __init__(self, katago_path_: str, config_path_: str, model_path_: str, additional_args=None):
        if additional_args is None:
            additional_args = []
        self.query_counter = 0
        katago_ = subprocess.Popen(
            [katago_path_, "analysis", "-config", config_path_, "-model", model_path_, *additional_args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.katago = katago_

        def print_forever():
            while katago_.poll() is None:
                data = katago_.stderr.readline()
                time.sleep(0)
                if data:
                    print("KataGo: ", data.decode(), end="")
            data = katago_.stderr.read()
            if data:
                print("KataGo: ", data.decode(), end="")

        self.stderrthread = Thread(target=print_forever)
        self.stderrthread.start()

    def close(self):
        self.katago.stdin.close()

    def query(self, initial_board: ChessBoard, max_visits=None, initial_player="b"):

        query = {"id": str(self.query_counter)}
        self.query_counter += 1

        # 获取棋盘尺寸
        board_size = initial_board.get_size()

        query["initialStones"] = []
        for y in range(board_size):
            for x in range(board_size):
                color_code = initial_board.get_piece(y, x)
                if color_code == BLACK:
                    color_str = "B"
                elif color_code == WHITE:
                    color_str = "W"
                else:
                    continue

                # 将数字坐标转换为字母坐标
                letter = chr(ord('A') + x)
                if letter >= 'I':  # 跳过I
                    letter = chr(ord(letter) + 1)
                number = board_size - y
                coord = f"{letter}{number}"

                query["initialStones"].append([color_str, coord])

        query["moves"] = []
        query["rules"] = "Chinese"
        query["komi"] = 0
        query["boardXSize"] = board_size
        query["boardYSize"] = board_size
        query["includePolicy"] = True
        query["initialPlayer"] = initial_player
        if max_visits is not None:
            query["maxVisits"] = max_visits

        return self.query_raw(query)

    def query_raw(self, query: Dict[str, Any]):
        self.katago.stdin.write((json.dumps(query) + "\n").encode())
        self.katago.stdin.flush()
        line = ""
        while line == "":
            if self.katago.poll():
                time.sleep(1)
                raise Exception("Unexpected katago exit")
            line = self.katago.stdout.readline()
            line = line.decode().strip()
        print(f"query_raw json line:\n {line}")
        response = json.loads(line)
        return response


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def object_to_json_with_encoder(obj, indent=None):
    return json.dumps(obj, cls=CustomEncoder, indent=indent, ensure_ascii=False)


if __name__ == "__main__":

    katago_path = "D:\project\model\KataGomo20250206\engine\gom15x_trt.exe"
    model_path = "D:\project\model\KataGomo20250206\weights\zhizi_renju28b_s1600.bin.gz"
    config_path = "engine.cfg"

    str1 = "basicRule=FREESTYLE"
    str2 = "basicRule=RENJU"
    str3 = "basicRule=STANDARD"

    katago = KataGoAnalysisEngine(katago_path, config_path, model_path,
                                  additional_args=["-override-config", str2])

    board = sgfmill.boards.Board(15)
    komi = 0
    moves = [("b", (3, 3))]

    display_board = board.copy()
    for color, move in moves:
        if move != "pass":
            row, col = move
            display_board.play(row, col, color)
    print(sgfmill.ascii_boards.render_board(display_board))

    print("Query result: ")
    print(object_to_json_with_encoder(katago.query(board, moves, komi)))

    katago.close()
