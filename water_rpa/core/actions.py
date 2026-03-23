from __future__ import annotations

import logging
import time
from typing import Callable

import pyautogui

from water_rpa.core.vision import _process_red_box_logic

logger = logging.getLogger(__name__)


def _should_log_exception(last_ts: float, min_interval_s: float = 2.0) -> bool:
    return (time.time() - last_ts) >= min_interval_s


def mouse_click(
    click_times: int,
    left_or_right: str,
    img_path: str,
    retry: int,
    should_stop: Callable[[], bool],
    timeout: float = 60,
) -> bool:
    """Locate `img_path` on screen and click at red-box offset (if present)."""
    start_time = time.time()
    last_exc_log_ts = 0.0

    has_red, off_x, off_y, search_img = _process_red_box_logic(img_path)

    def remaining_time() -> float:
        if not timeout:
            return float("inf")
        return max(0.0, timeout - (time.time() - start_time))

    def locate_target():
        nonlocal last_exc_log_ts
        try:
            return pyautogui.locateOnScreen(search_img, confidence=0.8)
        except Exception:
            if _should_log_exception(last_exc_log_ts):
                last_exc_log_ts = time.time()
                logger.exception("locateOnScreen failed")
            return None

    def click_at(box) -> None:
        if has_red:
            target_x = box.left + off_x
            target_y = box.top + off_y
        else:
            target_x = box.left + box.width / 2
            target_y = box.top + box.height / 2

        pyautogui.click(
            target_x,
            target_y,
            clicks=click_times,
            interval=0.2,
            duration=0.2,
            button=left_or_right,
        )

    def wait_slice() -> None:
        time.sleep(0.2)

    if retry == 1:
        while True:
            if should_stop():
                return False
            if remaining_time() <= 0:
                return False

            box = locate_target()
            if box is not None:
                click_at(box)
                return True

            wait_slice()

    if retry == -1:
        while True:
            if should_stop():
                return False
            if remaining_time() <= 0:
                return False

            box = locate_target()
            if box is not None:
                click_at(box)

            wait_slice()

    if retry <= 0:
        retry = 1

    completed = 0
    while completed < retry:
        if should_stop():
            return False
        if remaining_time() <= 0:
            return False

        box = locate_target()
        if box is not None:
            click_at(box)
            completed += 1
        else:
            wait_slice()

    return True


def mouse_move(
    img_path: str,
    retry: int,
    should_stop: Callable[[], bool],
    timeout: float = 60,
) -> bool:
    """Locate `img_path` on screen and move to red-box offset (if present)."""
    start_time = time.time()
    last_exc_log_ts = 0.0
    has_red, off_x, off_y, search_img = _process_red_box_logic(img_path)

    def remaining_time() -> float:
        if not timeout:
            return float("inf")
        return max(0.0, timeout - (time.time() - start_time))

    def locate_target():
        nonlocal last_exc_log_ts
        try:
            return pyautogui.locateOnScreen(search_img, confidence=0.8)
        except Exception:
            if _should_log_exception(last_exc_log_ts):
                last_exc_log_ts = time.time()
                logger.exception("locateOnScreen failed")
            return None

    def move_to(box) -> None:
        tx = box.left + off_x if has_red else box.left + box.width / 2
        ty = box.top + off_y if has_red else box.top + box.height / 2
        pyautogui.moveTo(tx, ty, duration=0.2)

    def wait_slice() -> None:
        time.sleep(0.2)

    if retry == 1:
        while True:
            if should_stop():
                return False
            if remaining_time() <= 0:
                return False

            box = locate_target()
            if box is not None:
                move_to(box)
                return True

            wait_slice()

    if retry == -1:
        while True:
            if should_stop():
                return False
            if remaining_time() <= 0:
                return False

            box = locate_target()
            if box is not None:
                move_to(box)

            wait_slice()

    if retry <= 0:
        retry = 1

    completed = 0
    while completed < retry:
        if should_stop():
            return False
        if remaining_time() <= 0:
            return False

        box = locate_target()
        if box is not None:
            move_to(box)
            completed += 1
        else:
            wait_slice()

    return True
