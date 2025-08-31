import cv2

from src.engine.util import crop_ndarray, save_ndarray, to_ndarray

source_img = "../../img/source.png"
target_img = "../../img/target.png"

"""Adjust the parameters below to determine the position and size of the entire chessboard. It is worth noting that 
the leftmost line in the image should be tangent to the circle where the leftmost chess piece is located, 
including the top, bottom, and right sides."""
left = 625
top = 69
width = 1314
height = 1314


def test_screen_capture():
    frame = to_ndarray(source_img)
    frame = crop_ndarray(frame, left, top, width, height)
    save_ndarray(frame, folder_path="../../img", filename="target.png")
    if frame is not None:
        print(f"image shape: {frame.shape}")

        if len(frame.shape) == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        cv2.imshow('Screen Capture', frame)
        print("Press any key to close the window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_screen_capture()
