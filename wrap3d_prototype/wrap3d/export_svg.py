"""Export flattened panels (with seam allowance + notches) to SVG/PDF sheets,
laid out via the skyline packer.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from wrap3d.packing import pack_boxes
from wrap3d.panel_geometry import PanelOutline, build_panel_outline
from wrap3d.unwrap import Panel

MM_PER_UNIT = 1000.0  # world units -> mm, arbitrary but consistent across exports


def build_layout(
    panels: list[Panel],
    seam_allowance: float = 0.0,
    notch_spacing: float | None = None,
    sheet_width_units: float = 3.0,
) -> tuple[list[PanelOutline], list[tuple[float, float]]]:
    """Compute panel outlines and their packed (x, y) offsets on the sheet."""
    outlines = [
        build_panel_outline(p, seam_allowance=seam_allowance, notch_spacing=notch_spacing)
        for p in panels
    ]

    sizes = []
    for outline in outlines:
        bbox_min = outline.offset_boundary.min(axis=0)
        bbox_max = outline.offset_boundary.max(axis=0)
        sizes.append(tuple(bbox_max - bbox_min))

    packed = pack_boxes(sizes, sheet_width=sheet_width_units, allow_rotate=True)

    offsets: list[tuple[float, float]] = [(0.0, 0.0)] * len(outlines)
    for item in packed:
        bbox_min = outlines[item.index].offset_boundary.min(axis=0)
        offsets[item.index] = (item.x - bbox_min[0], item.y - bbox_min[1])

    return outlines, offsets


def export_panels_svg(
    panels: list[Panel],
    path: str | Path,
    seam_allowance: float = 0.0,
    notch_spacing: float | None = None,
) -> None:
    path = Path(path)
    outlines, offsets = build_layout(panels, seam_allowance, notch_spacing)
    scale = MM_PER_UNIT

    max_x = 0.0
    max_y = 0.0
    body: list[str] = []

    for outline, (off_x, off_y) in zip(outlines, offsets):
        cut = _to_svg_polyline(outline.offset_boundary, off_x, off_y, scale)
        stitch = _to_svg_polyline(outline.boundary, off_x, off_y, scale, closed=True)
        body.append(f'<polygon points="{cut}" fill="none" stroke="black" stroke-width="0.5" />')
        if outline.offset_boundary is not outline.boundary:
            body.append(
                f'<polygon points="{stitch}" fill="none" stroke="#999" '
                'stroke-width="0.3" stroke-dasharray="2,2" />'
            )
        for notch in outline.notches:
            (x1, y1), (x2, y2) = notch
            body.append(
                f'<line x1="{(x1 + off_x) * scale:.2f}" y1="{(y1 + off_y) * scale:.2f}" '
                f'x2="{(x2 + off_x) * scale:.2f}" y2="{(y2 + off_y) * scale:.2f}" '
                'stroke="red" stroke-width="0.5" />'
            )
        lx, ly = (outline.label_position[0] + off_x) * scale, (outline.label_position[1] + off_y) * scale
        body.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" font-size="10" text-anchor="middle">'
            f"{outline.chart_id}</text>"
        )

        bbox_max = outline.offset_boundary.max(axis=0)
        max_x = max(max_x, (bbox_max[0] + off_x) * scale)
        max_y = max(max_y, (bbox_max[1] + off_y) * scale)

    header = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x:.2f}" height="{max_y:.2f}" '
        f'viewBox="0 0 {max_x:.2f} {max_y:.2f}">'
    )
    path.write_text("\n".join([header, *body, "</svg>"]))


def export_panels_pdf(
    panels: list[Panel],
    path: str | Path,
    seam_allowance: float = 0.0,
    notch_spacing: float | None = None,
    page_width_mm: float = 800.0,
    page_height_mm: float = 1200.0,
) -> None:
    """Export panels across one or more fixed-size PDF pages (poster-tiled).

    Raises ValueError if a single panel's bounding box is wider than page_width_mm
    — either enlarge page_width_mm or rescale the source mesh before unwrapping.
    """
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    path = Path(path)
    sheet_width_units = page_width_mm / MM_PER_UNIT
    try:
        outlines, offsets = build_layout(
            panels, seam_allowance, notch_spacing, sheet_width_units=sheet_width_units
        )
    except ValueError as exc:
        raise ValueError(
            f"{exc}. Increase page_width_mm (currently {page_width_mm}mm) to fit the "
            "largest panel, or rescale the mesh before unwrapping."
        ) from exc
    scale = MM_PER_UNIT

    page_height_units = page_height_mm / MM_PER_UNIT
    c = canvas.Canvas(str(path), pagesize=(page_width_mm * mm, page_height_mm * mm))

    max_y = max(
        (o.offset_boundary.max(axis=0)[1] + off_y) for o, (_, off_y) in zip(outlines, offsets)
    )
    n_pages = max(1, int(np.ceil(max_y / page_height_units)))

    for page in range(n_pages):
        page_y_min = page * page_height_units
        for outline, (off_x, off_y) in zip(outlines, offsets):
            _draw_pdf_panel(c, outline, off_x, off_y, page_y_min, scale, mm)
        c.showPage()

    c.save()


def _draw_pdf_panel(canvas_obj, outline, off_x, off_y, page_y_min, scale, mm_unit) -> None:
    def to_page(pt: np.ndarray) -> tuple[float, float]:
        x = (pt[0] + off_x) * scale
        y = (pt[1] + off_y - page_y_min) * scale
        return x * mm_unit, y * mm_unit

    pts = [to_page(p) for p in outline.offset_boundary]
    if not pts:
        return
    path = canvas_obj.beginPath()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()
    canvas_obj.setLineWidth(0.5)
    canvas_obj.drawPath(path, stroke=1, fill=0)

    for notch in outline.notches:
        (x1, y1), (x2, y2) = to_page(notch[0]), to_page(notch[1])
        canvas_obj.setStrokeColorRGB(1, 0, 0)
        canvas_obj.line(x1, y1, x2, y2)
        canvas_obj.setStrokeColorRGB(0, 0, 0)

    lx, ly = to_page(outline.label_position)
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawCentredString(lx, ly, str(outline.chart_id))


def _to_svg_polyline(
    points: np.ndarray, off_x: float, off_y: float, scale: float, closed: bool = False
) -> str:
    coords = [(p[0] + off_x) * scale for p in points], [(p[1] + off_y) * scale for p in points]
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in zip(*coords))
