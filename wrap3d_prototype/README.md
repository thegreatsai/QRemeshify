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

## Roadmap

1. **Mesh viewer + import** — done
2. **UV unwrapping + flat panel export** — done (this milestone)
3. Seam allowance, proper bin-packing, PDF export, panel labeling/notches
4. Texture/decal wrapping onto the 3D surface for preview
