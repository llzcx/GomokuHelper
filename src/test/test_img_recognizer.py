from src.engine.board_recognizer import  AdvancedBoardRecognizer
from src.engine.util import to_ndarray


target_img = "../../img/target.png"
"""
This test file can be used to adjust the following parameters and observe whether the output meets expectations
"""
grid_size = 15
cell_size = 89
piece_size = 69
image_size = 1314
black_threshold = 0.2
white_threshold = 0.7

if __name__ == '__main__':
    recognizer = AdvancedBoardRecognizer()
    if recognizer.initialize(config={
            "grid_size": grid_size,
            "cell_size": cell_size,
            "piece_size": piece_size,
            "image_size": image_size,
            "black_threshold": black_threshold,
            "white_threshold": white_threshold,
        }):
        image = to_ndarray("../../img/target.png")
        board_state, meta_info = recognizer.recognize(image)
        if board_state is not None:
            print("Chessboard recognition results：")
            print(board_state.render_numpy_board())
            print("\nmetadata：")
            for key, value in meta_info.items():
                print(f"{key}: {value}")
        else:
            print("Chessboard recognition failed, metadata:")
            for key, value in meta_info.items():
                print(f"{key}: {value}")
        print("\nRecognizer information:")
        info = recognizer.get_recognizer_info()
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("Collector initialization failed")