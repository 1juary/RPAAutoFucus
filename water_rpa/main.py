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
    setup_logging(config.LOG_FILE)
    logger = logging.getLogger(__name__)

    def _excepthook(exc_type, exc, tb):
        logger.exception("Unhandled exception", exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook

    app = QApplication(sys.argv)

    # app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_DontUseNativeDialogs)

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

    app.setStyleSheet(MODERN_QSS)

    window = RPAWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
