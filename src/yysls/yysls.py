from src.engine.image_capture import ScreenCapture

if __name__ == '__main__':
    capture = ScreenCapture()
    config = {
        "tool": "mss",
        "region": {"top": 0, "left": 0, "width": 2560, "height": 1440}
    }
    capture.initialize(config)
