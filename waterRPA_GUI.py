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
                               QFileDialog, QTextEdit, QFrame, QCheckBox, QDialog, QStyle)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QPixmap, QColor, QIcon, QClipboard, QPalette
import cv2
import numpy as np
# ==========================================
# 全局精美 QSS 样式表 (现代化扁平风格)
# ==========================================
MODERN_QSS = """
/* 主窗口背景 */
QMainWindow {
    background-color: #F0F2F5;
}

/* 强制对话框和提示框为白底黑字，防止被系统深色模式污染 */
QDialog, QMessageBox { 
    background-color: #FFFFFF; 
    color: #333333; 
}
QDialog QLabel, QMessageBox QLabel { 
    color: #333333; 
}
QDialog QCheckBox { 
    color: #333333; 
}

/* 按钮通用样式 */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D9D9D9;
    border-radius: 4px;
    padding: 6px 12px;
    color: #333333;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    color: #1890FF;
    border-color: #1890FF;
    background-color: #F8FBFF;
}
QPushButton:pressed {
    background-color: #E6F7FF;
}

/* 顶部操作按钮特殊强调 */
QPushButton#startBtn {
    background-color: #52C41A;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#startBtn:hover { background-color: #73D13D; }
QPushButton#startBtn:disabled { background-color: #B7EB8F; color: #FFFFFF; }

QPushButton#stopBtn {
    background-color: #FF4D4F;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#stopBtn:hover { background-color: #FF7875; }
QPushButton#stopBtn:disabled { background-color: #FFA39E; color: #FFFFFF; }

/* 输入框和下拉框 */
QLineEdit, QComboBox {
    border: 1px solid #D9D9D9;
    border-radius: 4px;
    padding: 5px 8px;
    background-color: #FFFFFF;
    color: #333333;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #1890FF;
}

/* 下拉框弹出列表（防止被系统深色模式污染，强制明亮风格） */
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #D9D9D9;
    selection-background-color: #E6F7FF;
    selection-color: #333333;
    outline: 0;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #D9D9D9;
}
QComboBox::drop-down:hover {
    background-color: #F8FBFF;
}
QComboBox:on {
    background-color: #FFFFFF;
}

/* 指令卡片样式 (TaskRow) */
QFrame#taskCard {
    background-color: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-radius: 6px;
    margin-bottom: 2px;
}
QFrame#taskCard:hover {
    border: 1px solid #1890FF;
    background-color: #FAFAFA;
}

/* 删除和移动按钮特殊样式 */
QPushButton#iconBtn {
    border: none;
    background: transparent;
    font-size: 14px;
    padding: 4px;
}
QPushButton#iconBtn:hover {
    background-color: #E8E8E8;
    border-radius: 4px;
}
QPushButton#deleteBtn {
    color: #FF4D4F;
}
QPushButton#deleteBtn:hover {
    background-color: #FFF1F0;
}

/* 日志区域 (改为明亮清爽的风格) */
QTextEdit {
    background-color: #FFFFFF;
    color: #555555;
    border: 1px solid #D9D9D9;
    border-radius: 6px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    padding: 10px;
}
"""


def apply_light_combobox(combo: QComboBox) -> None:
    """强制下拉弹层为亮色（解决 Windows 深色模式下弹出列表黑底问题）。"""
    # 不替换 view（避免 popup 定位/尺寸变化），只对现有弹层做样式兜底
    view = combo.view()
    if view is None:
        return

    view.setStyleSheet(
        "QAbstractItemView { background-color: #FFFFFF; color: #333333; }"
        "QAbstractItemView::item { padding: 4px 8px; }"
        "QAbstractItemView::item:selected { background-color: #E6F7FF; color: #333333; }"
    )

    pal = view.palette()
    pal.setColor(QPalette.Base, QColor("#FFFFFF"))
    pal.setColor(QPalette.Text, QColor("#333333"))
    pal.setColor(QPalette.Highlight, QColor("#E6F7FF"))
    pal.setColor(QPalette.HighlightedText, QColor("#333333"))
    view.setPalette(pal)
    view.setAutoFillBackground(True)


class LightMessageDialog(QDialog):
    """自绘轻量弹窗：绕开 Windows 深色模式/原生对话框导致的黑底问题。"""

    def __init__(self, parent, title: str, text: str, icon: QStyle.StandardPixmap, buttons=("OK",)):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._result = None

        self.setModal(True)
        self.setMinimumWidth(360)

        self.setStyleSheet(
            "QDialog { background-color: #FFFFFF; }"
            "QLabel { color: #333333; font-size: 13px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        body = QHBoxLayout()
        body.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        pm = QApplication.style().standardIcon(icon).pixmap(36, 36)
        icon_label.setPixmap(pm)
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        body.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        body.addWidget(text_label, 1)

        root.addLayout(body)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        def add_btn(caption: str, is_default: bool = False):
            btn = QPushButton(caption)
            btn.clicked.connect(lambda: self._close_with(caption))
            btn_row.addWidget(btn)
            if is_default:
                btn.setDefault(True)
                btn.setAutoDefault(True)

        if len(buttons) == 1:
            add_btn(buttons[0], True)
        else:
            # 约定：最后一个作为默认按钮
            for i, cap in enumerate(buttons):
                add_btn(cap, i == len(buttons) - 1)

        root.addLayout(btn_row)

    def _close_with(self, caption: str):
        self._result = caption
        self.accept()

    @property
    def result_caption(self):
        return self._result


def show_info(parent, title: str, text: str) -> None:
    LightMessageDialog(parent, title, text, QStyle.SP_MessageBoxInformation, buttons=("OK",)).exec()


def show_warning(parent, title: str, text: str) -> None:
    LightMessageDialog(parent, title, text, QStyle.SP_MessageBoxWarning, buttons=("OK",)).exec()


def show_error(parent, title: str, text: str) -> None:
    LightMessageDialog(parent, title, text, QStyle.SP_MessageBoxCritical, buttons=("OK",)).exec()


def ask_yes_no(parent, title: str, text: str, yes_text: str = "是", no_text: str = "否") -> bool:
    dlg = LightMessageDialog(parent, title, text, QStyle.SP_MessageBoxQuestion, buttons=(no_text, yes_text))
    dlg.exec()
    return dlg.result_caption == yes_text

# --------------------------
# 自定义输入框和对话框 (原封不动，非常完美)
# --------------------------

class ImageLineEdit(QLineEdit):
    # [代码保持不变...]
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_history =[]
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
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            clipboard = QApplication.clipboard()
            pixmap = clipboard.pixmap()
            if not pixmap.isNull():
                self._process_pasted_image(pixmap)
                return
        super().keyPressEvent(event)
    
    def insertFromMimeData(self, source):
        if source.hasImage():
            pixmap = source.imageData()
            if isinstance(pixmap, QPixmap) and not pixmap.isNull():
                self._process_pasted_image(pixmap)
                return
        if source.hasUrls():
            urls = source.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if self._is_image_file(file_path) and os.path.exists(file_path):
                    self.setText(file_path)
                    self._show_preview(file_path)
                    return
        super().insertFromMimeData(source)
    
    def _process_pasted_image(self, pixmap):
        if not isinstance(pixmap, QPixmap): return
        dialog = PasteConfirmDialog(pixmap, self)
        if dialog.exec() == QDialog.Accepted:
            saved_path = dialog.get_saved_path()
            if saved_path:
                self.setText(saved_path)
                self.image_history.append(saved_path)
                self._show_preview(saved_path)
    
    def _show_preview(self, file_path):
        if os.path.exists(file_path):
            file_size_kb = os.path.getsize(file_path) / 1024
            self.setPlaceholderText(f"📷 {os.path.basename(file_path)} ({file_size_kb:.0f}KB)")
    
    def _is_image_file(self, file_path):
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        return file_path.lower().endswith(valid_extensions)
    
    def get_image_history(self): return self.image_history
    def clear_history(self): self.image_history.clear()

class PasteConfirmDialog(QDialog):
    """粘贴确认对话框 - 彻底修复黑屏背景和字体不清问题"""
    
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.saved_path = None
        self.compress = False
        self.setWindowTitle("确认粘贴的图片")
        self.setFixedWidth(420)  # 稍微加宽一点，让比例更协调
        
        # 【关键修复】：直接在这个弹窗级别强制写死白底黑字，无视系统黑夜模式
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QCheckBox {
                color: #333333;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25) # 增加内边距让四周更透气
        
        # 标题
        title = QLabel("✓ 截图已复制到剪贴板")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #52C41A;")
        layout.addWidget(title)
        
        # 缩略图预览
        preview_label = QLabel()
        
        # 【修复点：智能按比例缩放预览图】
        # 对话框宽度为420，减去两边内边距25*2，可用最大宽度约为 360
        max_preview_width = 360
        max_preview_height = 160
        
        # 判断：如果原图大于这个预览框的尺寸，才进行缩放；
        # 如果原图本身就很小（比如几十像素的小图标），则保持原大小，防止被放大导致模糊。
        if self.pixmap.width() > max_preview_width or self.pixmap.height() > max_preview_height:
            scaled = self.pixmap.scaled(
                max_preview_width, 
                max_preview_height, 
                Qt.KeepAspectRatio,         # 核心参数：保持图片的原始长宽比
                Qt.SmoothTransformation     # 平滑缩放，防止出现锯齿
            )
        else:
            scaled = self.pixmap
            
        preview_label.setPixmap(scaled)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #E0E0E0; padding: 10px; margin: 15px 0; background: #F8F9FA; border-radius: 6px;")
        layout.addWidget(preview_label)
        
        # 【修复点 1】：分辨率文字改为深灰色，在白底上极其清晰
        info_text = f"分辨率: {self.pixmap.width()} × {self.pixmap.height()} px"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666666; font-size: 13px;") 
        layout.addWidget(info_label)
        
        # 【修复点 2】：复选框（文字颜色已在顶部的 setStyleSheet 统一定义）
        self.compress_check = QCheckBox("自动压缩大于 1MB 的图片")
        self.compress_check.setChecked(True)
        self.compress_check.setStyleSheet("margin-top: 5px; margin-bottom: 15px;")
        layout.addWidget(self.compress_check)
        
        # --- 精美的操作按钮 ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("✕ 取消")
        cancel_btn.setCursor(Qt.PointingHandCursor) # 鼠标悬浮变成小手
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #666666;
                border: 1px solid #D9D9D9;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { 
                color: #1890FF; 
                border-color: #1890FF; 
                background-color: #F8FBFF; 
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("💾 保存图片")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890FF;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #40A9FF; }
            QPushButton:pressed { background-color: #096DD9; }
        """)
        save_btn.clicked.connect(self.save_image)
        
        # 将按钮推到右侧
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def save_image(self):
        # （这里的保存逻辑保持你原来的不变即可，下面是原样复制）
        template_dir = "template"
        if not os.path.exists(template_dir): os.makedirs(template_dir)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(template_dir, f"screenshot_{timestamp}.png")
        
        counter = 1
        base_filename = filename[:-4]
        while os.path.exists(filename):
            filename = f"{base_filename}_{counter}.png"
            counter += 1
        
        pixmap = self.pixmap
        if self.compress_check.isChecked():
            file_size_mb = self.pixmap.width() * self.pixmap.height() * 4 / (1024*1024)
            if file_size_mb > 1:
                pixmap = self.pixmap.scaledToWidth(1920, Qt.SmoothTransformation)
        
        if pixmap.save(filename):
            self.saved_path = filename
            self.accept()
        else:
            show_warning(self, "✕ 错误", f"无法保存图片到 {filename}")

            
    def get_saved_path(self): 
        return self.saved_path


import os
from PIL import Image as PILImage

def _process_red_box_logic(img_path):
    """
    【深度优化版】：
    1. 智能过滤干扰：识别多个红色区域，只锁定面积最大、像素最密集的红框。
    2. 消除偏移：忽略 UI 自带的零散红点。
    """
    has_red = False
    offset_x, offset_y = 0, 0
    search_path = img_path
    
    try:
        source_img = PILImage.open(img_path).convert('RGBA')
        width, height = source_img.size
        pixels = source_img.load()
        
        red_pixels = []
        search_img = source_img.copy()
        search_pixels = search_img.load()
        
        # 1. 扫描所有红色像素，并同时将搜索图透明化（确保识别不卡死）
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                # 严格判定红框颜色 (R值极高，且远大于G和B)
                if r > 180 and r > g * 2.5 and r > b * 2.5:
                    red_pixels.append((x, y))
                    # 只要是红色，就在搜索图中设为透明，保证特征匹配成功
                    search_pixels[x, y] = (0, 0, 0, 0)
        
        if len(red_pixels) > 10:
            # 2. 【核心算法】：聚类分析
            # 我们将像素点进行分组，距离较近的像素点视为同一个物体
            clusters = []
            threshold = 20 # 判定为同一个框的像素距离阈值
            
            for px, py in red_pixels:
                found_cluster = False
                for cluster in clusters:
                    # 检查当前点是否在某个已有区域的边界附近
                    if (cluster['min_x'] - threshold <= px <= cluster['max_x'] + threshold and 
                        cluster['min_y'] - threshold <= py <= cluster['max_y'] + threshold):
                        cluster['pts'].append((px, py))
                        cluster['min_x'] = min(cluster['min_x'], px)
                        cluster['max_x'] = max(cluster['max_x'], px)
                        cluster['min_y'] = min(cluster['min_y'], py)
                        cluster['max_y'] = max(cluster['max_y'], py)
                        found_cluster = True
                        break
                if not found_cluster:
                    clusters.append({'pts': [(px, py)], 'min_x': px, 'max_x': px, 'min_y': py, 'max_y': py})
            
            # 3. 锁定真正的“目标框”：选取包含像素点最多的那个群体
            # 这能完美过滤掉 Clash 图标上的红点或 UI 的小红标
            if clusters:
                target_cluster = max(clusters, key=lambda c: len(c['pts']))
                
                # 如果这个群体足够大（防止误判噪点）
                if len(target_cluster['pts']) > 10:
                    has_red = True
                    # 只计算这个特定群体（即你的红框）的中心点
                    offset_x = (target_cluster['min_x'] + target_cluster['max_x']) // 2
                    offset_y = (target_cluster['min_y'] + target_cluster['max_y']) // 2
                    
                    # 保存临时搜索图 (无红框版)
                    temp_dir = "temp_masks"
                    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
                    search_path = os.path.join(temp_dir, f"search_{os.path.basename(img_path)}")
                    search_img.save(search_path)
            
    except Exception as e:
        print(f"红框深度解析异常: {e}")
        
    return has_red, offset_x, offset_y, search_path


def mouse_click(click_times, left_or_right, img_path, retry, engine, timeout=60):
    """
    1. 查找符合整图特征的区域 (无视红框部分)
    2. 找到后点击红框所在的局部坐标
    """
    start_time = time.time()
    
    # 步骤1：预处理图像，得到“挖掉红色”的图和点击偏移量
    has_red, off_x, off_y, search_img = _process_red_box_logic(img_path)
    
    while True:
        # 实时检测停止信号
        if engine.stop_requested:
            return False

        if timeout and (time.time() - start_time > timeout):
            return False

        try:
            # 步骤2：在屏幕上寻找符合特征的整块区域
            # 注意：使用 search_img (已经变透明了红框部分)，置信度设为0.8
            box = pyautogui.locateOnScreen(search_img, confidence=0.8)
            
            if box is not None:
                if has_red:
                    # 步骤3：在找到的区域(box)内，根据偏移量定位红框中心
                    target_x = box.left + off_x
                    target_y = box.top + off_y
                else:
                    # 没画红框，则点整图正中心
                    target_x = box.left + box.width / 2
                    target_y = box.top + box.height / 2
                
                pyautogui.click(target_x, target_y, clicks=click_times, interval=0.2, duration=0.2, button=left_or_right)
                return True
        except:
            pass # 没找到，继续循环直到超时

        time.sleep(0.2)


def mouse_move(img_path, retry, engine, timeout=60):
    """悬停逻辑同上"""
    start_time = time.time()
    has_red, off_x, off_y, search_img = _process_red_box_logic(img_path)
    
    while True:
        if engine.stop_requested: return False
        if timeout and (time.time() - start_time > timeout): return False

        try:
            box = pyautogui.locateOnScreen(search_img, confidence=0.8)
            if box is not None:
                tx = box.left + off_x if has_red else box.left + box.width/2
                ty = box.top + off_y if has_red else box.top + box.height/2
                pyautogui.moveTo(tx, ty, duration=0.2)
                return True
        except:
            pass
        time.sleep(0.2)

# --- RPAEngine 类中的 run_tasks 方法调用也需同步更新 ---

class RPAEngine:
    def __init__(self): 
        self.is_running = False
        self.stop_requested = False

    def stop(self):
        self.stop_requested = True
        self.is_running = False

    def run_tasks(self, tasks, loop_forever=False, callback_msg=None): 
        self.is_running = True 
        self.stop_requested = False
        try:
            while True:
                for idx, task in enumerate(tasks):
                    if self.stop_requested:
                        if callback_msg: callback_msg(">>> 🛑 任务已手动停止")
                        return
                    
                    cmd_type = task.get("type")
                    cmd_value = task.get("value")
                    retry = task.get("retry", 1)

                    if callback_msg:
                        callback_msg(f"▶ 步骤 {idx+1}: {CMD_TYPES_REV.get(cmd_type, '未知')}")

                    # 统一分发指令，传递 self 以便子函数检测 stop_requested
                    if cmd_type == 1.0: mouse_click(1, "left", cmd_value, retry, self)
                    elif cmd_type == 2.0: mouse_click(2, "left", cmd_value, retry, self)
                    elif cmd_type == 3.0: mouse_click(1, "right", cmd_value, retry, self)
                    elif cmd_type == 8.0: mouse_move(cmd_value, retry, self)
                    
                    # 文本输入 (保持不变)
                    elif cmd_type == 4.0:
                        pyperclip.copy(str(cmd_value))
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.5)
                        
                    # 等待 (优化：可以随时停止)
                    elif cmd_type == 5.0:
                        wait_t = float(cmd_value)
                        for _ in range(int(wait_t * 10)):
                            if self.stop_requested: return
                            time.sleep(0.1)
                            
                    # 其余简单操作略...
                    elif cmd_type == 6.0: pyautogui.scroll(int(cmd_value))
                    elif cmd_type == 7.0:
                        keys = [k.strip() for k in str(cmd_value).lower().split('+')]
                        pyautogui.hotkey(*keys)

                if not loop_forever: break
                time.sleep(0.2)
        finally:
            self.is_running = False
            if callback_msg: callback_msg("🏁 任务流结束")

# --------------------------
# GUI 界面重构 (组件化 & QSS美化)
# --------------------------

CMD_TYPES = {
    "左键单击": 1.0, "左键双击": 2.0, "右键单击": 3.0,
    "输入文本": 4.0, "等待(秒)": 5.0, "滚轮滑动": 6.0,
    "系统按键": 7.0, "鼠标悬停": 8.0, "截图保存": 9.0
}
CMD_TYPES_REV = {v: k for k, v in CMD_TYPES.items()}

class WorkerThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, engine, tasks, loop_forever):
        super().__init__()
        self.engine = engine
        self.tasks = tasks
        self.loop_forever = loop_forever

    def run(self):
        self.engine.run_tasks(self.tasks, self.loop_forever, self.log_callback)
        self.finished_signal.emit()

    def log_callback(self, msg):
        self.log_signal.emit(msg)


class TaskRow(QFrame):
    """
    【高精集成版】任务行组件
    功能：
    1. 实时同比缩略图预览
    2. 支持粘贴/拖拽图片的智能输入框
    3. 自动显隐逻辑 (根据操作类型切换 UI)
    4. 排序与删除信号通信
    """
    
    # 定义自定义信号，用于与主窗口通信
    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName("taskCard")  #应用 QSS 样式。setObjectName 是 Qt 的机制，允许我们在 QSS 中针对特定组件定义样式，而不影响其他同类组件。
        
        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        self.layout.setSpacing(8)
        
        # --- 1. 排序控制区 (左侧) ---
        sort_layout = QVBoxLayout()
        sort_layout.setSpacing(2)
        self.up_btn = QPushButton("▲")
        self.up_btn.setObjectName("iconBtn")
        self.up_btn.setFixedSize(22, 18)
        self.up_btn.clicked.connect(lambda: self.move_up_requested.emit(self))
        
        self.down_btn = QPushButton("▼")
        self.down_btn.setObjectName("iconBtn")
        self.down_btn.setFixedSize(22, 18)
        self.down_btn.clicked.connect(lambda: self.move_down_requested.emit(self))
        
        sort_layout.addWidget(self.up_btn)
        sort_layout.addWidget(self.down_btn)
        self.layout.addLayout(sort_layout)
        
        # --- 2. 操作类型选择 ---
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(CMD_TYPES.keys()))
        self.type_combo.setFixedWidth(105)
        apply_light_combobox(self.type_combo)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.layout.addWidget(self.type_combo)

        # --- 3. 【新增】实时缩略图预览 ---
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(64, 42)  # 16:10 左右的比例
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setText("No Img")
        self.thumb_label.setStyleSheet("""
            QLabel {
                background-color: #F0F2F5;
                border: 1px solid #D9D9D9;
                border-radius: 3px;
                color: #999;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.thumb_label)
        
        # --- 4. 参数输入框 (支持图片粘贴) ---
        self.value_input = ImageLineEdit()
        self.value_input.setPlaceholderText("参数值 (支持任何颜色的框选定位)")
        # 核心：文本改变时立即更新缩略图
        self.value_input.textChanged.connect(self.update_thumbnail)
        self.layout.addWidget(self.value_input)
        
        # --- 5. 辅助功能区 (浏览、重试、历史) ---
        self.file_btn = QPushButton("📁 浏览")
        self.file_btn.setFixedWidth(70)
        self.file_btn.clicked.connect(self.select_file)
        self.layout.addWidget(self.file_btn)
        
        self.retry_input = QLineEdit()
        self.retry_input.setPlaceholderText("次数")
        self.retry_input.setText("1")
        self.retry_input.setFixedWidth(50)
        self.retry_input.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.retry_input)
        
        self.history_btn = QPushButton("📋")
        self.history_btn.setObjectName("iconBtn")
        self.history_btn.setFixedSize(32, 32)
        self.history_btn.setToolTip("查看本行图片历史记录")
        self.history_btn.clicked.connect(self.show_image_history)
        self.layout.addWidget(self.history_btn)
        
        # --- 6. 删除按钮 (右侧) ---
        self.del_btn = QPushButton("✖")
        self.del_btn.setObjectName("deleteBtn")
        self.del_btn.setFixedSize(32, 32)
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        self.layout.addWidget(self.del_btn)

        # 初始化显示状态
        self.on_type_changed(self.type_combo.currentText())

    def update_thumbnail(self):
        """实时更新缩略图，保持比例同比缩小"""
        path = self.value_input.text().strip() #strip() 去除首尾空格，防止路径错误
        # 处理路径中可能存在的双引号（拖拽文件时常见）这行代码的作用是将路径字符串中的所有双引号（"）替换为空字符串（''）。
        path = path.replace('"', '') 
        
        if os.path.exists(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # 同比缩小以适应预览框，不失真
                scaled = pixmap.scaled(
                    self.thumb_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.thumb_label.setPixmap(scaled)
                self.thumb_label.setToolTip(f"完整路径: {os.getcwd()}{os.sep}{path}") #os.sep 根据系统自动使用 \ 或 / 
                return
        
        # 如果不是有效的图片路径，重置显示
        self.thumb_label.clear()
        self.thumb_label.setText("No Img")
        self.thumb_label.setToolTip("")

    def on_type_changed(self, text):
        """根据操作类型动态调整 UI 元素的可见性"""
        cmd_type = CMD_TYPES[text]
        
        # 图片类操作 (1, 2, 3, 8)
        is_img = cmd_type in [1.0, 2.0, 3.0, 8.0]
        
        self.thumb_label.setVisible(is_img)
        self.file_btn.setVisible(is_img or cmd_type == 9.0)
        self.retry_input.setVisible(is_img)
        self.history_btn.setVisible(is_img)
        
        # 修改 Placeholder 提示
        if is_img:
            self.value_input.setPlaceholderText("📷 粘贴截图")
            self.file_btn.setText("📁 浏览")
            self.update_thumbnail()
        elif cmd_type == 4.0:
            self.value_input.setPlaceholderText("请输入要自动输入的文本内容")
        elif cmd_type == 5.0:
            self.value_input.setPlaceholderText("等待时长 (秒)，如 1.5")
        elif cmd_type == 9.0:
            self.value_input.setPlaceholderText("截图保存的文件夹路径")
            self.file_btn.setText("📁 目录")

    def select_file(self):
        """浏览文件/目录"""
        cmd_type = CMD_TYPES[self.type_combo.currentText()]
        if cmd_type == 9.0:
            folder = QFileDialog.getExistingDirectory(self, "选择保存目录", os.getcwd())
            if folder: self.value_input.setText(folder)
        else:
            file, _ = QFileDialog.getOpenFileName(self, "选择图片", os.getcwd(), "图片 (*.png *.jpg *.bmp)")
            if file: self.value_input.setText(file)

    def show_image_history(self):
        """显示本行的图片历史"""
        history = self.value_input.get_image_history()
        if not history:
            show_info(self, "提示", "本行暂无图片粘贴记录")
            return
        
        msg = "📋 图片历史 (按时间排序):\n\n"
        for i, p in enumerate(history, 1):
            msg += f"{i}. {os.path.basename(p)}\n"
        
        if ask_yes_no(self, "历史记录", msg + "\n是否重新加载最后一次截图？"):
            self.value_input.setText(history[-1])

    def set_data(self, data):
        """回填数据 (导入配置用)"""
        cmd_type = data.get("type", 1.0)
        self.type_combo.setCurrentText(CMD_TYPES_REV.get(cmd_type, "左键单击"))
        self.value_input.setText(str(data.get("value", "")))
        self.retry_input.setText(str(data.get("retry", "1")))
        self.update_thumbnail()

    def get_data(self):
        """提取数据 (保存配置/执行任务用)"""
        return {
            "type": CMD_TYPES[self.type_combo.currentText()],
            "value": self.value_input.text().strip(),
            "retry": int(self.retry_input.text()) if self.retry_input.text().isdigit() or self.retry_input.text() == "-1" else 1
        }

class RPAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPA 精致自动化工具")
        self.resize(900, 650)
        # 注入精美样式
        self.setStyleSheet(MODERN_QSS)
        
        self.engine = RPAEngine()
        self.worker = None 
        self.rows =[]

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) 
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # ====== 1. 顶部现代化控制栏 ======
        top_bar = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 新增指令")
        self.add_btn.clicked.connect(self.add_row)
        top_bar.addWidget(self.add_btn)

        self.load_btn = QPushButton("📂 导入配置")
        self.load_btn.clicked.connect(self.load_config)
        top_bar.addWidget(self.load_btn)

        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.clicked.connect(self.save_config)
        top_bar.addWidget(self.save_btn)
        
        top_bar.addStretch() # 弹簧，把控制按钮推到右边
        
        self.minimize_check = QCheckBox("运行时最小化")
        self.minimize_check.setChecked(True)
        top_bar.addWidget(self.minimize_check)

        self.loop_check = QComboBox()
        self.loop_check.addItems(["执行一次", "循环执行"])
        apply_light_combobox(self.loop_check)
        top_bar.addWidget(self.loop_check)
        
        self.start_btn = QPushButton("▶ 开始运行")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_task)
        top_bar.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_task)
        self.stop_btn.setEnabled(False)
        top_bar.addWidget(self.stop_btn)
        
        main_layout.addLayout(top_bar)

        # ====== 2. 中间滚动任务列表 ======
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.task_container = QWidget()
        self.task_container.setStyleSheet("background-color: transparent;")
        
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 10, 0)
        self.task_layout.setSpacing(5)
        self.task_layout.addStretch() # 保持项在顶部
        
        scroll.setWidget(self.task_container)
        main_layout.addWidget(scroll, stretch=3) # 占据大部分空间

        # ====== 3. 底部运行日志 ======
        log_label = QLabel("运行日志 (Log):")
        log_label.setStyleSheet("color: #666; font-weight: bold;")
        main_layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(180)
        main_layout.addWidget(self.log_area, stretch=1)

        # 初始默认行
        self.add_row()

    # --- 核心排版与视图逻辑 ---
    
    def add_row(self, data=None):
        """【重构】安全的动态添加行组件"""
        # 1. 移除底部占位弹簧
        self.task_layout.takeAt(self.task_layout.count() - 1)
        
        # 2. 实例化独立的组件
        row_widget = TaskRow()
        if data:
            row_widget.set_data(data)
            
        # 3. 连接组件发出的信号
        row_widget.delete_requested.connect(self.delete_row)
        row_widget.move_up_requested.connect(self.move_up)
        row_widget.move_down_requested.connect(self.move_down)
        
        # 4. 塞入布局和内存管理
        self.task_layout.addWidget(row_widget)
        self.rows.append(row_widget)
        
        # 5. 加回占位弹簧
        self.task_layout.addStretch()

    def delete_row(self, row_widget):
        """【重构】接收子组件销毁请求"""
        if row_widget in self.rows:
            self.task_layout.removeWidget(row_widget)
            self.rows.remove(row_widget)
            row_widget.deleteLater()

    def move_up(self, row_widget):
        """【新增】安全且丝滑的上移功能"""
        idx = self.task_layout.indexOf(row_widget)
        if idx > 0: # 如果不是第一行
            self.task_layout.removeWidget(row_widget)
            self.task_layout.insertWidget(idx - 1, row_widget)
            # 同步更新内部 List (虽然我们按布局取数据，但保持一致是个好习惯)
            self.rows.remove(row_widget)
            self.rows.insert(idx - 1, row_widget)

    def move_down(self, row_widget):
        """【新增】安全且丝滑的下移功能"""
        idx = self.task_layout.indexOf(row_widget)
        # 减 2 是因为 layout 的最后一个元素永远是弹簧 (Stretch)
        if idx < self.task_layout.count() - 2:
            self.task_layout.removeWidget(row_widget)
            self.task_layout.insertWidget(idx + 1, row_widget)
            self.rows.remove(row_widget)
            self.rows.insert(idx + 1, row_widget)

    # --- 业务逻辑 ---
    
    def _get_ordered_tasks(self):
        """【重构】总是按照界面视觉的从上到下顺序获取任务"""
        tasks =[]
        # 遍历 Layout 获取正确的视觉顺序
        for i in range(self.task_layout.count() - 1): # -1 略过弹簧
            widget = self.task_layout.itemAt(i).widget()
            if isinstance(widget, TaskRow):
                tasks.append(widget.get_data())
        return tasks

    def save_config(self):
        tasks = self._get_ordered_tasks()
        if not tasks:
            show_warning(self, "警告", "没有可保存的配置")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "保存配置", os.getcwd(), "JSON Files (*.json);;Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=4, ensure_ascii=False)
                self.log("配置已保存到：" + filename)
            except Exception as e:
                show_error(self, "错误", f"保存失败: {e}")

    def load_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "导入配置", os.getcwd(), "JSON Files (*.json);;Text Files (*.txt)")
        if not filename: return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            if not isinstance(tasks, list): raise ValueError("文件格式不正确")

            # 清空现有行
            for row in list(self.rows):
                self.delete_row(row)
            
            # 重新添加行
            for task in tasks:
                self.add_row(task)
            self.log(f"成功导入 {len(tasks)} 条指令！")
        except Exception as e:
            show_error(self, "错误", f"导入失败: {e}")

    def start_task(self):
        tasks = self._get_ordered_tasks()
        for data in tasks:
            if not data['value']:
                show_warning(self, "警告", "存在参数为空的指令，请检查！")
                return
        if not tasks:
            show_warning(self, "警告", "请至少添加一条指令！")
            return

        self.log_area.clear()
        self.log("🚀 任务开始初始化...")
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_btn.setEnabled(False)
        
        loop = (self.loop_check.currentText() == "循环执行")
        
        self.worker = WorkerThread(self.engine, tasks, loop)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

        if self.minimize_check.isChecked():
            self.showMinimized()

    def stop_task(self):
        self.engine.stop()
        self.log("⏸ 正在发出停止请求...")

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        
        if self.minimize_check.isChecked() or self.isMinimized():
            self.showNormal()
            self.activateWindow()

    def log(self, msg):
        self.log_area.append(msg)
        # 自动滚动到底部
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.engine.stop()
            self.worker.quit()
            self.worker.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    # 支持高分屏 (让字体和图片更锐利)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # 禁用原生对话框：确保 QMessageBox / QFileDialog 等弹窗也能吃到 QSS，避免深色模式黑底
    app.setAttribute(Qt.AA_DontUseNativeDialogs)
    # 统一使用 Fusion，避免原生控件/弹层在深色模式下走系统配色
    app.setStyle("Fusion")
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor("#F0F2F5"))
    light_palette.setColor(QPalette.WindowText, QColor("#333333"))
    light_palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    light_palette.setColor(QPalette.AlternateBase, QColor("#FAFAFA"))
    light_palette.setColor(QPalette.Text, QColor("#333333"))
    light_palette.setColor(QPalette.Button, QColor("#FFFFFF"))
    light_palette.setColor(QPalette.ButtonText, QColor("#333333"))
    light_palette.setColor(QPalette.Highlight, QColor("#E6F7FF"))
    light_palette.setColor(QPalette.HighlightedText, QColor("#333333"))
    app.setPalette(light_palette)
    # 全局注入 QSS：确保 QComboBox 弹出列表等顶层 Popup 也能统一风格
    app.setStyleSheet(MODERN_QSS)
    window = RPAWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()