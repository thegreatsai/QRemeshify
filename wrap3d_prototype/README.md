# Wrap3D Prototype

Standalone, from-scratch prototype of a Wrap3D-style tool: import a mesh,
view it in 3D, and (in later milestones) unwrap it into flat 2D panels or
wrap a 2D design onto its surface.

This is a separate Python prototype, unrelated to the `QRemeshify` Blender
addon that lives elsewhere in this repository.

## Milestone 1 (current): mesh viewer + import

- Load OBJ/STL/PLY/glTF via `trimesh`
- Render with `moderngl` (shaded, wireframe toggle)
- Orbit/pan/zoom camera
- Minimal `imgui` control panel

## Setup

```bash
cd wrap3d_prototype
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m wrap3d.app path/to/mesh.obj
```

## Roadmap

1. **Mesh viewer + import** (this milestone)
2. UV unwrapping (LSCM / ABF++ or as-rigid-as-possible parameterization)
3. Flatten to 2D panels with seam allowance, packing, and SVG/PDF export
4. Texture/decal wrapping onto the 3D surface for preview
