from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from water_rpa.config import CMD_TYPES, CMD_TYPES_REV, DEFAULT_DIALOG_DIR
from water_rpa.gui.custom_widgets import ImageLineEdit, apply_light_combobox
from water_rpa.gui.dialogs import ask_yes_no, show_info


class TaskRow(QFrame):
    """任务行组件：操作类型 + 参数输入 + 缩略图预览 + 重试次数 + 排序/删除。"""

    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName("taskCard")

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        self.layout.setSpacing(8)

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

        from PySide6.QtWidgets import QComboBox  # local import to keep list short

        self.type_combo = QComboBox()
        self.type_combo.addItems(list(CMD_TYPES.keys()))
        self.type_combo.setFixedWidth(105)
        apply_light_combobox(self.type_combo)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.layout.addWidget(self.type_combo)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(64, 42)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setText("No Img")
        self.thumb_label.setStyleSheet(
            "QLabel { background-color: #F0F2F5; border: 1px solid #D9D9D9; border-radius: 3px; "
            "color: #999; font-size: 10px; font-weight: bold; }"
        )
        self.layout.addWidget(self.thumb_label)

        self.value_input = ImageLineEdit()
        self.value_input.setPlaceholderText("参数值 (支持任何颜色的框选定位)")
        self.value_input.textChanged.connect(self.update_thumbnail)
        self.layout.addWidget(self.value_input)

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

        self.del_btn = QPushButton("✖")
        self.del_btn.setObjectName("deleteBtn")
        self.del_btn.setFixedSize(32, 32)
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        self.layout.addWidget(self.del_btn)

        self.on_type_changed(self.type_combo.currentText())

    def update_thumbnail(self) -> None:
        path = self.value_input.text().strip().replace('"', "")

        if os.path.exists(path) and path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.thumb_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.thumb_label.setPixmap(scaled)
                self.thumb_label.setToolTip(f"完整路径: {os.path.abspath(path)}")
                return

        self.thumb_label.clear()
        self.thumb_label.setText("No Img")
        self.thumb_label.setToolTip("")

    def on_type_changed(self, text: str) -> None:
        cmd_type = CMD_TYPES[text]
        is_img = cmd_type in [1.0, 2.0, 3.0, 8.0]

        self.thumb_label.setVisible(is_img)
        self.file_btn.setVisible(is_img or cmd_type == 9.0)
        self.retry_input.setVisible(is_img)
        self.history_btn.setVisible(is_img)

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

    def select_file(self) -> None:
        cmd_type = CMD_TYPES[self.type_combo.currentText()]
        default_dir = str(DEFAULT_DIALOG_DIR)

        if cmd_type == 9.0:
            folder = QFileDialog.getExistingDirectory(self, "选择保存目录", default_dir)
            if folder:
                self.value_input.setText(folder)
        else:
            file, _ = QFileDialog.getOpenFileName(
                self, "选择图片", default_dir, "图片 (*.png *.jpg *.jpeg *.bmp)"
            )
            if file:
                self.value_input.setText(file)

    def show_image_history(self) -> None:
        history = self.value_input.get_image_history()
        if not history:
            show_info(self, "提示", "本行暂无图片粘贴记录")
            return

        msg = "📋 图片历史 (按时间排序):\n\n"
        for i, p in enumerate(history, 1):
            msg += f"{i}. {os.path.basename(p)}\n"

        if ask_yes_no(self, "历史记录", msg + "\n是否重新加载最后一次截图？"):
            self.value_input.setText(history[-1])

    def set_data(self, data: dict) -> None:
        cmd_type = data.get("type", 1.0)
        self.type_combo.setCurrentText(CMD_TYPES_REV.get(cmd_type, "左键单击"))
        self.value_input.setText(str(data.get("value", "")))
        self.retry_input.setText(str(data.get("retry", "1")))
        self.update_thumbnail()

    def get_data(self) -> dict:
        retry_text = self.retry_input.text()
        retry = 1
        if retry_text.isdigit() or retry_text == "-1":
            try:
                retry = int(retry_text)
            except Exception:
                retry = 1

        return {
            "type": CMD_TYPES[self.type_combo.currentText()],
            "value": self.value_input.text().strip(),
            "retry": retry,
        }
