import json
import subprocess
import time
from datetime import datetime
from threading import Thread
from typing import Tuple, List, Union, Literal, Any, Dict

import numpy as np
import sgfmill.ascii_boards
import sgfmill.boards

from src.engine.algorithm.algorithm import AlgorithmEngine
from src.engine.board import ChessBoard, BLACK, WHITE, MoveItem
from src.engine.util import object_to_json_with_encoder, gtp_2_np

Color = Union[Literal["b"], Literal["w"]]
Move = Union[None, Literal["pass"], Tuple[int, int]]


def sgfmill_to_str(move_: Move) -> str:
    if move_ is None:
        return "pass"
    if move_ == "pass":
        return "pass"
    (y, x) = move_
    return "ABCDEFGHJKLMNOPQRSTUVWXYZ"[x] + str(y + 1)


class KataGoAnalysisEngine(AlgorithmEngine):

    def __init__(self, katago_path: str, config_path: str, model_path: str, additional_args=None, board_size=15):
        if additional_args is None:
            additional_args = []
        self.query_counter = 0
        katago_ = subprocess.Popen(
            [katago_path, "analysis", "-config", config_path, "-model", model_path, *additional_args],
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

        analysis_result = self.query_raw(query)

        # 检查是否有分析结果
        if "error" in analysis_result:
            print(analysis_result["error"])
            return "", [], analysis_result

        # 获取最佳着法
        current_player = analysis_result["rootInfo"].get('currentPlayer')
        best_move_list = []
        for moveInfo in analysis_result["moveInfos"][:7]:
            best_move = moveInfo.get('move')
            row, col = gtp_2_np(best_move, board_size)
            best_move_list.append(MoveItem(move=(row, col), gtp=best_move, visits=moveInfo.get('visits'),
                                           weight=moveInfo.get('weight'), winrate=moveInfo.get('winrate')))
        return current_player, best_move_list, analysis_result[:7]

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