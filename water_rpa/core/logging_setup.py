from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure file logging for the app.

    Safe to call multiple times.
    """
    root_logger = logging.getLogger()
    if getattr(root_logger, "_water_rpa_configured", False):
        return root_logger

    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(threadName)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(level)

    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    setattr(root_logger, "_water_rpa_configured", True)
    root_logger.info("Logging initialized: %s", log_file)
    return root_logger
