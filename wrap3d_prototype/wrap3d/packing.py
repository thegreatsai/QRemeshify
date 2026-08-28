"""Simple skyline bin packer for laying out panel bounding boxes on a sheet.

Not a general nesting solver (no rotation beyond 0/90deg, no concave
interlocking) — good enough for a prototype's "get panels onto a printable
sheet without wasting half of it" needs. A proper nester (true-shape
interlocking) is future work if this becomes a real product.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PackedItem:
    index: int
    x: float
    y: float
    width: float
    height: float
    rotated: bool


class SkylinePacker:
    """Classic skyline (horizontal segments) bin packer."""

    def __init__(self, sheet_width: float):
        self.sheet_width = sheet_width
        # skyline: list of (x, y, width) segments, sorted by x, covering [0, sheet_width]
        self.skyline: list[list[float]] = [[0.0, 0.0, sheet_width]]

    def insert(self, width: float, height: float, allow_rotate: bool = True) -> PackedItem | None:
        best = self._find_position(width, height)
        if allow_rotate:
            rotated = self._find_position(height, width)
            if rotated is not None and (best is None or rotated[1] < best[1]):
                best = rotated
                best_dims = (height, width)
            else:
                best_dims = (width, height)
        else:
            best_dims = (width, height)

        if best is None:
            return None

        x, y = best[0], best[1]
        w, h = best_dims
        self._update_skyline(x, y, w, h)
        return PackedItem(index=-1, x=x, y=y, width=w, height=h, rotated=best_dims != (width, height))

    def _find_position(self, width: float, height: float) -> tuple[float, float] | None:
        if width > self.sheet_width:
            return None

        best_y = None
        best_x = None
        for seg in self.skyline:
            x = seg[0]
            if x + width > self.sheet_width + 1e-6:
                continue
            y = self._height_at(x, width)
            if best_y is None or y < best_y:
                best_y = y
                best_x = x
        if best_y is None:
            return None
        return (best_x, best_y)

    def _height_at(self, x: float, width: float) -> float:
        max_y = 0.0
        remaining = width
        cursor = x
        for seg in self.skyline:
            seg_x, seg_y, seg_w = seg
            seg_end = seg_x + seg_w
            if seg_end <= cursor:
                continue
            if seg_x >= cursor + width:
                break
            max_y = max(max_y, seg_y)
            remaining -= min(seg_end, cursor + width) - max(seg_x, cursor)
        return max_y

    def _update_skyline(self, x: float, y: float, width: float, height: float) -> None:
        new_y = y + height
        new_segments: list[list[float]] = []
        placed = False
        for seg in self.skyline:
            seg_x, seg_y, seg_w = seg
            seg_end = seg_x + seg_w
            insert_start, insert_end = x, x + width

            if seg_end <= insert_start or seg_x >= insert_end:
                new_segments.append(seg)
                continue

            if seg_x < insert_start:
                new_segments.append([seg_x, seg_y, insert_start - seg_x])
            if not placed:
                new_segments.append([insert_start, new_y, width])
                placed = True
            if seg_end > insert_end:
                new_segments.append([insert_end, seg_y, seg_end - insert_end])

        if not placed:
            new_segments.append([x, new_y, width])

        new_segments.sort(key=lambda s: s[0])
        self.skyline = new_segments


def pack_boxes(
    sizes: list[tuple[float, float]], sheet_width: float, allow_rotate: bool = True
) -> list[PackedItem]:
    """Pack boxes largest-area-first onto a sheet of fixed width, unbounded height."""
    order = sorted(range(len(sizes)), key=lambda i: -(sizes[i][0] * sizes[i][1]))
    packer = SkylinePacker(sheet_width)
    results: list[PackedItem | None] = [None] * len(sizes)

    for i in order:
        w, h = sizes[i]
        item = packer.insert(w, h, allow_rotate=allow_rotate)
        if item is None:
            raise ValueError(f"item {i} ({w}x{h}) does not fit on sheet width {sheet_width}")
        item.index = i
        results[i] = item

    return results  # type: ignore[return-value]
