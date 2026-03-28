from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from water_rpa import config
from water_rpa.config import MODERN_QSS
from water_rpa.core.logging_setup import setup_logging
from water_rpa.gui.app_window import RPAWindow


def main() -> None:
    setup_logging(config.LOG_FILE) #以后所有的底层错误，都写进config.LOG_FILE指定的日志文件里，方便排查问题。并且在gui界面上也会显示出来。
    logger = logging.getLogger(__name__) #在各个功能文件来获取一个与当前模块名称相同的 Logger 对象，这样就可以在日志中清楚地看到每条日志来自哪个模块。__name__ 是一个特殊变量，表示当前模块的名称。main.py 的 __name__ 是 "main"。

    def _excepthook(exc_type, exc, tb): 
        logger.exception("Unhandled exception", exc_info=(exc_type, exc, tb)) #记录下异常，并打包放进.log文件里面
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook 

    app = QApplication(sys.argv) #创建一个QApplication对象，负责管理应用程序的控制流和主要设置。它是所有Qt应用程序的基础，必须在创建任何其他Qt对象之前创建。

    # app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_DontUseNativeDialogs) #禁用原生对话框，使用Qt自带的对话框。这可以确保在不同平台上有一致的用户界面体验，避免原生对话框可能带来的兼容性问题。

    app.setStyle("Fusion") #Fusion是一种什么样的风格？  Fusion是一种跨平台的Qt风格，提供了一致的外观和感觉。
    light_palette = QPalette() #Palette 调色盘
    light_palette.setColor(QPalette.Window, QColor("#F0F2F5")) #setColor是实例方法
    light_palette.setColor(QPalette.WindowText, QColor("#333333"))
    light_palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    light_palette.setColor(QPalette.AlternateBase, QColor("#FAFAFA"))
    light_palette.setColor(QPalette.Text, QColor("#333333"))
    light_palette.setColor(QPalette.Button, QColor("#FFFFFF"))
    light_palette.setColor(QPalette.ButtonText, QColor("#333333"))
    light_palette.setColor(QPalette.Highlight, QColor("#E6F7FF"))
    light_palette.setColor(QPalette.HighlightedText, QColor("#333333"))
    app.setPalette(light_palette) 

    app.setStyleSheet(MODERN_QSS)

    window = RPAWindow()
    window.show()
    sys.exit(app.exec()) #app.exec()进入Qt的事件循环，等待用户交互和其他事件的发生。直到你点击了窗口右上角的“✖”关闭按钮，接待员下班（app.exec() 结束并返回一个退出代码，比如 0），然后最外层的 sys.exit(0) 接收到这个代码，正式把整个程序关掉。


if __name__ == "__main__":#__name__ 是一个系统自带的隐藏变量。直接运行当前代码会启动下面行，如果被其他代码导入，则不会执行下面行。
    main()
