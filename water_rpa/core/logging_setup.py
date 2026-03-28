from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure file logging for the app.

    Safe to call multiple times.
    """
    root_logger = logging.getLogger()  #官方自带类，原本是没有"_water_rpa_configured"这个属性的，现在我们给它贴了个标签，值是True，表示已经配置过了。下次再调用setup_logging时，就会通过getattr检查到这个标签，知道已经配置过了，就不会重复配置了。
    if getattr(root_logger, "_water_rpa_configured", False): #getattr(目标对象, "要找的属性名", 找不到时的备用答案)
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

    setattr(root_logger, "_water_rpa_configured", True)  #setattr(目标对象, "你要贴的标签名字", 你要写在标签上的值)，原来是没有"_water_rpa_configured"这个属性的，现在贴了个标签，值是True，表示已经配置过了。下次再调用setup_logging时，就会通过getattr检查到这个标签，知道已经配置过了，就不会重复配置了。
    root_logger.info("Logging initialized: %s", log_file)
    return root_logger
