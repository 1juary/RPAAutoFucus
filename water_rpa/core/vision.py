from __future__ import annotations

import logging
import os

from PIL import Image as PILImage

from water_rpa.config import TEMP_MASKS_DIR

logger = logging.getLogger(__name__)


def _process_red_box_logic(img_path: str) -> tuple[bool, int, int, str]:
    """
    1) 扫描红色像素并透明化红框区域，避免特征匹配失败
    2) 对红色像素进行简单聚类，锁定像素最多的红框

    Returns:
        (has_red, offset_x, offset_y, search_path)
    """
    has_red = False
    offset_x, offset_y = 0, 0
    search_path = img_path

    try:
        source_img = PILImage.open(img_path).convert("RGBA")
        width, height = source_img.size
        pixels = source_img.load()

        red_pixels: list[tuple[int, int]] = []
        search_img = source_img.copy()
        search_pixels = search_img.load()

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if r > 180 and r > g * 2.5 and r > b * 2.5:
                    red_pixels.append((x, y))
                    search_pixels[x, y] = (0, 0, 0, 0)

        if len(red_pixels) > 10:
            clusters: list[dict[str, object]] = []
            threshold = 20

            for px, py in red_pixels:
                found_cluster = False
                for cluster in clusters:
                    min_x = cluster["min_x"]
                    max_x = cluster["max_x"]
                    min_y = cluster["min_y"]
                    max_y = cluster["max_y"]
                    if (
                        min_x - threshold <= px <= max_x + threshold
                        and min_y - threshold <= py <= max_y + threshold
                    ):
                        cluster["pts"].append((px, py))
                        cluster["min_x"] = min(min_x, px)
                        cluster["max_x"] = max(max_x, px)
                        cluster["min_y"] = min(min_y, py)
                        cluster["max_y"] = max(max_y, py)
                        found_cluster = True
                        break

                if not found_cluster:
                    clusters.append(
                        {
                            "pts": [(px, py)],
                            "min_x": px,
                            "max_x": px,
                            "min_y": py,
                            "max_y": py,
                        }
                    )

            if clusters:
                target_cluster = max(clusters, key=lambda c: len(c["pts"]))
                if len(target_cluster["pts"]) > 10:
                    has_red = True
                    offset_x = (target_cluster["min_x"] + target_cluster["max_x"]) // 2
                    offset_y = (target_cluster["min_y"] + target_cluster["max_y"]) // 2

                    TEMP_MASKS_DIR.mkdir(parents=True, exist_ok=True)
                    search_path = str(
                        (TEMP_MASKS_DIR / f"search_{os.path.basename(img_path)}").resolve()
                    )
                    search_img.save(search_path)

    except Exception:
        logger.exception("红框深度解析异常")

    return has_red, offset_x, offset_y, search_path
