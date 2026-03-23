from __future__ import annotations

import os
from pathlib import Path

# Package dir = .../RPAAutoFucus/water_rpa
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Repo root = .../RPAAutoFucus
REPO_ROOT: Path = Path(BASE_DIR).resolve().parent

# Resource directories (kept at repo root to match current layout)
TEMPLATE_DIR: Path = REPO_ROOT / "template"
TEMP_MASKS_DIR: Path = REPO_ROOT / "temp_masks"

# Default folder for file dialogs (instead of os.getcwd())
DEFAULT_DIALOG_DIR: Path = REPO_ROOT

# Logs
LOG_DIR: Path = REPO_ROOT / "logs"
LOG_FILE: Path = LOG_DIR / "water_rpa.log"

# ==========================================
# Global modern QSS stylesheet
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


CMD_TYPES = {
    "左键单击": 1.0,
    "左键双击": 2.0,
    "右键单击": 3.0,
    "输入文本": 4.0,
    "等待(秒)": 5.0,
    "滚轮滑动": 6.0,
    "系统按键": 7.0,
    "鼠标悬停": 8.0,
    "截图保存": 9.0,
}

CMD_TYPES_REV = {v: k for k, v in CMD_TYPES.items()}
