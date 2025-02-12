import requests
from PIL import Image, ImageTk
from io import BytesIO
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import cv2
import numpy as np

# 创建主窗口
root = tk.Tk()
root.withdraw()  # 隐藏主窗口

def is_suitable_for_work(image):
    # 创建模型目录
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)
    
    # 模型文件路径
    prototxt_path = os.path.join(model_dir, "deploy.prototxt")
    caffemodel_path = os.path.join(model_dir, "resnet_50_1by2_nsfw.caffemodel")
    
    # 检查模型文件是否存在
    if not os.path.exists(prototxt_path):
        # 下载prototxt文件
        prototxt_url = "https://raw.githubusercontent.com/yahoo/open_nsfw/master/nsfw_model/deploy.prototxt"
        response = requests.get(prototxt_url)
        with open(prototxt_path, "wb") as f:
            f.write(response.content)
    
    if not os.path.exists(caffemodel_path):
        # 下载caffemodel文件（需确保URL有效）
        caffemodel_url = "https://github.com/yahoo/open_nsfw/raw/master/nsfw_model/resnet_50_1by2_nsfw.caffemodel"
        response = requests.get(caffemodel_url)
        with open(caffemodel_path, "wb") as f:
            f.write(response.content)
        # 注意：GitHub可能无法直接下载LFS文件，建议手动下载
    
    # 加载Caffe模型
    net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)
    
    # 转换PIL图像到OpenCV格式
    image_np = np.array(image)
    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    
    # 预处理（与Caffe模型匹配）
    blob = cv2.dnn.blobFromImage(
        image_cv, 
        scalefactor=1.0,
        size=(224, 224),
        mean=(104.0, 117.0, 123.0),
        swapRB=False,  # 已在前面转换颜色通道
        crop=True
    )
    
    # 执行推理
    net.setInput(blob)
    preds = net.forward()
    
    # 解析输出结果（输出格式：[概率非NSFW, 概率NSFW]）
    nsfw_prob = preds[0][1]
    print(f"[调试] NSFW概率值: {nsfw_prob:.4f}")
    
    # 返回检测结果（概率阈值设为0.3）
    return nsfw_prob < 0.3

def get_image_with_retry(max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            print("正在获取图片...")
            # 获取图片
            image_url = "https://image.anosu.top/pixiv/direct" # 这里是pixiv的API,当然你也可以换成其他的API
            response = requests.get(image_url)
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            image = Image.open(BytesIO(response.content))
            print("图片获取成功,正在进行NSFW检测...")
            return image
        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"图片获取失败，尝试重新获取 ({retries}/{max_retries})...")
            if retries >= max_retries:
                print("图片获取失败，已达到最大重试次数，请检查您的网络或您给的图片URL是否正确。")
                return None

# 获取图片
image = get_image_with_retry()

if image is None:
    print("无法获取图片，程序退出。")
    root.quit()
    exit()

# NSFW检测
if not is_suitable_for_work(image):
    print("[调试]图片不适合工作场合")
    # 如果不适合，询问用户是否继续显示
    user_choice = messagebox.askyesno("警告", "此图片可能为NSFW内容(工作场合不宜)。是否继续显示？")
    if not user_choice:
        root.quit()
        exit()

# 创建图片显示窗口
image_window = tk.Toplevel()
image_window.title("随机图片")

# 转换并显示图片
tk_image = ImageTk.PhotoImage(image)
label = tk.Label(image_window, image=tk_image)
label.pack()

# 窗口关闭处理
def on_closing():
    root.quit()

image_window.protocol("WM_DELETE_WINDOW", on_closing)
image_window.mainloop()