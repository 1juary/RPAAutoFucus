from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from water_rpa.config import DEFAULT_DIALOG_DIR, MODERN_QSS
from water_rpa.core.engine import RPAEngine
from water_rpa.gui.components import TaskRow
from water_rpa.gui.custom_widgets import apply_light_combobox
from water_rpa.gui.dialogs import show_error, show_warning
from water_rpa.gui.threads import WorkerThread


class RPAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPA 精致自动化工具")
        self.resize(900, 650)
        self.setStyleSheet(MODERN_QSS)

        self.engine = RPAEngine()
        self.worker: WorkerThread | None = None
        self.rows: list[TaskRow] = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

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

        top_bar.addStretch()

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.task_container = QWidget()
        self.task_container.setStyleSheet("background-color: transparent;")

        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 10, 0)
        self.task_layout.setSpacing(5)
        self.task_layout.addStretch()

        scroll.setWidget(self.task_container)
        main_layout.addWidget(scroll, stretch=3)

        log_label = QLabel("运行日志 (Log):")
        log_label.setStyleSheet("color: #666; font-weight: bold;")
        main_layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(180)
        main_layout.addWidget(self.log_area, stretch=1)

        self.add_row()

    def add_row(self, data: dict | None = None) -> None:
        self.task_layout.takeAt(self.task_layout.count() - 1)

        row_widget = TaskRow()
        if data:
            row_widget.set_data(data)

        row_widget.delete_requested.connect(self.delete_row)
        row_widget.move_up_requested.connect(self.move_up)
        row_widget.move_down_requested.connect(self.move_down)

        self.task_layout.addWidget(row_widget)
        self.rows.append(row_widget)

        self.task_layout.addStretch()

    def delete_row(self, row_widget: TaskRow) -> None:
        if row_widget in self.rows:
            self.task_layout.removeWidget(row_widget)
            self.rows.remove(row_widget)
            row_widget.deleteLater()

    def move_up(self, row_widget: TaskRow) -> None:
        idx = self.task_layout.indexOf(row_widget)
        if idx > 0:
            self.task_layout.removeWidget(row_widget)
            self.task_layout.insertWidget(idx - 1, row_widget)
            self.rows.remove(row_widget)
            self.rows.insert(idx - 1, row_widget)

    def move_down(self, row_widget: TaskRow) -> None:
        idx = self.task_layout.indexOf(row_widget)
        if idx < self.task_layout.count() - 2:
            self.task_layout.removeWidget(row_widget)
            self.task_layout.insertWidget(idx + 1, row_widget)
            self.rows.remove(row_widget)
            self.rows.insert(idx + 1, row_widget)

    def _get_ordered_tasks(self) -> list[dict]:
        tasks: list[dict] = []
        for i in range(self.task_layout.count() - 1):
            widget = self.task_layout.itemAt(i).widget()
            if isinstance(widget, TaskRow):
                tasks.append(widget.get_data())
        return tasks

    def save_config(self) -> None:
        tasks = self._get_ordered_tasks()
        if not tasks:
            show_warning(self, "警告", "没有可保存的配置")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存配置",
            str(DEFAULT_DIALOG_DIR),
            "JSON Files (*.json);;Text Files (*.txt)",
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, indent=4, ensure_ascii=False)
                self.log("配置已保存到：" + filename)
            except Exception as exc:
                show_error(self, "错误", f"保存失败: {exc}")

    def load_config(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "导入配置",
            str(DEFAULT_DIALOG_DIR),
            "JSON Files (*.json);;Text Files (*.txt)",
        )
        if not filename:
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            if not isinstance(tasks, list):
                raise ValueError("文件格式不正确")

            for row in list(self.rows):
                self.delete_row(row)

            for task in tasks:
                self.add_row(task)
            self.log(f"成功导入 {len(tasks)} 条指令！")

        except Exception as exc:
            show_error(self, "错误", f"导入失败: {exc}")

    def start_task(self) -> None:
        tasks = self._get_ordered_tasks()

        for data in tasks:
            if not data.get("value"):
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

        loop = self.loop_check.currentText() == "循环执行"

        self.worker = WorkerThread(self.engine, tasks, loop)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

        if self.minimize_check.isChecked():
            self.showMinimized()

    def stop_task(self) -> None:
        self.engine.stop()
        self.log("⏸ 正在发出停止请求...")

    def on_finished(self) -> None:
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_btn.setEnabled(True)

        if self.minimize_check.isChecked() or self.isMinimized():
            self.showNormal()
            self.activateWindow()

    def log(self, msg: str) -> None:
        self.log_area.append(msg)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.engine.stop()
            self.worker.quit()
            self.worker.wait()
        event.accept()
