import requests
from PIL import Image, ImageTk
from io import BytesIO
import tkinter as tk
from tkinter import simpledialog, messagebox
import re  # 导入正则表达式模块
import os

# 创建主窗口
root = tk.Tk()
root.withdraw()  # 隐藏主窗口

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["NO_PROXY"] = "*"

# 验证QQ号格式的函数
def is_valid_qq(qq):
    # 正则表达式：5到12位数字
    pattern = r'^\d{5,12}$'
    return re.match(pattern, qq) is not None

# 判断头像是否适合在工作场合显示的函数
def is_suitable_for_work(image):
    # 转换为RGB确保处理正确
    image = image.convert('RGB')
    width, height = image.size
    total_pixels = width * height

    # 转换为HSV颜色空间
    hsv = image.convert('HSV')
    h, s, v = hsv.split()

    # 计算平均饱和度和明度
    avg_s = sum(pixel / 255.0 for pixel in s.getdata()) / total_pixels
    avg_v = sum(pixel / 255.0 for pixel in v.getdata()) / total_pixels

    # # 条件1：平均饱和度不宜过高
    # if avg_s > 0.6:
    #     return False

    # # 条件2：明度不宜过低或过高
    # if avg_v < 0.3 or avg_v > 0.9:
    #     return False

    # 条件3：检测高红色区域（R>200且G,B<100）
    red_count = 0
    for r, g, b in image.getdata():
        if r > 200 and g < 100 and b < 100:
            red_count += 1
    if red_count / total_pixels > 0.4:  # 超过40%的红色区域
        return False

    # 条件4：检测肤色区域（H在0-30，S>=0.2，V>=0.4）
    h_data = [pixel * 2 for pixel in h.getdata()]  # H范围0-360
    s_data = [pixel / 255.0 for pixel in s.getdata()]
    v_data = [pixel / 255.0 for pixel in v.getdata()]

    skin_count = 0
    for h_val, s_val, v_val in zip(h_data, s_data, v_data):
        if 0 <= h_val <= 30 and s_val >= 0.2 and v_val >= 0.4:
            skin_count += 1
    if skin_count / total_pixels > 0.5:  # 超过50%的肤色区域
        return False

    return True

# 弹窗输入QQ号
qq_number = simpledialog.askstring("输入QQ号", "请输入QQ号:")

if qq_number:
    if is_valid_qq(qq_number):
        try:
            # 构造QQ头像的URL
            image_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq_number}&s=5"

            # 发送HTTP请求获取图片
            response = requests.get(image_url)
            response.raise_for_status()  # 检查请求是否成功

            # 将图片内容转换为Pillow的Image对象
            image = Image.open(BytesIO(response.content))

            # 判断头像是否适合在工作场合显示
            if not is_suitable_for_work(image):
                # 如果不适合，询问用户是否继续显示
                user_choice = messagebox.askyesno("警告", "此头像可能不适合在工作场合显示。是否继续显示？")
                if not user_choice:
                    root.quit()
                    exit()

            # 创建一个新窗口显示图片
            image_window = tk.Toplevel()
            image_window.title("QQ头像")

            # 设置窗口大小（宽度x高度）
            window_width = 512  # 设置窗口宽度
            window_height = 512  # 设置窗口高度
            image_window.geometry(f"{window_width}x{window_height}")

            # 调整图片大小以适应窗口
            image = image.resize((window_width, window_height), Image.Resampling.LANCZOS)

            # 将Pillow图片转换为Tkinter可用的格式
            tk_image = ImageTk.PhotoImage(image)

            # 创建标签并显示图片
            label = tk.Label(image_window, image=tk_image)
            label.pack()

            # 绑定窗口关闭事件
            def on_closing():
                root.quit()  # 退出主循环

            image_window.protocol("WM_DELETE_WINDOW", on_closing)

            # 运行Tkinter主循环
            image_window.mainloop()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("错误", f"无法获取QQ头像: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"发生未知错误: {e}")
    else:
        messagebox.showwarning("警告", "QQ号格式不正确！")
else:
    messagebox.showwarning("警告", "未输入QQ号")
