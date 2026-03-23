from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import pyautogui
import pyperclip

from water_rpa.config import CMD_TYPES_REV, REPO_ROOT
from water_rpa.core.actions import mouse_click, mouse_move
from water_rpa.core.models import RPATask

logger = logging.getLogger(__name__)


class RPAEngine:
    def __init__(self) -> None:
        self.is_running = False
        self.stop_requested = False

    def stop(self) -> None:
        self.stop_requested = True
        self.is_running = False

    def should_stop(self) -> bool:
        return bool(self.stop_requested)

    def _coerce_tasks(self, tasks: list[dict] | list[RPATask]) -> list[RPATask]:
        out: list[RPATask] = []
        for t in tasks:
            if isinstance(t, RPATask):
                out.append(t)
            else:
                out.append(RPATask.from_dict(t))
        return out

    def _resolve_path(self, value: str) -> str:
        p = Path(str(value).strip().strip('"'))
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        return str(p)

    def _screenshot_filename(self, folder: Path) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = folder / f"screenshot_{stamp}.png"
        if not base.exists():
            return base

        counter = 1
        while True:
            candidate = folder / f"screenshot_{stamp}_{counter}.png"
            if not candidate.exists():
                return candidate
            counter += 1

    def run_tasks(
        self,
        tasks: list[dict] | list[RPATask],
        loop_forever: bool = False,
        callback_msg: Callable[[str], None] | None = None,
    ) -> None:
        self.is_running = True
        self.stop_requested = False

        coerced_tasks = self._coerce_tasks(tasks)

        try:
            while True:
                for idx, task in enumerate(coerced_tasks):
                    if self.stop_requested:
                        if callback_msg:
                            callback_msg(">>> 🛑 任务已手动停止")
                        return

                    cmd_type = task.type
                    cmd_value = task.value
                    retry = task.retry

                    if callback_msg:
                        callback_msg(f"▶ 步骤 {idx+1}: {CMD_TYPES_REV.get(cmd_type, '未知')}")

                    try:
                        if cmd_type in (1.0, 2.0, 3.0, 8.0):
                            resolved = self._resolve_path(cmd_value)

                            if cmd_type == 1.0:
                                ok = mouse_click(1, "left", resolved, retry, self.should_stop)
                            elif cmd_type == 2.0:
                                ok = mouse_click(2, "left", resolved, retry, self.should_stop)
                            elif cmd_type == 3.0:
                                ok = mouse_click(1, "right", resolved, retry, self.should_stop)
                            else:
                                ok = mouse_move(resolved, retry, self.should_stop)

                            if not ok and callback_msg:
                                callback_msg(f"❌ 图片操作失败(超时/停止): {resolved}")

                        elif cmd_type == 4.0:
                            pyperclip.copy(str(cmd_value))
                            pyautogui.hotkey("ctrl", "v")
                            time.sleep(0.5)

                        elif cmd_type == 5.0:
                            wait_t = float(cmd_value)
                            for _ in range(int(wait_t * 10)):
                                if self.stop_requested:
                                    return
                                time.sleep(0.1)

                        elif cmd_type == 6.0:
                            pyautogui.scroll(int(cmd_value))

                        elif cmd_type == 7.0:
                            keys = [k.strip() for k in str(cmd_value).lower().split("+") if k.strip()]
                            if keys:
                                pyautogui.hotkey(*keys)

                        elif cmd_type == 9.0:
                            folder_value = str(cmd_value).strip().strip('"')
                            if not folder_value:
                                if callback_msg:
                                    callback_msg("⚠ 截图保存：目录为空，已跳过")
                                continue

                            folder = Path(folder_value)
                            if not folder.is_absolute():
                                folder = (REPO_ROOT / folder).resolve()

                            folder.mkdir(parents=True, exist_ok=True)
                            out_file = self._screenshot_filename(folder)
                            pyautogui.screenshot(str(out_file))
                            logger.info("Screenshot saved: %s", out_file)
                            if callback_msg:
                                callback_msg(f"📸 截图已保存: {out_file}")

                        else:
                            if callback_msg:
                                callback_msg(f"⚠ 未支持的指令类型: {cmd_type}")

                    except Exception:
                        logger.exception(
                            "Step failed",
                            extra={
                                "step": idx + 1,
                                "type": cmd_type,
                                "value": cmd_value,
                                "retry": retry,
                            },
                        )
                        if callback_msg:
                            callback_msg(f"⚠ 步骤 {idx+1} 执行异常，已记录日志并继续")

                if not loop_forever:
                    break
                time.sleep(0.2)

        finally:
            self.is_running = False
            if callback_msg:
                callback_msg("🏁 任务流结束")
