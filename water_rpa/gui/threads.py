from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class WorkerThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, engine, tasks: list[dict], loop_forever: bool):
        super().__init__()
        self.engine = engine
        self.tasks = tasks
        self.loop_forever = loop_forever

    def run(self) -> None:
        self.engine.run_tasks(self.tasks, self.loop_forever, self.log_callback)
        self.finished_signal.emit()

    def log_callback(self, msg: str) -> None:
        self.log_signal.emit(msg)
