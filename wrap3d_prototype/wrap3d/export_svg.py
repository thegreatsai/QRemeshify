"""Export flattened panels as a single SVG, laid out in a simple grid.

This is the Wrap3D-style deliverable: cuttable/printable flat patterns.
Packing is a naive row layout for now; a real bin-packer is a later milestone.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from wrap3d.unwrap import Panel

MARGIN = 0.02  # world units between panels


def export_panels_svg(panels: list[Panel], path: str | Path, units_per_mm: float = 1.0) -> None:
    path = Path(path)

    cursor_x = 0.0
    row_y = 0.0
    row_height = 0.0
    max_row_width = 0.0
    placements: list[tuple[Panel, float, float]] = []

    row_limit = _estimate_row_limit(panels)

    for panel in panels:
        bbox_min = panel.positions_2d.min(axis=0)
        bbox_max = panel.positions_2d.max(axis=0)
        width, height = (bbox_max - bbox_min)

        if cursor_x + width > row_limit and cursor_x > 0:
            cursor_x = 0.0
            row_y += row_height + MARGIN
            row_height = 0.0

        placements.append((panel, cursor_x - bbox_min[0], row_y - bbox_min[1]))
        cursor_x += width + MARGIN
        row_height = max(row_height, height)
        max_row_width = max(max_row_width, cursor_x)

    total_width = max_row_width
    total_height = row_y + row_height

    scale = units_per_mm * 1000.0  # world units -> mm-ish, arbitrary but consistent
    svg_width = max(total_width * scale, 1.0)
    svg_height = max(total_height * scale, 1.0)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width:.2f}" '
        f'height="{svg_height:.2f}" viewBox="0 0 {svg_width:.2f} {svg_height:.2f}">'
    ]

    for panel, off_x, off_y in placements:
        edges = _boundary_edges(panel.indices)
        for a, b in edges:
            pa = panel.positions_2d[a]
            pb = panel.positions_2d[b]
            x1, y1 = (pa[0] + off_x) * scale, (pa[1] + off_y) * scale
            x2, y2 = (pb[0] + off_x) * scale, (pb[1] + off_y) * scale
            lines.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                'stroke="black" stroke-width="0.5" />'
            )

    lines.append("</svg>")
    path.write_text("\n".join(lines))


def _estimate_row_limit(panels: list[Panel]) -> float:
    if not panels:
        return 1.0
    widths = [float(np.ptp(p.positions_2d[:, 0])) for p in panels]
    return max(sum(widths) / 3.0, max(widths))


def _boundary_edges(indices: np.ndarray) -> list[tuple[int, int]]:
    """Edges that belong to exactly one triangle are the panel's cut outline."""
    edge_count: dict[tuple[int, int], int] = {}
    for tri in indices:
        for i in range(3):
            a, b = int(tri[i]), int(tri[(i + 1) % 3])
            key = (a, b) if a < b else (b, a)
            edge_count[key] = edge_count.get(key, 0) + 1
    return [edge for edge, count in edge_count.items() if count == 1]
