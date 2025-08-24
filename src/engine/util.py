import os
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from PyQt5.QtGui import QColor


def to_ndarray(image_path: str) -> Optional[np.ndarray]:
    """
    将本地图片文件转换为 Optional[np.ndarray]

    参数:
        image_path: 图片文件路径

    返回:
        Optional[np.ndarray]: 成功则返回图像数组，失败则返回None
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"错误: 文件不存在 - {image_path}")
            return None

        # 打开图像文件
        image = Image.open(image_path)

        # 转换为RGB模式（确保三通道）
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 转换为numpy数组
        image_array = np.array(image)

        return image_array

    except Exception as e:
        print(f"转换图片时出错: {e}")
        return None


def crop_ndarray(
        image: Optional[np.ndarray],
        left: int,
        top: int,
        width: int,
        height: int
) -> Optional[np.ndarray]:
    """
    根据给定的区域参数裁剪图像

    参数:
        image: 输入的图像数组，可以是None
        left: 裁剪区域左边界
        top: 裁剪区域上边界
        width: 裁剪区域宽度
        height: 裁剪区域高度

    返回:
        Optional[np.ndarray]: 裁剪后的图像数组，如果输入为None或裁剪失败则返回None
    """
    # 检查输入是否为None
    if image is None:
        return None

    # 检查输入是否为有效的numpy数组
    if not isinstance(image, np.ndarray):
        print("错误: 输入不是numpy数组")
        return None

    # 检查数组维度
    if image.ndim not in [2, 3]:
        print("错误: 不支持的图像维度")
        return None

    # 获取图像尺寸
    img_height, img_width = image.shape[:2]

    # 验证裁剪参数
    if left < 0 or top < 0 or width <= 0 or height <= 0:
        print("错误: 裁剪参数无效")
        return None

    # 计算裁剪区域的右边界和下边界
    right = left + width
    bottom = top + height

    # 检查裁剪区域是否超出图像边界
    if left >= img_width or top >= img_height:
        print("错误: 裁剪区域完全超出图像边界")
        return None

    # 调整裁剪区域以确保在图像范围内
    adj_left = max(0, left)
    adj_top = max(0, top)
    adj_right = min(img_width, right)
    adj_bottom = min(img_height, bottom)

    # 计算调整后的宽度和高度
    adj_width = adj_right - adj_left
    adj_height = adj_bottom - adj_top

    # 如果调整后的区域无效，返回None
    if adj_width <= 0 or adj_height <= 0:
        print("错误: 调整后的裁剪区域无效")
        return None

    # 执行裁剪
    try:
        if image.ndim == 2:  # 灰度图像
            cropped = image[adj_top:adj_bottom, adj_left:adj_right]
        else:  # 彩色图像
            cropped = image[adj_top:adj_bottom, adj_left:adj_right, :]

        return cropped
    except Exception as e:
        print(f"裁剪图像时出错: {e}")
        return None


def save_ndarray(image: Optional[np.ndarray],
                 folder_path: str,
                 filename: Optional[str] = None,
                 default_name: str = "board_image") -> bool:
    """
    将可能为空的numpy数组图像保存到本地文件夹

    参数:
        image: 要保存的图像数组，可以是None
        folder_path: 保存图像的文件夹路径
        filename: 指定的文件名（不含扩展名），如果为None则自动生成
        default_name: 当filename为None时使用的默认名称前缀

    返回:
        bool: 保存成功返回True，失败返回False
    """
    # 检查图像是否为空
    if image is None:
        print("警告: 图像为空，无法保存")
        return False

    # 确保文件夹存在
    os.makedirs(folder_path, exist_ok=True)

    # 生成文件名
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{default_name}_{timestamp}.png"
    else:
        # 确保文件名有正确的扩展名
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            filename += '.png'

    # 构建完整文件路径
    file_path = os.path.join(folder_path, filename)

    try:
        # 保存图像
        success = cv2.imwrite(file_path, image)
        if success:
            print(f"图像已成功保存到: {file_path}")
            return True
        else:
            print(f"保存图像失败: {file_path}")
            return False
    except Exception as e:
        print(f"保存图像时发生错误: {str(e)}")
        return False


def gtp_2_np(gtp, size):
    column_letter = gtp[0].upper()
    row_number = int(gtp[1:])
    if column_letter < 'I':
        col = ord(column_letter) - ord('A')
    else:
        col = ord(column_letter) - ord('A') - 1  # 跳过I
    row = size - row_number
    return row, col

def get_win_rate_color(win_rate):
    """
    根据胜率返回对应的QColor颜色对象
    参数:
        win_rate (float): 胜率百分比值（0-100）
    返回:
        QColor: 对应的颜色对象
    """
    if win_rate*100 > 95:
        return QColor(255, 0, 0, 200)    # 红色
    elif win_rate > 85:
        return QColor(255, 165, 0, 200)  # 橙色
    elif win_rate > 75:
        return QColor(128, 0, 128, 200)  # 紫色
    elif win_rate > 50:
        return QColor(0, 0, 255, 200)    # 蓝色
    else:
        return QColor(255, 255, 255, 200) # 白色