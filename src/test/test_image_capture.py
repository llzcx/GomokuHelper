import cv2
from src.engine.image_capture import ScreenCapture
from src.engine.util import crop_ndarray, save_ndarray, to_ndarray, print_board


def test_screen_capture():
    # 创建屏幕采集器
    capture = ScreenCapture()

    # 初始化配置
    config = {
        "tool": "mss",  # 或 "pyautogui"
        "region": {"left": 625, "top": 69, "width": 1314, "height": 1318}
    }

    if capture.initialize(config):
        print("采集器初始化成功")
        print("采集器信息:", capture.get_capture_info())

        # 捕获一帧图像
        #frame = capture.capture_frame()
        frame = to_ndarray("D:\project\py\gomoku\img\p4.png")
        frame = crop_ndarray(frame, 625, 69, 1314, 1314)
        save_ndarray(frame, folder_path="D:\project\py\gomoku\img", filename="p5.png")
        if frame is not None:
            print(f"捕获图像形状: {frame.shape}")

            # 注意：mss 返回的是 BGRA 格式，pyautogui 返回的是 RGB 格式
            # 转换为 BGR 格式（OpenCV 标准格式）
            if len(frame.shape) == 3 and frame.shape[2] == 4:  # BGRA
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif len(frame.shape) == 3 and frame.shape[2] == 3:  # RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 显示图像
            cv2.imshow('Screen Capture', frame)
            print("按任意键关闭窗口...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("截图失败")
    # 释放资源
    capture.release()


if __name__ == "__main__":
    test_screen_capture()
