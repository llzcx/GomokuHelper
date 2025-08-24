from dataclasses import dataclass

import numpy as np
from typing import Optional, Tuple, List

BLACK = 1
WHITE = 2


class ChessBoard:
    def __init__(self, size: int = 15, board: np.array = None):
        self.size = size
        if board is not None:
            self.board = board
        else:
            self.board = np.zeros((size, size), dtype=int)

    def reset(self) -> None:
        self.board = np.zeros((self.size, self.size), dtype=int)

    def place_piece(self, row: int, col: int, chess: int) -> bool:
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False

        if self.board[row, col] != 0:
            return False

        self.board[row, col] = chess
        return True

    def remove_piece(self, row: int, col: int) -> bool:
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False

        if self.board[row, col] == 0:
            return False

        self.board[row, col] = 0
        return True

    def get_piece(self, row: int, col: int) -> int:
        if not (0 <= row < self.size and 0 <= col < self.size):
            return -1  # 无效位置

        return self.board[row, col]

    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def is_empty(self, row: int, col: int) -> bool:
        if not self.is_valid_position(row, col):
            return False

        return self.board[row, col] == 0

    def get_board(self) -> np.ndarray:
        return self.board.copy()

    def set_board(self, new_board: np.ndarray) -> bool:
        if new_board.shape != (self.size, self.size):
            return False

        self.board = new_board.copy()
        return True

    def count_pieces(self, chess: Optional[int] = None) -> int:
        if chess is None:
            return np.count_nonzero(self.board)
        else:
            return np.count_nonzero(self.board == chess)

    def is_effective_chessboard(self) -> bool:
        return abs(np.count_nonzero(self.board == WHITE) - np.count_nonzero(self.board == BLACK)) <= 1

    def find_pieces(self, player: int) -> List[Tuple[int, int]]:
        positions = []
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i, j] == player:
                    positions.append((i, j))
        return positions

    def save_to_file(self, filename: str) -> None:
        np.save(filename, self.board)

    def load_from_file(self, filename: str) -> bool:
        try:
            loaded_board = np.load(filename)
            if loaded_board.shape == (self.size, self.size):
                self.board = loaded_board
                return True
            else:
                print(f"棋盘大小不匹配。期望: {self.size}x{self.size}，实际: {loaded_board.shape}")
                return False
        except FileNotFoundError:
            print(f"文件未找到: {filename}")
            return False
        except Exception as e:
            print(f"加载棋盘时出错: {e}")
            return False

    def determine_current_player(self) -> int:
        board_state = self.board
        if board_state.shape != (15, 15):
            raise ValueError("棋盘必须是15x15的numpy数组")

        black_count = np.sum(board_state == BLACK)
        white_count = np.sum(board_state == WHITE)

        if white_count > black_count:
            raise ValueError(f"无效的棋盘状态：白棋({white_count})比黑棋({black_count})多")
        if black_count - white_count > 1:
            raise ValueError(f"无效的棋盘状态：黑棋({black_count})比白棋({white_count})多超过1个")

        if black_count == white_count:
            return BLACK
        else:
            return WHITE

    def render_numpy_board(self):
        """生成棋盘字符串：列标题 + 倒序行号（15到1） + 保持数组原始顺序的内容"""
        # 用于存储整个棋盘的字符串
        board_str = []

        # 1. 生成列标题（A B C ... P）
        col_titles = []
        for i in range(15):  # 仅生成15列
            if i < 8:
                col_titles.append(chr(ord('A') + i))  # A-H
            else:
                col_titles.append(chr(ord('A') + i + 1))  # 跳过I，直接从J开始（J-P）

        # 添加列标题行
        board_str.append(f"    {' '.join(col_titles)}")

        # 2. 按15到1的顺序生成行号，但使用原始数组顺序
        for display_row_num in range(self.size, 0, -1):
            # 计算显示行号对应的数组索引
            # 显示行15 → 索引0，显示行1 → 索引14
            array_index = self.size - display_row_num

            # 行号对齐：占2位
            formatted_row_num = f"{display_row_num:2d}"

            # 转换当前行的numpy数据为字符（0→.，1→X，2→O）
            row_chars = []
            for val in self.board[array_index]:
                if val == 1:
                    row_chars.append('X')
                elif val == 2:
                    row_chars.append('O')
                else:
                    row_chars.append('.')

            # 将当前行添加到字符串列表
            board_str.append(f"{formatted_row_num}  {' '.join(row_chars)}")

        # 拼接所有行，用换行符分隔
        return '\n'.join(board_str)

    def get_size(self) -> int:
        return self.board.shape[0]

@dataclass
class MoveItem:
    move: Tuple[int, int]
    gtp: str
    visits: int
    weight: int
    winrate: float

    def __str__(self):
        return f"Move{self.move}({self.gtp}): v{self.visits} w{self.weight} {self.winrate:.1%}"