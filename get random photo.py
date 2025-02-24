import requests
from PIL import Image, ImageTk
from io import BytesIO
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import cv2
import numpy as np
import datetime

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
    
    # 返回检测结果（概率阈值设为0.2）
    return nsfw_prob < 0.2

def get_image_with_retry(max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            print("正在获取图片...")
            # 获取图片
            image_url = "https://image.anosu.top/pixiv/direct" # pixiv图片api
            response = requests.get(image_url)
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            content_type = response.headers.get('Content-Type', '').lower()
            image = Image.open(BytesIO(response.content))
            print("图片获取成功,正在进行NSFW检测...")
            return image, content_type
        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"图片获取失败，尝试重新获取 ({retries}/{max_retries})...")
            if retries >= max_retries:
                print("图片获取失败，已达到最大重试次数，请检查您的网络或您给的图片URL是否正确。")
                return None, None

# 获取图片和Content-Type
image, content_type = get_image_with_retry()

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

# 创建保存目录
image_dir = "image"
os.makedirs(image_dir, exist_ok=True)

# 确定文件扩展名
format_to_ext = {
    'jpeg': 'jpg',
    'jpg': 'jpg',
    'png': 'png',
    'gif': 'gif',
    'webp': 'webp',
}

file_ext = 'jpg'  # 默认扩展名

# 优先使用PIL检测的图片格式
if image.format:
    pil_format = image.format.lower()
    file_ext = format_to_ext.get(pil_format, pil_format)
else:
    # 其次使用Content-Type判断
    if content_type:
        content_type_main = content_type.split(';')[0].strip().lower()
        if content_type_main.startswith('image/'):
            mime_type = content_type_main.split('/')[1]
            file_ext = format_to_ext.get(mime_type, mime_type)

# 生成文件名
current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
filename = os.path.join(image_dir, f"{current_time}.{file_ext}")

# 保存图片
try:
    image.save(filename)
    print(f"图片已保存为: {filename}")
except Exception as e:
    print(f"保存失败: {str(e)}")

# 创建图片显示窗口
image_window = tk.Toplevel()
image_window.title("随机图片")

# 调整图片大小以适应屏幕
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
img_width, img_height = image.size

# 计算缩放比例（仅在图片尺寸超过屏幕时缩放）
if img_width > screen_width or img_height > screen_height:
    width_ratio = screen_width / img_width
    height_ratio = screen_height / img_height
    scale_ratio = min(width_ratio, height_ratio)
    new_width = int(img_width * scale_ratio)
    new_height = int(img_height * scale_ratio)
else:
    new_width, new_height = img_width, img_height

# 高质量缩放
resized_image = image.resize((new_width, new_height), Image.LANCZOS)
tk_image = ImageTk.PhotoImage(resized_image)

# 设置窗口最大尺寸为屏幕尺寸
image_window.maxsize(screen_width, screen_height)

# 显示图片
label = tk.Label(image_window, image=tk_image)
label.pack()

# 窗口关闭处理（保持不变）
def on_closing():
    root.quit()

image_window.protocol("WM_DELETE_WINDOW", on_closing)
image_window.mainloop()
