from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class WorkerThread(QThread):
    #信号（Signal）必须定义在类里面，而且必须写在 __init__ 的外面！
    log_signal = Signal(str)
    finished_signal = Signal() 

    def __init__(self, engine, tasks: list[dict], loop_forever: bool):
        super().__init__()
        self.engine = engine
        self.tasks = tasks
        self.loop_forever = loop_forever

    def run(self) -> None:
        self.engine.run_tasks(self.tasks, self.loop_forever, self.log_callback)
        self.finished_signal.emit() #当你调用 self.finished_signal.emit() 时，表示你正在发出 finished_signal 信号，这个信号会被所有连接到这个信号的槽函数（slot）接收并执行。并且能够传参数，可以一对多，也可以多对一，不用管connect，盲发。
    def log_callback(self, msg: str) -> None:
        self.log_signal.emit(msg)
