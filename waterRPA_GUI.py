# -*- coding: utf-8 -*-
import sys
import os
import time
import json
import pyautogui
import pyperclip
import traceback
from PIL import Image as PILImage
from io import BytesIO
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QComboBox, QLineEdit, QScrollArea, 
                               QFileDialog, QTextEdit, QMessageBox, QFrame, QCheckBox, QDialog, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QPixmap, QColor, QIcon, QClipboard

# --------------------------
# 自定义输入框和对话框 (版本B - 增强版)
# --------------------------

class ImageLineEdit(QLineEdit):
    """支持粘贴/拖拽图片的智能输入框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_history = []  # 本行的图片历史
        self.setPlaceholderText("粘贴截图或拖拽图片")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if self._is_image_file(file_path):
                    self.setText(file_path)
                    event.acceptProposedAction()
        elif mime_data.hasImage():
            pixmap = mime_data.imageData()
            self._process_pasted_image(pixmap)
            event.acceptProposedAction()
    
    def keyPressEvent(self, event):
        """监听快捷键，Ctrl+V时从剪贴板获取图片"""
        # 检测 Ctrl+V (粘贴快捷键)
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            print("\n" + "="*60)
            print("🔍【Ctrl+V 粘贴检测】")
            print("="*60)
            
            # 直接从QApplication的剪贴板获取图片
            clipboard = QApplication.clipboard()
            pixmap = clipboard.pixmap()
            
            print(f"✓ 剪贴板图片: {pixmap.width()}×{pixmap.height()}")
            
            if not pixmap.isNull():
                print("✓ 找到有效的图片数据，处理中...")
                self._process_pasted_image(pixmap)
                print("✓ 粘贴处理完成")
                print("="*60)
                return  # 阻止默认行为
            else:
                print("⚠️  剪贴板中没有图片")
                print("="*60)
        
        # 其他按键的默认处理
        super().keyPressEvent(event)
    
    def insertFromMimeData(self, source):
        """拦截粘贴事件 - 支持多种剪贴板格式"""
        # 尝试从source直接获取图片（用于dropEvent等场景）
        if source.hasImage():
            pixmap = source.imageData()
            if isinstance(pixmap, QPixmap) and not pixmap.isNull():
                print("✓ insertFromMimeData - 识别图片数据")
                self._process_pasted_image(pixmap)
                return
        
        # 尝试文件URL（拖拽文件）
        if source.hasUrls():
            urls = source.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if self._is_image_file(file_path) and os.path.exists(file_path):
                    print(f"✓ insertFromMimeData - 识别文件: {file_path}")
                    self.setText(file_path)
                    self._show_preview(file_path)
                    return
        
        # 默认行为（保留文本粘贴能力）
        super().insertFromMimeData(source)
    
    def _process_pasted_image(self, pixmap):
        """处理粘贴的图片（显示确认对话框）"""
        if not isinstance(pixmap, QPixmap):
            return
        
        # 显示确认对话框
        dialog = PasteConfirmDialog(pixmap, self)
        if dialog.exec() == QDialog.Accepted:
            saved_path = dialog.get_saved_path()
            if saved_path:
                self.setText(saved_path)
                self.image_history.append(saved_path)
                self._show_preview(saved_path)
    
    def _show_preview(self, file_path):
        """显示图片预览提示（文件名+大小）"""
        if os.path.exists(file_path):
            file_size_kb = os.path.getsize(file_path) / 1024
            self.setPlaceholderText(f"📷 {os.path.basename(file_path)} ({file_size_kb:.0f}KB)")
    
    def _is_image_file(self, file_path):
        """检查是否为图片文件"""
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        return file_path.lower().endswith(valid_extensions)
    
    def get_image_history(self):
        """获取图片历史列表"""
        return self.image_history
    
    def clear_history(self):
        """清空历史记录"""
        self.image_history.clear()


class PasteConfirmDialog(QDialog):
    """粘贴确认对话框 - 显示缩略图、大小、压缩选项"""
    
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.saved_path = None
        self.compress = False
        self.setWindowTitle("确认粘贴的图片")
        self.setFixedWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题（成功提示）
        title = QLabel("✓ 截图已复制到剪贴板")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(title)
        
        # 缩略图预览
        preview_label = QLabel()
        scaled = self.pixmap.scaledToHeight(150, Qt.SmoothTransformation)
        preview_label.setPixmap(scaled)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("border: 2px solid #ddd; padding: 10px; margin: 10px 0;")
        layout.addWidget(preview_label)
        
        # 图片信息（分辨率）
        info_text = f"分辨率: {self.pixmap.width()}×{self.pixmap.height()} px"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)
        
        # 压缩选项
        self.compress_check = QCheckBox("自动压缩大于1MB的图片")
        self.compress_check.setChecked(True)
        layout.addWidget(self.compress_check)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 保存")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px;")
        save_btn.clicked.connect(self.save_image)
        
        cancel_btn = QPushButton("✕ 取消")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def save_image(self):
        """保存图片到template目录"""
        template_dir = "template"
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        
        # 生成唯一文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(template_dir, f"screenshot_{timestamp}.png")
        
        # 避免文件名重复
        counter = 1
        base_filename = filename[:-4]
        while os.path.exists(filename):
            filename = f"{base_filename}_{counter}.png"
            counter += 1
        
        # 检查是否需要压缩
        pixmap = self.pixmap
        if self.compress_check.isChecked():
            file_size_mb = self.pixmap.width() * self.pixmap.height() * 4 / (1024*1024)
            if file_size_mb > 1:
                # 压缩到1920宽度
                pixmap = self.pixmap.scaledToWidth(1920, Qt.SmoothTransformation)
        
        # 保存图片
        if pixmap.save(filename):
            self.saved_path = filename
            # QMessageBox.information(self, "✓ 成功", f"图片已保存：\n{filename}")
            self.accept()
        else:
            QMessageBox.warning(self, "✕ 错误", f"无法保存图片到 {filename}")
    
    def get_saved_path(self):
        """获取保存的文件路径"""
        return self.saved_path

# --------------------------
# 核心逻辑 (原 waterRPA.py)
# --------------------------

def mouse_click(click_times, left_or_right, img, retry, timeout=60):
    """
    retry: 1 (一次), -1 (无限), >1 (指定次数)
    timeout: 超时时间(秒)，默认60秒。防止无限卡死。
    """
    start_time = time.time()
    
    if retry == 1:
        while True:
            # 检查超时
            if timeout and (time.time() - start_time > timeout):
                print(f"等待图片 {img} 超时 ({timeout}秒)")
                return # 或者抛出异常
            
            try:
                location=pyautogui.locateCenterOnScreen(img,confidence=0.9)
                if location is not None:
                    pyautogui.click(location.x,location.y,clicks=click_times,interval=0.2,duration=0.2,button=left_or_right)
                    break
            except pyautogui.ImageNotFoundException:
                pass # 没找到，继续重试
            
            print("未找到匹配图片,0.1秒后重试")
            time.sleep(0.1)
    elif retry == -1:
        while True:
            # 无限重试通常也需要某种中断机制，这里保留原意但增加超时保护（可选）
            # 如果确实想“死等”，可以把 timeout 设为 None
            if timeout and (time.time() - start_time > timeout):
                print(f"等待图片 {img} 超时 ({timeout}秒)")
                return 

            try:
                location=pyautogui.locateCenterOnScreen(img,confidence=0.9)
                if location is not None:
                    pyautogui.click(location.x,location.y,clicks=click_times,interval=0.2,duration=0.2,button=left_or_right)
            except pyautogui.ImageNotFoundException:
                pass

            time.sleep(0.1)
    elif retry > 1:
        i = 1
        while i < retry + 1:
            if timeout and (time.time() - start_time > timeout):
                print(f"操作超时 ({timeout}秒)")
                return

            try:
                location=pyautogui.locateCenterOnScreen(img,confidence=0.9)
                if location is not None:
                    pyautogui.click(location.x,location.y,clicks=click_times,interval=0.2,duration=0.2,button=left_or_right)
                    print("重复")
                    i += 1
            except pyautogui.ImageNotFoundException:
                pass
            
            time.sleep(0.1)

def mouse_move(img, retry, timeout=60):
    """
    鼠标悬停（移动但不点击）
    """
    start_time = time.time()
    while True:
        if timeout and (time.time() - start_time > timeout):
            print(f"等待图片 {img} 超时 ({timeout}秒)")
            return

        try:
            location = pyautogui.locateCenterOnScreen(img, confidence=0.9)
            if location is not None:
                pyautogui.moveTo(location.x, location.y, duration=0.2)
                break
        except pyautogui.ImageNotFoundException:
            pass

        print("未找到匹配图片,0.1秒后重试")
        time.sleep(0.1)
        if retry == 1: # 如果只试一次且没找到，直接退出（或者遵循原逻辑死循环？原mouse_click逻辑是retry=1也会死循环直到找到，这里保持一致）
            pass 
        # 注意：原mouse_click中 retry=1 也是 while True，直到找到。这里保持一致。

class RPAEngine: #RPA引擎，负责执行任务列表中的操作，并提供停止功能
    def __init__(self): 
        self.is_running = False
        self.stop_requested = False

    def stop(self): # 请求停止当前正在执行的任务
        self.stop_requested = True
        self.is_running = False

    def run_tasks(self, tasks, loop_forever=False, callback_msg=None): 
        """
        tasks: list of dict, format:
        [
            {"type": 1.0, "value": "1.png", "retry": 1},
            ...
        ]
        """
        self.is_running = True 
        self.stop_requested = False
        
        try:
            while True:
                for idx, task in enumerate(tasks): #遍历任务列表
                    if self.stop_requested: #检查终止信号
                        if callback_msg: 
                            callback_msg("任务已停止")
                        return
                    #提取任务参数
                    cmd_type = task.get("type")
                    cmd_value = task.get("value")
                    retry = task.get("retry", 1)

                    if callback_msg: #这里callback_msg一定会执行？  是的，只要在GUI中传入了这个函数，就会在每个步骤开始时调用它来更新日志区域，显示当前正在执行的操作类型和内容。这有助于用户了解程序的执行进度和当前操作的细节。
                        callback_msg(f"执行步骤 {idx+1}: 类型={cmd_type}, 内容={cmd_value}")

                    if cmd_type == 1.0: # 单击左键
                        mouse_click(1, "left", cmd_value, retry)
                        if callback_msg: 
                            callback_msg(f"单击左键: {cmd_value}")
                    
                    elif cmd_type == 2.0: # 双击左键
                        mouse_click(2, "left", cmd_value, retry)
                        if callback_msg: 
                            callback_msg(f"双击左键: {cmd_value}")
                    
                    elif cmd_type == 3.0: # 右键
                        mouse_click(1, "right", cmd_value, retry)
                        if callback_msg: 
                            callback_msg(f"右键单击: {cmd_value}")
                    
                    elif cmd_type == 4.0: # 输入
                        pyperclip.copy(str(cmd_value))
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.5)
                        if callback_msg: 
                            callback_msg(f"输入文本: {cmd_value}")
                    
                    elif cmd_type == 5.0: # 等待
                        sleep_time = float(cmd_value)
                        time.sleep(sleep_time)
                        if callback_msg: 
                            callback_msg(f"等待 {sleep_time} 秒")
                    
                    elif cmd_type == 6.0: # 滚轮
                        scroll_val = int(cmd_value)
                        pyautogui.scroll(scroll_val)
                        if callback_msg: 
                            callback_msg(f"滚轮滑动 {scroll_val}")

                    elif cmd_type == 7.0: # 系统按键 (组合键)
                        keys = str(cmd_value).lower().split('+')
                        # 去除空格
                        keys = [k.strip() for k in keys]
                        pyautogui.hotkey(*keys)
                        if callback_msg: 
                            callback_msg(f"按键组合: {cmd_value}")

                    elif cmd_type == 8.0: # 鼠标悬停
                        mouse_move(cmd_value, retry)
                        if callback_msg: 
                            callback_msg(f"鼠标悬停: {cmd_value}")

                    elif cmd_type == 9.0: # 截图保存
                        path = str(cmd_value)
                        # 如果是目录，自动拼接时间戳文件名
                        if os.path.isdir(path):
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filename = os.path.join(path, f"screenshot_{timestamp}.png")
                        else:
                            # 兼容旧逻辑：如果用户直接输入了带文件名的路径
                            filename = path
                            if not filename.endswith(('.png', '.jpg', '.bmp')):
                                filename += '.png'
                        
                        pyautogui.screenshot(filename)
                        if callback_msg: 
                            callback_msg(f"截图已保存: {filename}")

                if not loop_forever:
                    break
                
                if callback_msg: 
                    callback_msg("等待 0.1 秒进入下一轮循环...")
                time.sleep(0.1)
                
        except Exception as e:
            if callback_msg: 
                callback_msg(f"执行出错: {e}")
            traceback.print_exc()
        finally:
            self.is_running = False
            if callback_msg: 
                callback_msg("任务结束")

# --------------------------
# GUI 界面 (原 rpa_gui.py)
# --------------------------

# 定义操作类型映射
# 这是什么数据类型？    是一个字典，键是操作类型的中文描述，值是对应的数字代码（float）。这个映射用于在界面上显示友好的文本，同时在内部使用数字代码来区分不同的操作类型。
CMD_TYPES = {
    "左键单击": 1.0,
    "左键双击": 2.0,
    "右键单击": 3.0,
    "输入文本": 4.0,
    "等待(秒)": 5.0,
    "滚轮滑动": 6.0,
    "系统按键": 7.0,
    "鼠标悬停": 8.0,
    "截图保存": 9.0
}

CMD_TYPES_REV = {v: k for k, v in CMD_TYPES.items()} # 反向映射，方便根据数字代码找到对应的文本描述

# 线程类：负责在后台执行任务，避免界面卡死
class WorkerThread(QThread):

    log_signal = Signal(str) #  声明一个发送字符串的信号,接收方是GUI的log方法，用于更新日志区域
    finished_signal = Signal() # 声明一个无参数的信号，表示任务完成

    # 构造函数：接收 RPA 引擎实例、任务列表和是否循环执行的标志
    def __init__(self, engine, tasks, loop_forever):
        super().__init__()           # 调用父类QThread的初始化
        self.engine = engine         # 来源 于主窗口的 RPAEngine 实例，用于执行任务
        self.tasks = tasks           # 来源 于主窗口的任务列表，是一个字典列表，每个字典包含 type、value 和 retry 等信息
        self.loop_forever = loop_forever  # 来源 于主窗口的布尔值，表示是否循环执行任务

    def run(self):
        self.engine.run_tasks(self.tasks, self.loop_forever, self.log_callback) # 调用 RPAEngine 的 run_tasks 方法，执行每一个任务
        self.finished_signal.emit() # 任务完成后发送 finished_signal 信号，通知 GUI 可以更新界面状态（如启用开始按钮，禁用停止按钮等）

    def log_callback(self, msg): # 什么是回调函数？   回调函数是一种通过参数传递的函数，当某个事件发生时被调用。在这里，log_callback 是一个回调函数，它被传递给 RPAEngine 的 run_tasks 方法。当 RPAEngine 在执行任务过程中需要记录日志时，会调用这个 log_callback 函数，并将日志消息作为参数传递给它。log_callback 函数内部使用 self.log_signal.emit(msg) 将日志消息发送到 GUI 的 log 方法，从而在界面上显示日志信息。这种设计允许 RPAEngine 在执行过程中与 GUI 进行通信，而不需要直接依赖 GUI 的实现细节，实现了更好的模块化和解耦。
        self.log_signal.emit(msg) #emit 是 PyQt/PySide 中的一个方法，用于发送信号。当调用 self.log_signal.emit(msg) 时，所有连接到 log_signal 的槽函数（在这里是 GUI 的 log 方法）都会被调用，并且 msg 作为参数传递给它们。这是 PyQt/PySide 中线程间通信的常用方式，可以安全地从工作线程向主线程发送数据或通知。


class TaskRow(QFrame): # 每一行任务的 UI 组件，包含操作类型选择、参数输入、文件选择按钮、重试次数输入和删除按钮
    def __init__(self, parent_layout, delete_callback): # parent_layout 是父布局，用于将这个行组件添加到主界面；delete_callback 是一个函数，当点击删除按钮时调用，参数是当前行组件的实例
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # 操作类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(CMD_TYPES.keys()))
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.layout.addWidget(self.type_combo)
        
        # 参数输入区域（支持粘贴/拖拽图片）
        self.value_input = ImageLineEdit()
        self.value_input.setPlaceholderText("参数值 (粘贴截图或拖拽图片)")
        self.layout.addWidget(self.value_input)
        
        # 文件选择按钮 (默认隐藏)
        self.file_btn = QPushButton("选择图片")
        self.file_btn.clicked.connect(self.select_file)
        self.file_btn.setVisible(True) # 默认是左键单击，需要显示
        self.layout.addWidget(self.file_btn)
        
        # 重试次数 (默认隐藏)
        self.retry_input = QLineEdit()
        self.retry_input.setPlaceholderText("重试次数 (1=一次, -1=无限)")
        self.retry_input.setText("1")
        self.retry_input.setFixedWidth(100)
        self.retry_input.setVisible(True)
        self.layout.addWidget(self.retry_input)
        
        # 历史记录按钮
        self.history_btn = QPushButton("📋")
        self.history_btn.setFixedWidth(30)
        self.history_btn.setToolTip("查看本行的图片历史")
        self.history_btn.clicked.connect(self.show_image_history)
        self.history_btn.setVisible(False)  # 图片操作时显示
        self.layout.addWidget(self.history_btn)
        
        # 删除按钮
        self.del_btn = QPushButton("X")
        self.del_btn.setStyleSheet("color: red; font-weight: bold;")
        self.del_btn.setFixedWidth(30)
        self.del_btn.clicked.connect(lambda: delete_callback(self))
        self.layout.addWidget(self.del_btn)
        
        parent_layout.addWidget(self)

    def on_type_changed(self, text):
        cmd_type = CMD_TYPES[text]
        
        # 图片相关操作 (1, 2, 3, 8)
        if cmd_type in [1.0, 2.0, 3.0, 8.0]:
            self.file_btn.setVisible(True)
            self.file_btn.setText("选择图片")
            self.retry_input.setVisible(True)
            self.history_btn.setVisible(True)
            self.value_input.setPlaceholderText("📷 粘贴截图或拖拽 / 选择图片按钮")
        # 输入 (4)
        elif cmd_type == 4.0:
            self.file_btn.setVisible(False)
            self.history_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("请输入要发送的文本")
        # 等待 (5)
        elif cmd_type == 5.0:
            self.file_btn.setVisible(False)
            self.history_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("等待秒数 (如 1.5)")
        # 滚轮 (6)
        elif cmd_type == 6.0:
            self.file_btn.setVisible(False)
            self.history_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("滚动距离 (正数向上，负数向下)")
        # 系统按键 (7)
        elif cmd_type == 7.0:
            self.file_btn.setVisible(False)
            self.history_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("组合键 (如 ctrl+s, alt+tab)")
        # 截图保存 (9)
        elif cmd_type == 9.0:
            self.file_btn.setVisible(True)
            self.history_btn.setVisible(False)
            self.file_btn.setText("选择保存文件夹")
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("保存目录 (如 D:\\Screenshots)")

    def show_image_history(self):
        """显示本行的图片历史"""
        history = self.value_input.get_image_history()
        if not history:
            QMessageBox.information(self, "提示", "当前没有图片历史")
            return
        
        msg = "📋 本行的图片历史：\n\n"
        for i, path in enumerate(history, 1):
            file_size = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
            msg += f"{i}. {os.path.basename(path)} ({file_size:.0f}KB)\n"
        
        reply = QMessageBox.question(self, "图片历史", msg + "\n点击【是】快速重新使用最后一个图片？")
        if reply == QMessageBox.Yes and history:
            self.value_input.setText(history[-1])

    def set_data(self, data):
        """用于回填数据"""
        cmd_type = data.get("type")
        value = data.get("value", "")
        retry = data.get("retry", 1)

        # 设置类型 (反向查找文本)
        if cmd_type in CMD_TYPES_REV:
            self.type_combo.setCurrentText(CMD_TYPES_REV[cmd_type])
        
        # 设置值
        self.value_input.setText(str(value))
        
        # 设置重试次数
        self.retry_input.setText(str(retry))

    def select_file(self):
        cmd_type = CMD_TYPES[self.type_combo.currentText()]
        
        # 截图保存 (9.0) -> 选择文件夹
        if cmd_type == 9.0:
            folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹", os.getcwd())
            if folder:
                self.value_input.setText(folder)
        
        # 其他图片操作 (1, 2, 3, 8) -> 打开文件对话框
        else:
            filename, _ = QFileDialog.getOpenFileName(self, "选择图片", os.getcwd(), "Image Files (*.png *.jpg *.bmp)")
            if filename:
                self.value_input.setText(filename)

    def get_data(self):
        cmd_type = CMD_TYPES[self.type_combo.currentText()]
        value = self.value_input.text()
        
        # 数据校验与转换
        try:
            if cmd_type in [5.0, 6.0]:
                # 尝试转换为数字，如果失败可能会在运行时报错，这里简单处理
                if not value: value = "0"
            
            retry = 1
            if self.retry_input.isVisible():
                retry_text = self.retry_input.text()
                if retry_text:
                    retry = int(retry_text)
        except ValueError:
            pass # 保持默认

        return {
            "type": cmd_type,
            "value": value,
            "retry": retry
        }

class RPAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("非常简单 RPA 配置工具")
        self.resize(800, 600)
        
        self.engine = RPAEngine()
        self.worker = None #没有实例吗？    是的，worker 是在 start_task 方法中创建的，当用户点击“开始运行”按钮时才会实例化 WorkerThread 并启动线程。这里先初始化为 None，表示当前没有正在运行的任务线程。
        self.rows = [] #一开始为空？    是的，rows 是一个列表，用于存储当前界面上所有的 TaskRow 实例。初始时界面上没有任何任务行，所以 rows 列表是空的。当用户点击“新增指令”按钮时，会调用 add_row 方法创建新的 TaskRow 实例，并将其添加到 rows 列表中。

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) 

        # 顶部控制栏
        # [+新增] [保存] [导入]  ═════════════  [执行▼]  [开始]  [停止]
        #    按钮    按钮   按钮    (弹簧)       下拉框   按钮   按钮
        # 弹簧是 Qt 布局中的一个概念，指的是一个占位符组件，它会占据布局中剩余的空间，从而将其他组件推到布局的一端。
        top_bar = QHBoxLayout()
        
        self.add_btn = QPushButton("+ 新增指令")
        self.add_btn.clicked.connect(self.add_row)
        top_bar.addWidget(self.add_btn)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        top_bar.addWidget(self.save_btn)

        self.load_btn = QPushButton("导入配置")
        self.load_btn.clicked.connect(self.load_config)
        top_bar.addWidget(self.load_btn)
        
        top_bar.addStretch() #这里为什么加弹簧  top_bar.addStretch() 添加了一个弹簧（stretch），它会占据顶部控制栏中剩余的水平空间，从而将前面的按钮（新增指令、保存配置、导入配置）推到左侧，而后面的循环执行选项和开始/停止按钮则会靠右显示。这种布局方式使得界面看起来更整洁，按钮分布更合理。
        
        self.loop_check = QComboBox() #下拉框选择执行模式，默认是执行一次，用户可以选择循环执行
        self.loop_check.addItems(["执行一次", "循环执行"])
        top_bar.addWidget(self.loop_check)
        
        # 垂直布局容器：包含开始按钮和“运行时最小化”选项，
        # container相当于打包了组件？   是的，start_container 是一个 QWidget，它作为一个容器来包含开始按钮和“运行时最小化”选项。通过创建这个容器并设置一个垂直布局（QVBoxLayout），我们可以将开始按钮和复选框垂直排列在一起，然后将这个容器添加到顶部控制栏中。这样做的好处是可以更灵活地组织这些相关的控件，使得界面布局更加清晰和美观。 
        start_container = QWidget()
        start_layout = QVBoxLayout(start_container)
        start_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_btn = QPushButton("开始运行")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.start_btn.clicked.connect(self.start_task)
        start_layout.addWidget(self.start_btn)
        
        self.minimize_check = QCheckBox("运行时最小化")
        self.minimize_check.setChecked(True) # 默认开启
        start_layout.addWidget(self.minimize_check)
        
        top_bar.addWidget(start_container)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_btn.clicked.connect(self.stop_task)
        self.stop_btn.setEnabled(False)
        top_bar.addWidget(self.stop_btn)
        
        main_layout.addLayout(top_bar)

        # 任务列表区域 (滚动)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container) #垂直方向排列任务行
        self.task_layout.addStretch() # 弹簧，确保添加的行在顶部
        scroll.setWidget(self.task_container)
        main_layout.addWidget(scroll)

        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        main_layout.addWidget(QLabel("运行日志:"))
        main_layout.addWidget(self.log_area)

        # 初始添加一行
        self.add_row()

    def add_row(self, data=None):
        # 移除底部的弹簧
        self.task_layout.takeAt(self.task_layout.count() - 1) # 这行代码的作用是从 task_layout 中移除最后一个组件，这个组件是之前添加的弹簧（stretch）。因为我们要在这个位置添加新的 TaskRow，所以需要先移除弹簧，等添加完 TaskRow 后再加回弹簧。这样可以确保新的 TaskRow 被添加到布局的正确位置，而不会被弹簧推到其他地方。
        row = TaskRow(self.task_layout, self.delete_row)
        if data:
            row.set_data(data)
        self.rows.append(row)
        # 加回弹簧
        self.task_layout.addStretch()

    def delete_row(self, row_widget): #这里的row_widget是哪个组件？    row_widget 是 TaskRow 类的实例，代表当前行组件。当用户点击某一行的删除按钮时，这个函数会被调用，并且会传入对应的 TaskRow 实例作为参数。函数内部会检查这个实例是否在 self.rows 列表中，如果存在，就将其从列表中移除，并调用 deleteLater() 方法来删除这个组件，从而从界面上移除对应的任务行。
        if row_widget in self.rows:
            self.rows.remove(row_widget)
            row_widget.deleteLater()
            
    def save_config(self):
        tasks = []
        for row in self.rows:
            data = row.get_data() #get_data方法会返回一个字典，包含当前行的操作类型、参数值和重试次数等信息。这个数据结构与 RPAEngine 期望的任务列表格式一致，可以直接用于保存配置文件。
            tasks.append(data)
            
        if not tasks:
            QMessageBox.warning(self, "警告", "没有可保存的配置")
            return

         # 打开"保存文件"对话框
        filename, _ = QFileDialog.getSaveFileName(
            self,                                    # 父窗口
            "保存配置",                              # 对话框标题  
            os.getcwd(),                            # 初始目录
            "JSON Files (*.json);;Text Files (*.txt)"  # 文件类型过滤
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=4, ensure_ascii=False) # indent=4 使得保存的 JSON 文件更易读，ensure_ascii=False 允许保存中文字符而不是转义为 Unicode 编码
                QMessageBox.information(self, "成功", "配置已保存！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def load_config(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "导入配置", 
            os.getcwd(), 
            "JSON Files (*.json);;Text Files (*.txt)"
            )
        if not filename:
            return
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            
            if not isinstance(tasks, list): # 加载的文件内容必须是一个列表，列表中的每个元素应该是一个字典，代表一个任务。如果不是这种格式，就认为文件格式不正确。
                raise ValueError("文件格式不正确")

            # 清空现有行
            for row in self.rows:
                row.deleteLater()
            self.rows.clear()
            
            # 重新添加行
            for task in tasks:
                self.add_row(task)
                
            QMessageBox.information(self, "成功", f"成功导入 {len(tasks)} 条指令！")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def start_task(self):
        tasks = []
        for row in self.rows:
            data = row.get_data()
            if not data['value']: #如果参数值为空，提示用户检查输入，并且不启动任务。这是为了避免在执行过程中因为缺少必要的参数而导致错误或异常。
                QMessageBox.warning(self, "警告", "请检查有空参数的指令！")
                return
            tasks.append(data)
            
        if not tasks:
            QMessageBox.warning(self, "警告", "请至少添加一条指令！")
            return

        self.log_area.clear()
        self.log("任务开始...")
        
        # 更新按钮状态（防止重复启动）
        self.start_btn.setEnabled(False)   # 禁用开始按钮
        self.stop_btn.setEnabled(True)     # 启用停止按钮
        self.add_btn.setEnabled(False)     # 禁用添加按钮
        
        loop = (self.loop_check.currentText() == "循环执行")
        
        # 创建并启动工作线程
        self.worker = WorkerThread(self.engine, tasks, loop)
        # 【关键】连接信号到槽
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_finished) #收到任务结束信号后调用 on_finished 方法，更新界面状态并显示任务结束日志
        self.worker.start()        #启动线程，WorkerThread 的 run 方法会调用 RPAEngine 的 run_tasks 方法来执行任务列表，同时在执行过程中通过 log_signal 发送日志消息到 GUI 界面，任务完成后通过 finished_signal 通知 GUI 更新状态。


        # 最小化窗口 (如果勾选)
        if self.minimize_check.isChecked():
            self.showMinimized()

    def stop_task(self):
        self.engine.stop()
        self.log("正在停止...")

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        self.log("任务已结束")
        
        # 恢复窗口并置顶 (如果勾选了最小化，或者只是为了方便用户查看结果，通常都恢复比较好)
        if self.minimize_check.isChecked() or self.isMinimized():
            self.showNormal()
            self.activateWindow()

    def log(self, msg):
        self.log_area.append(msg)

    def closeEvent(self, event):
        """窗口关闭事件：确保线程停止，防止残留"""
        if self.worker and self.worker.isRunning():
            self.engine.stop()
            self.worker.quit()
            self.worker.wait()
        event.accept()

def main():
    app = QApplication(sys.argv) # 创建应用程序实例，sys.argv 允许从命令行传递参数（虽然这个程序目前没有使用命令行参数，但这是一个常见的模式）。创建 QApplication 实例是启动任何 PyQt/PySide 应用程序的第一步，它负责管理应用程序的控制流和主要设置。
    window = RPAWindow()
    window.show()
    sys.exit(app.exec()) # 启动事件循环，等待用户交互。exec() 方法会进入应用程序的主事件循环，直到应用程序退出（如用户关闭窗口）。sys.exit() 确保当应用程序退出时，返回一个适当的退出状态码给操作系统。

if __name__ == "__main__":
    main()
