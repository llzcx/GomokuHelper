import numpy as np

from src.engine.analysis_engine import KatagoEngine
from src.engine.board import ChessBoard, WHITE, BLACK

if __name__ == '__main__':
    katago = KatagoEngine()
    katago.initialize(config={
        "katago_path": r"D:\project\model\KataGomo20250206\engine\gom15x_trt.exe",
        "model_path": r"D:\project\model\KataGomo20250206\weights\zhizi_renju28b_s1600.bin.gz",
        "config_path": "D:\project\py\gomoku\src\engine\\algorithm\katago\engine.cfg",
        "rule": "RENJU"
    })

    board = ChessBoard(size=15)
    board.place_piece(7, 7, WHITE)
    board.place_piece(7, 8, BLACK)

    best, gtp, info = katago.analyze(board)
    print(best)
    print(gtp)
    print(info)
    katago.close()
