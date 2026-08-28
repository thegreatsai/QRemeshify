# Wrap3D Prototype

Standalone, from-scratch prototype of a Wrap3D-style tool: import a mesh,
view it in 3D, and (in later milestones) unwrap it into flat 2D panels or
wrap a 2D design onto its surface.

This is a separate Python prototype, unrelated to the `QRemeshify` Blender
addon that lives elsewhere in this repository.

## Milestone 1: mesh viewer + import

- Load OBJ/STL/PLY/glTF via `trimesh`
- Render with `moderngl` (shaded, wireframe toggle)
- Orbit/pan/zoom camera
- Minimal `imgui` control panel

## Milestone 2 (current): UV unwrapping + flat panel export

- Chart segmentation + parametrization via `xatlas`
- Panels recovered as UV-connected components, rescaled to true mesh-space
  size (undoing xatlas's `[0,1]` atlas packing)
- SVG export of each panel's cut outline, laid out in a simple row-packed grid
- "Unwrap to Panels" / "Export SVG" buttons in the viewer

Note: input meshes with per-triangle-duplicated vertices (e.g. raw STL) are
welded (`merge_vertices`) on load — otherwise every triangle is topologically
isolated and unwrapping produces one degenerate panel per triangle.

## Setup

```bash
cd wrap3d_prototype
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m wrap3d.app path/to/mesh.obj
```

## Milestone 3 (current): seam allowance, real packing, PDF, notches/labels

- `panel_geometry.py`: ordered boundary-loop extraction, seam allowance via
  `shapely` polygon offset (mitre join), evenly-spaced alignment notches
  along the cut edge, and a panel label anchor point
- `packing.py`: self-contained skyline bin packer (largest-area-first,
  0/90deg rotation) — used instead of the `rectpack` package, which fails
  to build in this environment (setuptools/`install_layout` incompatibility)
- `export_svg.py`: SVG export now draws the seam-allowance cut line, the
  original stitch line (dashed), notches (red ticks), and per-panel id
  labels, all packed onto a sheet via the skyline packer; `export_panels_pdf`
  tiles the same layout across fixed-size PDF pages (poster-style) via
  `reportlab`

Known limitation: the boundary-loop walker assumes each panel's cut edge is
a single simple loop. On charts with pathological topology (e.g. a boundary
vertex touching more than 2 boundary edges) the walk can produce a
self-intersecting loop; on the bundled Suzanne test model this affects 2 of
70 panels. A more robust half-edge-based boundary walk is future work if
this becomes more than a prototype.

## Roadmap

1. **Mesh viewer + import** — done
2. **UV unwrapping + flat panel export** — done
3. **Seam allowance, packing, PDF export, notches/labels** — done (this milestone)
4. Texture/decal wrapping onto the 3D surface for preview
5. Robust half-edge boundary walk; true-shape (concave) nesting
