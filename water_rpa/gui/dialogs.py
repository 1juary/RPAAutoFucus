from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
)

from water_rpa.config import TEMPLATE_DIR


class LightMessageDialog(QDialog):
    """自绘轻量弹窗：绕开 Windows 深色模式/原生对话框导致的黑底问题。"""

    def __init__(
        self,
        parent,
        title: str,
        text: str,
        icon: QStyle.StandardPixmap,
        buttons=("OK",),
    ):
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
            for i, cap in enumerate(buttons):
                add_btn(cap, i == len(buttons) - 1)

        root.addLayout(btn_row)

    def _close_with(self, caption: str) -> None:
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


def ask_yes_no(
    parent,
    title: str,
    text: str,
    yes_text: str = "是",
    no_text: str = "否",
) -> bool:
    dlg = LightMessageDialog(parent, title, text, QStyle.SP_MessageBoxQuestion, buttons=(no_text, yes_text))
    dlg.exec()
    return dlg.result_caption == yes_text


class PasteConfirmDialog(QDialog):
    """粘贴确认对话框 - 强制白底黑字，保存截图到 template/"""

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.saved_path: str | None = None
        self.setWindowTitle("确认粘贴的图片")
        self.setFixedWidth(420)

        self.setStyleSheet(
            "QDialog { background-color: #FFFFFF; }"
            "QCheckBox { color: #333333; font-size: 13px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("✓ 截图已复制到剪贴板")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #52C41A;")
        layout.addWidget(title)

        preview_label = QLabel()
        max_preview_width = 360
        max_preview_height = 160

        if self.pixmap.width() > max_preview_width or self.pixmap.height() > max_preview_height:
            scaled = self.pixmap.scaled(
                max_preview_width,
                max_preview_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        else:
            scaled = self.pixmap

        preview_label.setPixmap(scaled)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet(
            "border: 1px solid #E0E0E0; padding: 10px; margin: 15px 0; "
            "background: #F8F9FA; border-radius: 6px;"
        )
        layout.addWidget(preview_label)

        info_label = QLabel(f"分辨率: {self.pixmap.width()} × {self.pixmap.height()} px")
        info_label.setStyleSheet("color: #666666; font-size: 13px;")
        layout.addWidget(info_label)

        self.compress_check = QCheckBox("自动压缩大于 1MB 的图片")
        self.compress_check.setChecked(True)
        self.compress_check.setStyleSheet("margin-top: 5px; margin-bottom: 15px;")
        layout.addWidget(self.compress_check)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("✕ 取消")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #666666; border: 1px solid #D9D9D9; "
            "padding: 8px 20px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { color: #1890FF; border-color: #1890FF; background-color: #F8FBFF; }"
        )
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 保存图片")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(
            "QPushButton { background-color: #1890FF; color: white; border: none; "
            "padding: 8px 20px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #40A9FF; }"
            "QPushButton:pressed { background-color: #096DD9; }"
        )
        save_btn.clicked.connect(self._save_image)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _save_image(self) -> None:
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base = TEMPLATE_DIR / f"screenshot_{timestamp}.png"

        candidate = base
        counter = 1
        while candidate.exists():
            candidate = TEMPLATE_DIR / f"screenshot_{timestamp}_{counter}.png"
            counter += 1

        pixmap = self.pixmap
        if self.compress_check.isChecked():
            file_size_mb = self.pixmap.width() * self.pixmap.height() * 4 / (1024 * 1024)
            if file_size_mb > 1:
                pixmap = self.pixmap.scaledToWidth(1920, Qt.SmoothTransformation)

        if pixmap.save(str(candidate)):
            self.saved_path = str(candidate)
            self.accept()
        else:
            show_warning(self, "✕ 错误", f"无法保存图片到 {candidate}")

    def get_saved_path(self) -> str | None:
        return self.saved_path
