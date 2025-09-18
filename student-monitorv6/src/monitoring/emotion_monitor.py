"""
编程情绪监控系统 - 独立版（彻底修复版）
功能：
1. 每120秒弹出独立情绪量表窗口
2. 收集学生选择的情绪状态
3. 将选择结果保存到CSV文件（含时间戳）
彻底修复了多线程和Tkinter的问题
"""

import csv
import time
import threading
import os
import queue
from datetime import datetime
import logging
import sys

# 尝试导入Tkinter，如果失败则提供友好的错误信息
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    Tkinter_AVAILABLE = True
except ImportError:
    Tkinter_AVAILABLE = False
    print("警告: Tkinter不可用，情绪监控功能将无法正常工作")
    print("请安装Tkinter: 在Ubuntu/Debian上使用 'sudo apt-get install python3-tk'")
    print("或在Windows上确保安装了Tkinter组件")

# 配置日志
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "emotion_monitor.log")),
        logging.StreamHandler()
    ]
)

class EmotionMonitor:
    def __init__(self, username, interval=120, stop_event=None):
        """
        初始化情绪监控器
        :param username: 用户名
        :param interval: 弹出间隔（秒）
        :param stop_event: 停止事件
        """
        if not Tkinter_AVAILABLE:
            logging.warning("Tkinter不可用，情绪监控器将无法正常工作")

        self.username = username
        self.interval = interval
        self.is_running = False
        self.thread = None
        self.gui_thread = None
        self.stop_event = stop_event or threading.Event()
        self.gui_queue = queue.Queue()
        self.gui_ready = threading.Event()

        # 设置输出文件路径
        data_dir = os.path.join(BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)
        self.output_file = os.path.join(data_dir, f"{username}_emotion_performance.csv")

        # 确保输出文件存在
        self.init_output_file()

        logging.info(f"情绪监控器初始化完成，用户: {username}, 间隔: {interval}秒")

    def init_output_file(self):
        """初始化输出文件"""
        if not os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'emotion', 'description'])
                logging.info(f"创建新的输出文件: {self.output_file}")
            except Exception as e:
                logging.error(f"创建输出文件失败: {str(e)}")

    def save_response(self, emotion, description):
        """保存情绪响应到CSV文件"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, emotion, description])
            logging.info(f"记录情绪: {emotion} - {description}")
        except Exception as e:
            logging.error(f"保存情绪响应失败: {str(e)}")

    def gui_main(self):
        """GUI线程的主函数"""
        if not Tkinter_AVAILABLE:
            logging.error("Tkinter不可用，无法启动GUI")
            self.gui_ready.set()
            return

        try:
            # 创建主Tkinter实例但不显示
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口

            # 存储当前窗口引用
            current_window = None
            selected_emotion = None

            # 通知主线程GUI已准备好
            self.gui_ready.set()

            def process_gui_queue():
                """处理GUI队列中的命令"""
                try:
                    # 处理所有队列中的命令
                    while True:
                        try:
                            command, data = self.gui_queue.get_nowait()

                            if command == 'show_dialog':
                                show_emotion_dialog()
                            elif command == 'close_dialog':
                                close_dialog()
                            elif command == 'quit':
                                close_dialog()
                                root.quit()
                                return

                        except queue.Empty:
                            break

                    # 如果没有退出命令，继续处理队列
                    if not self.stop_event.is_set():
                        root.after(100, process_gui_queue)

                except Exception as e:
                    logging.error(f"处理GUI队列时出错: {str(e)}")
                    if not self.stop_event.is_set():
                        root.after(100, process_gui_queue)

            def show_emotion_dialog():
                """显示情绪对话框"""
                nonlocal current_window, selected_emotion

                # 关闭现有窗口
                close_dialog()

                # 创建新窗口
                current_window = tk.Toplevel(root)
                current_window.title(f"编程情绪微量表 - {self.username}")
                current_window.geometry("600x400")

                # 窗口置顶
                current_window.attributes("-topmost", True)
                current_window.focus_force()
                current_window.grab_set()  # 模态窗口

                # 设置窗口位置为屏幕中央
                current_window.update_idletasks()
                width = current_window.winfo_width()
                height = current_window.winfo_height()
                x = (current_window.winfo_screenwidth() // 2) - (width // 2)
                y = (current_window.winfo_screenheight() // 2) - (height // 2)
                current_window.geometry(f"+{x}+{y}")

                current_window.resizable(False, False)
                current_window.protocol("WM_DELETE_WINDOW", lambda: on_dialog_close(None))

                # 创建主框架
                main_frame = ttk.Frame(current_window, padding=20)
                main_frame.pack(fill=tk.BOTH, expand=True)

                # 标题
                title_label = ttk.Label(
                    main_frame,
                    text="编程情绪微量表",
                    font=("Arial", 18, "bold"),
                    foreground="#2c3e50"
                )
                title_label.pack(pady=(0, 15))

                question_label = ttk.Label(
                    main_frame,
                    text="问题：当前最符合你状态的描述是？",
                    font=("Arial", 14),
                    foreground="#34495e"
                )
                question_label.pack(pady=(0, 25))

                # 情绪选项
                emotions = [
                    {"letter": "A", "name": "专注", "description": "流畅编码，完全投入"},
                    {"letter": "B", "name": "无聊", "description": "简单重复，缺乏挑战"},
                    {"letter": "C", "name": "沮丧", "description": "反复报错，难以解决"},
                    {"letter": "D", "name": "困惑", "description": "思路卡壳，不知方向"}
                ]

                # 创建选项按钮
                selected_emotion = tk.StringVar()

                for emotion in emotions:
                    frame = ttk.Frame(main_frame, padding=10)
                    frame.pack(fill=tk.X, pady=8, padx=15)

                    option_text = f"{emotion['letter']}. {emotion['name']}（{emotion['description']}）"

                    rb = ttk.Radiobutton(
                        frame,
                        text=option_text,
                        variable=selected_emotion,
                        value=emotion['name'],
                        command=lambda e=emotion: on_emotion_selected(e)
                    )
                    rb.pack(anchor=tk.W)

                # 关闭按钮
                close_btn = ttk.Button(
                    main_frame,
                    text="关闭窗口（不保存）",
                    command=lambda: on_dialog_close(None),
                )
                close_btn.pack(pady=25)

            def close_dialog():
                """关闭对话框"""
                nonlocal current_window
                if current_window:
                    try:
                        current_window.destroy()
                    except:
                        pass
                    current_window = None

            def on_emotion_selected(emotion):
                """处理情绪选择"""
                # 保存响应
                option_text = f"{emotion['letter']}.{emotion['name']}（{emotion['description']}）"
                self.save_response(emotion['name'], option_text)

                # 关闭对话框
                close_dialog()

                logging.info(f"情绪选择已保存: {emotion['name']}")

            def on_dialog_close(event):
                """处理对话框关闭"""
                close_dialog()

            # 开始处理GUI队列
            root.after(100, process_gui_queue)

            # 运行Tkinter主循环
            root.mainloop()

        except Exception as e:
            logging.error(f"GUI线程错误: {str(e)}")
            self.gui_ready.set()
        finally:
            # 确保资源被清理
            try:
                if 'root' in locals() and root:
                    root.quit()
            except:
                pass

    def show_emotion_scale(self):
        """显示情绪量表窗口（线程安全）"""
        if not self.is_running or self.stop_event.is_set() or not Tkinter_AVAILABLE:
            return False

        # 发送显示命令到GUI队列
        try:
            self.gui_queue.put(('show_dialog', None))
            return True
        except:
            logging.error("无法发送显示命令到GUI队列")
            return False

    def close_dialog(self):
        """关闭对话框（线程安全）"""
        if not Tkinter_AVAILABLE:
            return

        try:
            self.gui_queue.put(('close_dialog', None))
        except:
            pass

    def periodic_prompt(self):
        """定期弹出情绪量表"""
        while self.is_running and not self.stop_event.is_set():
            try:
                logging.info("弹出情绪量表...")
                self.show_emotion_scale()

                # 等待下一个周期
                for _ in range(self.interval):
                    if not self.is_running or self.stop_event.is_set():
                        break
                    time.sleep(1)

            except Exception as e:
                logging.error(f"定期提示错误: {str(e)}")
                time.sleep(1)

    def start(self):
        """启动情绪监控器"""
        if not self.is_running:
            logging.info("启动情绪监控器")
            self.is_running = True

            # 启动GUI线程（如果Tkinter可用）
            if Tkinter_AVAILABLE:
                self.gui_thread = threading.Thread(target=self.gui_main)
                self.gui_thread.daemon = True
                self.gui_thread.start()

                # 等待GUI初始化完成
                self.gui_ready.wait(timeout=5)
            else:
                logging.warning("Tkinter不可用，情绪监控器将以无GUI模式运行")

            # 启动提示线程
            self.thread = threading.Thread(target=self.periodic_prompt)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """停止情绪监控器"""
        if self.is_running:
            logging.info("停止情绪监控器")
            self.is_running = False
            self.stop_event.set()

            # 通知GUI线程退出
            if Tkinter_AVAILABLE:
                try:
                    self.gui_queue.put(('quit', None))
                except:
                    pass

                # 等待GUI线程结束
                if self.gui_thread and self.gui_thread.is_alive():
                    self.gui_thread.join(timeout=2)

            # 等待提示线程结束
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)

    def run(self):
        """运行情绪监控器"""
        self.start()
        try:
            # 保持主线程运行
            while self.is_running and not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logging.error(f"发生错误: {str(e)}")
            self.stop()

def main():
    """独立运行情绪监控器"""
    if len(sys.argv) != 2:
        print("用法: python emotion_monitor.py <用户名>")
        sys.exit(1)

    username = sys.argv[1]
    monitor = EmotionMonitor(username, interval=120)
    monitor.run()

if __name__ == "__main__":
    main()