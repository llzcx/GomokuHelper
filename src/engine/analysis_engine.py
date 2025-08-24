import time
from abc import abstractmethod
from typing import Optional, Dict, Any
from typing import Tuple, List

import numpy as np

from src.engine.algorithm.katago.katago import KataGo
from src.engine.board import ChessBoard, BLACK, MoveItem
from src.engine.util import gtp_2_np

class AnalysisEngine:
    """分析引擎抽象基类"""

    @abstractmethod
    def initialize(self, config: dict = None) -> bool:
        """初始化分析引擎"""
        pass

    @abstractmethod
    def analyze(self, board: np.ndarray, player: int = 1) -> Tuple[Optional[Tuple[int, int]], dict]:
        """
        分析棋盘并返回最佳落子位置

        参数:
            board: 15x15的棋盘状态
            player: 当前玩家 (1=黑, 2=白)

        返回:
            best_move: 最佳落子位置 (row, col)
            analysis_info: 分析信息，如评分、备选落子等
        """
        pass

    @abstractmethod
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        pass

    @abstractmethod
    def close(self):
        """关闭引擎"""
        pass


class AdvancedAnalysisEngine(AnalysisEngine):
    def __init__(self):
        self.initialized = False
        # 引擎配置参数
        self.config = {
            "search_depth": 5,  # 搜索深度，越大AI越强但速度越慢
            "max_considered_moves": 20,  # 每步考虑的最大候选落子数
            "win_score": 1000000,  # 获胜分数
            "eval_weights": {
                "five": 100000,  # 连五
                "four": 10000,  # 活四
                "three": 1000,  # 活三
                "two": 100,  # 活二
                "four_half": 5000,  # 冲四（半活四）
                "three_half": 500  # 眠三（半活三）
            }
        }
        self.info = {
            "name": "Alpha-Beta Gomoku Engine",
            "version": "1.0",
            "algorithm": "Minimax with Alpha-Beta Pruning",
            "features": ["pattern_recognition", "depth_search", "move_ordering"]
        }
        # 方向向量：上下、左右、两个对角线
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                           (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def initialize(self, config: dict = None) -> bool:
        """初始化分析引擎，可更新配置参数"""
        if config:
            self.config.update(config)
        self.initialized = True
        return True

    def analyze(self, board: np.ndarray, player: int = 1) -> Tuple[Optional[Tuple[int, int]], dict]:
        if not self.initialized:
            return None, {"error": "Engine not initialized", "score": 0}

        # 验证输入
        if board.shape != (15, 15):
            return None, {"error": "Board must be 15x15", "score": 0}
        if player not in (1, 2):
            return None, {"error": "Player must be 1 or 2", "score": 0}

        start_time = time.time()
        try:
            # 生成候选落子位置（优先考虑已有棋子附近）
            candidate_moves = self._generate_candidate_moves(board)

            if not candidate_moves:
                return None, {"error": "No valid moves", "score": 0}

            # 使用Alpha-Beta剪枝算法寻找最佳落子
            best_score = -float('inf')
            best_move = None
            alternative_moves = []

            # 对候选落子排序（提高剪枝效率）
            candidate_moves.sort(key=lambda move: self._evaluate_move(board, move, player), reverse=True)

            # 遍历候选落子
            for move in candidate_moves[:self.config["max_considered_moves"]]:
                row, col = move
                # 模拟落子
                board[row, col] = player
                # 评估对手的最佳应对
                score = -self._alpha_beta(board, self.config["search_depth"] - 1,
                                          -float('inf'), float('inf'), self._get_opponent(player))
                # 撤销落子
                board[row, col] = 0

                alternative_moves.append((move, score))

                # 更新最佳落子
                if score > best_score:
                    best_score = score
                    best_move = move

                # 如果找到必胜落子，提前结束搜索
                if best_score >= self.config["win_score"]:
                    break

            # 对备选落子排序
            alternative_moves.sort(key=lambda x: x[1], reverse=True)

            analysis_time = time.time() - start_time
            analysis_info = {
                "score": best_score,
                "analysis_time": round(analysis_time, 3),
                "search_depth": self.config["search_depth"],
                "considered_moves": len(candidate_moves),
                "alternative_moves": alternative_moves[:5],  # 返回前5个备选落子
                "is_winning_move": best_score >= self.config["win_score"]
            }

            return best_move, analysis_info

        except Exception as e:
            return None, {"error": str(e), "score": 0}

    def _alpha_beta(self, board: np.ndarray, depth: int, alpha: float, beta: float, player: int) -> float:
        """Alpha-Beta剪枝实现"""
        # 检查是否到达搜索深度或游戏结束
        if depth == 0:
            return self._evaluate_board(board, player)

        # 检查当前玩家是否已获胜
        if self._check_win(board, self._get_opponent(player)):
            return -self.config["win_score"] if depth % 2 == 0 else self.config["win_score"]

        # 生成候选落子
        candidate_moves = self._generate_candidate_moves(board)
        if not candidate_moves:
            return 0  # 平局

        # 排序候选落子以提高剪枝效率
        candidate_moves.sort(key=lambda move: self._evaluate_move(board, move, player), reverse=True)

        for move in candidate_moves[:self.config["max_considered_moves"]]:
            row, col = move
            # 模拟落子
            board[row, col] = player
            # 递归评估
            score = -self._alpha_beta(board, depth - 1, -beta, -alpha, self._get_opponent(player))
            # 撤销落子
            board[row, col] = 0

            if score >= beta:
                return beta  # beta剪枝
            if score > alpha:
                alpha = score  # 更新alpha

        return alpha

    def _evaluate_board(self, board: np.ndarray, player: int) -> int:
        """评估当前棋盘对玩家的有利程度"""
        if self._check_win(board, player):
            return self.config["win_score"]

        opponent = self._get_opponent(player)
        if self._check_win(board, opponent):
            return -self.config["win_score"]

        # 计算双方的棋型得分
        player_score = self._calculate_pattern_score(board, player)
        opponent_score = self._calculate_pattern_score(board, opponent)

        return player_score - opponent_score

    def _calculate_pattern_score(self, board: np.ndarray, player: int) -> int:
        """计算玩家在棋盘上的棋型得分"""
        score = 0
        for i in range(15):
            for j in range(15):
                if board[i, j] == player:
                    # 检查以(i,j)为中心的所有方向的棋型
                    for dir in self.directions[:4]:  # 每对方向只检查一次
                        pattern = self._get_pattern(board, i, j, dir, player)
                        score += self._pattern_to_score(pattern)
        return score

    def _get_pattern(self, board: np.ndarray, row: int, col: int, direction: Tuple[int, int], player: int) -> str:
        """获取指定方向上的棋型模式"""
        pattern = []
        # 向一个方向延伸
        for i in range(1, 5):
            r = row + direction[0] * i
            c = col + direction[1] * i
            if 0 <= r < 15 and 0 <= c < 15:
                pattern.append(str(board[r, c]))
            else:
                break

        # 加上当前位置
        pattern.append(str(player))

        # 向相反方向延伸
        for i in range(1, 5):
            r = row - direction[0] * i
            c = col - direction[1] * i
            if 0 <= r < 15 and 0 <= c < 15:
                pattern.append(str(board[r, c]))
            else:
                break

        return "".join(pattern)

    def _pattern_to_score(self, pattern: str) -> int:
        """将棋型模式转换为得分"""
        # 替换玩家标识为统一符号以便匹配（1->X, 2->O, 0->.）
        normalized = pattern.replace('1', 'X').replace('2', 'O').replace('0', '.')
        opp = 'O' if 'X' in normalized else 'X'  # 确定对手符号

        # 连五（直接获胜）
        if 'XXXXX' in normalized or 'OOOOO' in normalized:
            return self.config["eval_weights"]["five"]

        # 活四（两侧都有空位的四个连续子）
        if '.XXXX.' in normalized or '.OOOO.' in normalized:
            return self.config["eval_weights"]["four"]

        # 冲四（一侧被阻挡，另一侧有空位的四个连续子）
        if ('XXXX.' in normalized or '.XXXX' in normalized or
                'OOOO.' in normalized or '.OOOO' in normalized):
            # 排除被对手阻挡的情况
            if not (f'XXXX{opp}' in normalized or f'{opp}XXXX' in normalized or
                    f'OOOO{opp}' in normalized or f'{opp}OOOO' in normalized):
                return self.config["eval_weights"]["four_half"]

        # 活三（两侧都有空位的三个连续子）
        if '.XXX.' in normalized or '.OOO.' in normalized:
            return self.config["eval_weights"]["three"]

        # 眠三（一侧被阻挡，另一侧有空位的三个连续子）
        if ('XXX.' in normalized or '.XXX' in normalized or
                'OOO.' in normalized or '.OOO' in normalized):
            # 排除被对手阻挡的情况
            if not (f'XXX{opp}' in normalized or f'{opp}XXX' in normalized or
                    f'OOO{opp}' in normalized or f'{opp}OOO' in normalized):
                return self.config["eval_weights"]["three_half"]

        # 活二（两侧都有空位的两个连续子）
        if '.XX.' in normalized or '.OO.' in normalized:
            return self.config["eval_weights"]["two"]

        return 0

    def _evaluate_move(self, board: np.ndarray, move: Tuple[int, int], player: int) -> int:
        """快速评估单个落子的价值（用于排序候选落子）"""
        row, col = move
        # 模拟落子
        board[row, col] = player
        # 评估这个落子的价值
        score = self._calculate_pattern_score(board, player)
        # 撤销落子
        board[row, col] = 0
        return score

    def _generate_candidate_moves(self, board: np.ndarray) -> List[Tuple[int, int]]:
        """生成候选落子位置（优先考虑已有棋子附近）"""
        moves = []
        # 遍历棋盘寻找空位
        for i in range(15):
            for j in range(15):
                if board[i, j] == 0:
                    # 只考虑周围有棋子的空位（提高效率）
                    if self._has_adjacent_pieces(board, i, j):
                        moves.append((i, j))

        # 如果没有候选落子（空棋盘），返回中心位置
        if not moves:
            return [(7, 7)]  # 棋盘中心

        return moves

    def _has_adjacent_pieces(self, board: np.ndarray, row: int, col: int) -> bool:
        """检查指定位置周围是否有棋子（3x3范围内）"""
        for i in range(max(0, row - 2), min(15, row + 3)):
            for j in range(max(0, col - 2), min(15, col + 3)):
                if (i != row or j != col) and board[i, j] != 0:
                    return True
        return False

    def _check_win(self, board: np.ndarray, player: int) -> bool:
        """检查玩家是否获胜（是否有五连子）"""
        # 检查所有可能的五连子
        for i in range(15):
            for j in range(15):
                if board[i, j] == player:
                    # 检查所有方向
                    for dr, dc in self.directions:
                        # 检查当前方向上是否有连续5个相同的棋子
                        win = True
                        for k in range(1, 5):
                            ni, nj = i + dr * k, j + dc * k
                            if ni < 0 or ni >= 15 or nj < 0 or nj >= 15 or board[ni, nj] != player:
                                win = False
                                break
                        if win:
                            return True
        return False

    def _get_opponent(self, player: int) -> int:
        """获取对手玩家编号"""
        return 2 if player == 1 else 1

    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            **self.info,
            "current_config": self.config.copy()
        }


class KatagoAnalysisEngine:
    """
    basicRule=FREESTYLE,RENJU,STANDARD
    "initialStones": [
        ["B", "Q4"],
        ["B", "C4"]
    ],
15  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
14  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
13  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
12  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
11  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
10  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 9  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 8  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 7  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 6  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 5  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 4  .  .  .  #  .  .  .  .  .  .  .  .  .  .  .
 3  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 2  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
 1  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    A  B  C  D  E  F  G  H  J  K  L  M  N  O  P
    """

    def __init__(self):
        self.board = None
        self.instance = None

    def initialize(self, config: Dict[str, Any] = None) -> bool:
        # 使用配置参数或默认路径
        if config is None:
            config = {}

        katago_path = config.get('katago_path')
        model_path = config.get('model_path')
        config_path = config.get('config_path')
        rule = config.get('rule', 'RENJU')

        # 根据规则选择配置字符串
        rule_configs = {
            'FREESTYLE': "basicRule=FREESTYLE",
            'RENJU': "basicRule=RENJU",
            'STANDARD': "basicRule=STANDARD"
        }
        additional_args = ["-override-config", rule_configs.get(rule, "basicRule=RENJU")]

        # 初始化KataGo引擎
        try:
            katago = KataGo(
                katago_path_=katago_path,
                config_path_=config_path,
                model_path_=model_path,
                additional_args=additional_args
            )
            self.instance = katago
        except Exception as e:
            print(f"Failed to initialize KataGo: {e}")
            return False

        return True

    def analyze(self, board: ChessBoard) -> Tuple[str, List[MoveItem], Dict[str, Any]]:
        try:
            # 打印棋盘状态
            print(f"本次请求棋盘状态:\n{board.render_numpy_board()}")

            # 调用分析引擎
            analysis_result = self.instance.query(initial_board=board, initial_player= "b" if board.determine_current_player() == BLACK  else "w")

            # 检查是否有分析结果
            if "error" in analysis_result:
                print(analysis_result["error"])
                return "",[], analysis_result

            # 获取最佳着法
            current_player = analysis_result["rootInfo"].get('currentPlayer')
            best_move_list = []
            for moveInfo in analysis_result["moveInfos"][:7]:
                best_move = moveInfo.get('move')
                row, col = gtp_2_np(best_move, board.get_size())
                best_move_list.append(MoveItem(move=(row, col), gtp=best_move, visits=moveInfo.get('visits'),
                             weight=moveInfo.get('weight'), winrate=moveInfo.get('winrate')))
            return current_player, best_move_list, analysis_result

        except Exception as e:
            print(f"Analysis failed: {e}")
            return "", [], {}

    def get_engine_info(self) -> Dict[str, Any]:
        # 返回引擎信息
        return {
            'name': 'KataGo',
            'version': '1.0',
            'supported_rules': ['FREESTYLE', 'RENJU', 'STANDARD']
        }

    def close(self):
        # 关闭KataGo引擎
        if self.instance:
            self.instance.close()

