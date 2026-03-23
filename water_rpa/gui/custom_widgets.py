from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QLineEdit

from water_rpa.gui.dialogs import PasteConfirmDialog


def apply_light_combobox(combo: QComboBox) -> None:
    """强制下拉弹层为亮色（解决 Windows 深色模式下弹出列表黑底问题）。"""
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


class ImageLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_history: list[str] = []
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
        if not isinstance(pixmap, QPixmap):
            return

        dialog = PasteConfirmDialog(pixmap, self)
        if dialog.exec() == QDialog.Accepted:
            saved_path = dialog.get_saved_path()
            if saved_path:
                self.setText(saved_path)
                self.image_history.append(saved_path)
                self._show_preview(saved_path)

    def _show_preview(self, file_path: str) -> None:
        if os.path.exists(file_path):
            file_size_kb = os.path.getsize(file_path) / 1024
            self.setPlaceholderText(f"📷 {os.path.basename(file_path)} ({file_size_kb:.0f}KB)")

    def _is_image_file(self, file_path: str) -> bool:
        valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
        return file_path.lower().endswith(valid_extensions)

    def get_image_history(self) -> list[str]:
        return self.image_history

    def clear_history(self) -> None:
        self.image_history.clear()
