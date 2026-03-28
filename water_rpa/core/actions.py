from __future__ import annotations

import logging
import time
from typing import Callable #Callable 是一个类型提示工具，用于表示一个可调用对象（如函数）的类型。在这个代码中，Callable[[], bool] 表示一个不接受任何参数并返回布尔值的函数类型。这种类型提示有助于提高代码的可读性和可维护性，让开发者更清楚地了解函数的预期输入和输出。

import pyautogui

from water_rpa.core.vision import _process_red_box_logic

logger = logging.getLogger(__name__) #logging.getLogger(__name__) 会返回一个与当前模块名称相同的 Logger 对象。这种做法有助于在大型项目中更好地组织和管理日志输出，使得每个模块都可以独立地记录日志，并且可以根据需要配置不同的日志级别和处理器。


def _should_log_exception(last_ts: float, min_interval_s: float = 2.0) -> bool: #_内部函数，仅限内部使用建议不要import使用
    return (time.time() - last_ts) >= min_interval_s


def mouse_click(
    click_times: int,
    left_or_right: str,
    img_path: str,
    retry: int,
    should_stop: Callable[[], bool], #类型为 Callable[[], bool]，表示这是一个不用传入任何参数，并返回布尔值的函数指的should_stop。不传变量是因为，除了再次更新变量，不然不会主动更新状态，但是被传入的函数参数是可以自己return的，业务被分离了。
    timeout: float = 30, #默认等待时间
) -> bool:
    """Locate `img_path` on screen and click at red-box offset (if present)."""
    start_time = time.time()
    last_exc_log_ts = 0.0 #记录上次日志记录的时间戳，初始值为0.0。

    has_red, off_x, off_y, search_img = _process_red_box_logic(img_path)

    def remaining_time() -> float:
        if not timeout:
            return float("inf") #如果没有设置超时时间（timeout为0或None），则返回正无穷大，表示永远不会超时。
        return max(0.0, timeout - (time.time() - start_time)) #计算剩余时间，确保不会返回负值。

    def locate_target():
        nonlocal last_exc_log_ts #nonlocal 关键字用于在函数内部声明一个变量是来自外部作用域的（但不是全局作用域）。
        try:
            return pyautogui.locateOnScreen(search_img, confidence=0.8)
        except Exception:
            if _should_log_exception(last_exc_log_ts):
                last_exc_log_ts = time.time() #更新上次日志记录的时间戳为当前时间，以便下次发生异常时能够判断是否需要记录日志。
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

    def wait_slice() -> None: # wait_slice函数是一个简单的工具函数，用于在执行过程中引入短暂的延迟。
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
                # 注意：这里没有 return True，因为 retry=-1 表示无限重试，只有在 should_stop() 或 timeout 触发时才会退出循环。
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
