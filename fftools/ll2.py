import os
import tkinter as tk
from tkinter import ttk, filedialog
import subprocess

# 设置文件选择
def browse_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        path_label.config(text=file_path)

# 调用whisper进行语音转文字
def whisper():
    # 判断是否选择了文件
    if path_label.cget("text") == "文件路径":
        # 弹出提示框
        tk.messagebox.showinfo(title='提示', message='请先选择文件')
        return
    else:
        # 调用控制台激活虚拟环境whisper
        outpath=path_label.cget("text")
        # 找到文件夹路径
        outpath=outpath[:outpath.rfind("/")+1]
        print(outpath)
        # 获得选择的语言模型
        model=model_dropdown_value.get()
        # 合成命令行语句
        cmd="start cmd /k \"conda activate whisper && whisper "+path_label.cget("text")+" --model "+ model +" --language Japanese --task translate --output_format srt --output_dir "+outpath+" && EXIT\""
        print(cmd)
        # 执行命令行语句，结束后自动关闭
        subprocess.Popen(cmd,shell=True).wait()
        # 将字幕从英文翻译成中文

# 添加程序入口
if __name__ =='__main__':
    root = tk.Tk()
    root.title("Whisper字幕生成器")
    # 设置背景颜色
    root.config(bg="#F7EFE5")
    root.geometry("640x480")

    ################################语言模型选择################################
    # 窗口的最上面空一行
    ttk.Label(root).pack(pady=10)
    # 创建行的模块，以将模型选择的标签和下拉列表框放在一起
    model_row_frame = ttk.Frame(root)
    model_row_frame.pack(pady=10)
    # 创建模型标签
    model_dropdown_label = ttk.Label(model_row_frame, text="选择语言模型：", font=("微软雅黑", 14))
    model_dropdown_label.pack(side="left")
    # 创建模型选择拉列表
    model_options = ["tiny", "base", "small", "medium", "large"]
    model_dropdown_value = tk.StringVar(value=model_options[0])
    model_dropdown = ttk.Combobox(model_row_frame, textvariable=model_dropdown_value, justify="center", values=model_options, width=20, foreground="#FD5825", font=("微软雅黑", 14))
    model_dropdown.pack(side="left", padx=10)
    ################################语言模型选择################################
    # 创建行的模块，以将语言选择的标签和下拉列表框放在一起
    language_row_frame = ttk.Frame(root)
    language_row_frame.pack(pady=10)
    # 创建模型标签
    language_dropdown_label = ttk.Label(language_row_frame, text="选择语音语种：", font=("微软雅黑", 14))
    language_dropdown_label.pack(side="left")
    # 创建语言选择下拉列表
    language_options = ["日语", "英语", "中文"]
    language_dropdown_value = tk.StringVar(value=language_options[0])
    language_dropdown = ttk.Combobox(language_row_frame, textvariable=language_dropdown_value, justify="center", values=language_options, width=20, foreground="#FD5825", font=("微软雅黑", 14))
    language_dropdown.pack(side="left", padx=10)
    ################################语言模型选择################################
    # 创建行的模块，以将语言选择的标签和下拉列表框放在一起
    bing_or_google_row_frame = ttk.Frame(root)
    bing_or_google_row_frame.pack(pady=10)
    # 创建模型标签
    bing_or_google_dropdown_label = ttk.Label(bing_or_google_row_frame, text="选择翻译引擎：", font=("微软雅黑", 14))
    bing_or_google_dropdown_label.pack(side="left")
    # 创建语言选择下拉列表
    bing_or_google_options = ["必应", "谷歌翻译（需要梯子）"]
    bing_or_google_dropdown_value = tk.StringVar(value=bing_or_google_options[0])
    bing_or_google_dropdown = ttk.Combobox(bing_or_google_row_frame, textvariable=bing_or_google_dropdown_value, justify="center", values = bing_or_google_options, width=20, foreground="#FD5825", font=("微软雅黑", 14))
    bing_or_google_dropdown.pack(side="left", padx=10)
    ################################视频文件选择################################
    # 创建文件选择按钮
    # 创建行的模块，以将语言选择的标签和下拉列表框放在一起
    file_row_frame = ttk.Frame(root)
    file_row_frame.pack(pady=10)
    # 创建模型标签
    filepath_label = ttk.Label(file_row_frame, text="选择视频文件：", font=("微软雅黑", 14))
    filepath_label.pack(side="left")
    filepath_button = tk.Button(file_row_frame, text="...", command=browse_file, width=10, bg="#3FABAF", fg="#F7EFE5", font=("微软雅黑", 14, "bold"))
    filepath_button.pack(side="left", padx=10)
    # 创建文件路径标签，标签居中对齐
    path_label = ttk.Label(root, text="文件路径", font=("微软雅黑", 14), justify="center")
    path_label.pack(pady=10)
    ################################Whisper语音转字幕################################
    whisper_Trans_button = tk.Button(root, text="语音转字幕", command=whisper, width=20, bg="#3FABAF", fg="#F7EFE5", font=("微软雅黑", 14, "bold"))
    whisper_Trans_button.pack(pady=10)
    ################################Whisper语音转字幕################################
    merge_button = tk.Button(root, text="合并语音和字幕", width=20, bg="#3FABAF", fg="#F7EFE5", font=("微软雅黑", 14, "bold"))
    merge_button.pack(pady=10)
    root.mainloop()
