from src.engine.board_recognizer import  AdvancedBoardRecognizer
from src.engine.util import print_board, to_ndarray

if __name__ == '__main__':
    recognizer = AdvancedBoardRecognizer()
    # 初始化识别器
    if recognizer.initialize():
        # 模拟一张图像（这里用None代替，实际应传入np.ndarray类型的图像）
        image = to_ndarray("D:\project\py\gomoku\img\p5.png")
        board_state, meta_info = recognizer.recognize(image)
        if board_state is not None:
            print("棋盘识别结果：")
            print_board(board_state)
            print("\n元信息：")
            for key, value in meta_info.items():
                print(f"{key}: {value}")
        else:
            print("棋盘识别失败，元信息：")
            for key, value in meta_info.items():
                print(f"{key}: {value}")
        print("\n识别器信息：")
        info = recognizer.get_recognizer_info()
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("采集器初始化失败")