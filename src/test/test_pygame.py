import os
import pygame
import ctypes

# 设置窗口位置 (例如：屏幕左上角位置为 (100, 100))
os.environ['SDL_VIDEO_WINDOW_POS'] = "100,100"

# 初始化 Pygame
pygame.init()

# 创建窗口 (宽 800，高 600)
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pygame 窗口指定位置显示")

# 确保窗口置顶（可选）
hwnd = pygame.display.get_wm_info()['window']
ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001)

# 主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 填充背景颜色
    screen.fill((0, 128, 255))

    # 更新显示
    pygame.display.flip()

# 退出 Pygame
pygame.quit()
