from abc import abstractmethod

from src.engine.board import ChessBoard


class AlgorithmEngine:
    """分析引擎抽象基类"""

    @abstractmethod
    def query(self, initial_board: ChessBoard, initial_player) -> (str, list, map):
        """获取算法引擎信息"""
        pass

    @abstractmethod
    def close(self):
        """关闭引擎"""
        pass
