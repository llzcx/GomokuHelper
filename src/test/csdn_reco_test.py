# 导入相关库
import cv2
import numpy as np

# 读取图像
img = cv2.imread('D:\project\py\gomoku\img\p2.png')
cv2.imshow('img', img)

# 转换为灰度图像
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# print('gray:', gray.shape)
# cv2.imshow('gray', gray)

# 高斯模糊
blur = cv2.GaussianBlur(gray, (5, 5), 0)
# cv2.imshow('blur', blur)

# 边缘检测
edges = cv2.Canny(blur, 50, 150)
# cv2.imshow('edges', edges)

# 轮廓提取
contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 找到最大的轮廓，即棋盘的轮廓
max_area = 0
max_contour = None
for contour in contours:
    area = cv2.contourArea(contour)
    if area > max_area:
        max_area = area
        max_contour = contour

# 找到最小外接矩形，即棋盘的四个角点
rect = cv2.minAreaRect(max_contour)
box = cv2.boxPoints(rect)
box = np.intp(box)

# 绘制轮廓和角点
cv2.drawContours(img, [box], 0, (0, 0, 255), 3)
for point in box:
    cv2.circle(img, tuple(point), 5, (0, 255, 0), -1)

width = int(rect[1][0])
height = int(rect[1][1])

warped = gray

# 圆检测，找到棋盘上的圆形，即棋子
circles = cv2.HoughCircles(warped, method=cv2.HOUGH_GRADIENT,
                           dp=1, minDist=25, param1=100, param2=19,
                           minRadius=10, maxRadius=20)
print('circles: ', circles)
circles = np.uint16(np.around(circles))

# 计算每个圆形所在的格子位置
grid_size = width // 18  # 棋盘有19x19个格子
centers = []  # 存储圆心坐标和格子位置
for i in circles[0, :]:
    cx = i[0]  # 圆心x坐标
    cy = i[1]  # 圆心y坐标
    r = i[2]  # 圆半径
    # 计算格子行号和列号，从0开始
    row = round(cy / grid_size) - 4
    col = round(cx / grid_size) - 4
    # 绘制圆形和圆心
    cv2.circle(img, (cx, cy), r, (0, 255, 0), 2)
    cv2.circle(img, (cx, cy), 2, (0, 0, 255), 2)
    # 添加到列表中
    centers.append((cx, cy, row, col))

# 颜色空间转换，将图像转换为HSV空间
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 阈值分割，根据黑子和白子的颜色范围分别设置阈值，得到两个二值图像
lower_black = np.array([0, 0, 10])
upper_black = np.array([180, 255, 90])
mask_black = cv2.inRange(hsv, lower_black, upper_black)
lower_white = np.array([0, 0, 100])
upper_white = np.array([180, 30, 255])
mask_white = cv2.inRange(hsv, lower_white, upper_white)

# 与运算，将二值图像和原图像相与，得到黑子和白子的图像
res_black = cv2.bitwise_and(img, img, mask=mask_black)
res_white = cv2.bitwise_and(img, img, mask=mask_white)

res_black = cv2.cvtColor(res_black, cv2.COLOR_BGR2GRAY)
res_white = cv2.cvtColor(res_white, cv2.COLOR_BGR2GRAY)

# cv2.imshow('res_black', res_black)
# cv2.imshow('res_white', res_white)

# 统计每个圆形区域内的非零像素个数，判断是否有棋子，以及棋子的颜色
stones = []  # 存储棋子的颜色和位置
for center in centers:
    cx, cy, row, col = center
    # 在黑子图像上取一个圆形区域
    black_roi = res_black[cy - r:cy + r, cx - r:cx + r]
    # 计算非零像素个数
    nz_count_black = cv2.countNonZero(black_roi)
    # 如果大于阈值，则判断为黑子
    if nz_count_black > 50:
        color = 'black'
        stones.append((color, row, col))

        cv2.putText(img, '(' + str(row + 1) + ',' + str(col + 1) + ')', (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 0, 255), 1)

        continue
    # 在白子图像上取一个圆形区域
    white_roi = res_white[cy - r:cy + r, cx - r:cx + r]
    # 计算非零像素个数
    nz_count_white = cv2.countNonZero(white_roi)
    # 如果大于阈值，则判断为白子
    if nz_count_white > 50:
        color = 'white'
        stones.append((color, row, col))

        cv2.putText(img, '(' + str(row + 1) + ',' + str(col + 1) + ')', (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (255, 0, 0), 1)

        continue

print('num: ', len(stones))

# 输出棋子的颜色和位置信息
board = []
for i in range(19):
    b = []
    for j in range(19):
        b.append(0)
    board.append(b)

cnt = 0
for stone in stones:
    color, row, col = stone
    print(f'There is a {color} stone at row {row + 1} and column {col + 1}.')
    board[row][col] = 1 if color == 'white' else 2

print(board)


def check_win(board, x, y):
    def check_dir(dx, dy):
        cnt = 1
        tx, ty = x + dx, y + dy
        while tx >= 0 and tx <= 18 and ty >= 0 and ty <= 18 and board[tx][ty] == board[x][y]:
            cnt += 1
            tx += dx
            ty += dy
        return cnt

    for dx, dy in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        if check_dir(dx, dy) + check_dir(-dx, -dy) - 1 >= 5:
            return True
    return False


flag = False
for stone in stones:
    color, row, col = stone
    if check_win(board, row, col):
        print(f"{color} stone Win!!! palce({row + 1}, {col + 1})")
        flag = True
        break

if not flag:
    print("No Win")

# 如果需要扩展功能，可以在这里添加检测五子连排的代码

# 显示图像
cv2.imshow('img', img)
# cv2.imshow('warped', warped)
cv2.waitKey(0)
cv2.destroyAllWindows()
