"""Panel outline extraction, seam allowance, and alignment notches.

Operates on a Panel's flattened triangulation (wrap3d.unwrap.Panel) and
produces the ordered boundary loop(s) a cutter/printer actually needs.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import Polygon
from shapely.validation import make_valid

from wrap3d.unwrap import Panel


@dataclass
class PanelOutline:
    chart_id: int
    boundary: np.ndarray  # (K, 2) float32, ordered loop, no seam allowance
    offset_boundary: np.ndarray  # (K', 2) float32, boundary grown by seam_allowance
    notches: list[np.ndarray] = field(default_factory=list)  # small tick marks, world units
    label_position: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))


def _ordered_boundary_loops(indices: np.ndarray) -> list[list[int]]:
    """Walk boundary edges (edges used by exactly one triangle) into ordered loops."""
    edge_count: dict[tuple[int, int], int] = {}
    for tri in indices:
        for i in range(3):
            a, b = int(tri[i]), int(tri[(i + 1) % 3])
            key = (a, b) if a < b else (b, a)
            edge_count[key] = edge_count.get(key, 0) + 1

    boundary_edges = [e for e, c in edge_count.items() if c == 1]
    adjacency: dict[int, list[int]] = {}
    for a, b in boundary_edges:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    visited_edges: set[tuple[int, int]] = set()
    loops: list[list[int]] = []

    for start in list(adjacency.keys()):
        for neighbor in list(adjacency.get(start, [])):
            edge_key = (start, neighbor) if start < neighbor else (neighbor, start)
            if edge_key in visited_edges:
                continue
            loop = [start]
            prev, current = start, neighbor
            visited_edges.add(edge_key)
            while current != start:
                loop.append(current)
                next_candidates = [n for n in adjacency.get(current, []) if n != prev]
                if not next_candidates:
                    break
                nxt = next_candidates[0]
                key = (current, nxt) if current < nxt else (nxt, current)
                if key in visited_edges:
                    break
                visited_edges.add(key)
                prev, current = current, nxt
            if len(loop) >= 3:
                loops.append(loop)

    return loops


def build_panel_outline(
    panel: Panel, seam_allowance: float = 0.0, notch_spacing: float | None = None
) -> PanelOutline:
    loops = _ordered_boundary_loops(panel.indices)
    if not loops:
        raise ValueError(f"panel {panel.chart_id} has no boundary loop (degenerate)")

    # The outer loop is the one enclosing the largest area; inner loops (holes)
    # are ignored for now since flat-pattern export cares mainly about the cut edge.
    loop_areas = []
    for loop in loops:
        pts = panel.positions_2d[loop]
        loop_areas.append(abs(_polygon_area(pts)))
    outer_loop = loops[int(np.argmax(loop_areas))]
    boundary = panel.positions_2d[outer_loop].astype(np.float32)

    offset_boundary = boundary
    if seam_allowance > 0:
        offset_boundary = _offset_polygon(boundary, seam_allowance)

    notches: list[np.ndarray] = []
    if notch_spacing and notch_spacing > 0:
        notches = _place_notches(boundary, notch_spacing)

    label_position = boundary.mean(axis=0).astype(np.float32)

    return PanelOutline(
        chart_id=panel.chart_id,
        boundary=boundary,
        offset_boundary=offset_boundary,
        notches=notches,
        label_position=label_position,
    )


def _polygon_area(points: np.ndarray) -> float:
    x, y = points[:, 0], points[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def _offset_polygon(boundary: np.ndarray, distance: float) -> np.ndarray:
    poly = Polygon(boundary)
    if not poly.is_valid:
        poly = make_valid(poly)
    grown = poly.buffer(distance, join_style="mitre", mitre_limit=3.0)
    if grown.is_empty:
        return boundary
    # buffer() can return a MultiPolygon for pathological shapes; keep the largest part.
    if grown.geom_type == "MultiPolygon":
        grown = max(grown.geoms, key=lambda g: g.area)
    coords = np.array(grown.exterior.coords, dtype=np.float32)
    return coords


def _place_notches(boundary: np.ndarray, spacing: float) -> list[np.ndarray]:
    """Small perpendicular tick marks along the boundary, spaced by arc length,
    for aligning adjacent panels when reassembling the physical piece."""
    notches: list[np.ndarray] = []
    n = len(boundary)
    accumulated = 0.0
    tick_length = spacing * 0.15

    for i in range(n):
        a = boundary[i]
        b = boundary[(i + 1) % n]
        seg = b - a
        seg_len = float(np.linalg.norm(seg))
        if seg_len < 1e-9:
            continue
        direction = seg / seg_len
        normal = np.array([-direction[1], direction[0]], dtype=np.float32)

        pos_along = spacing - (accumulated % spacing)
        while pos_along < seg_len:
            point = a + direction * pos_along
            notches.append(np.array([point, point + normal * tick_length], dtype=np.float32))
            pos_along += spacing
        accumulated += seg_len

    return notches
