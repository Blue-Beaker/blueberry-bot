import random
import cv2
from numpy import ndarray
from nonebot import logger
import traceback

def get_variance_cv2(image:ndarray):
    try:
        """
        计算图像每个通道的方差（总体方差）
        :param image: OpenCV 读取的图像，numpy 数组，形状 (H, W, 3)，dtype=uint8，BGR 顺序
        :return: (red_variance, green_variance, blue_variance) 浮点数元组
        """
        # 使用 OpenCV 计算均值和标准差
        mean, stddev = cv2.meanStdDev(image)
        # stddev 形状为 (3, 1)，按 BGR 顺序排列，转换为方差
        variances = stddev.flatten() ** 2  # [B, G, R] 方差
        # 按 (R, G, B) 顺序返回
        return (variances[2], variances[1], variances[0])
    except:
        logger.error(traceback.format_exc())
        return (0,0,0)

def isnonsense_cv2(image:ndarray):
    """
    判断图像是否为“无意义”图像（三个通道方差之和小于 300）
    :param image: OpenCV 读取的图像
    :return: bool
    """
    r, g, b = get_variance_cv2(image)
    return r + g + b < 300

def random_crop(crop_width, crop_height, image:ndarray):
    
    height,width,channels = image.shape
    
    left = random.randint(0, width - crop_width)
    top = random.randint(0, height - crop_height)
    right = left + crop_width
    bottom = top + crop_height
    cropped_image = image[top:bottom,left:right]
    return left,top,right,bottom,cropped_image
