"""Foundation milestone: 3D viewport + mesh import + orbit camera + basic UI.

Run with: python -m wrap3d.app [optional/path/to/mesh.obj]
"""
from __future__ import annotations

import sys
from pathlib import Path

import imgui
import moderngl
import moderngl_window as mglw
import numpy as np
from imgui.integrations.pyglet import PygletProgrammablePipelineRenderer

from wrap3d.camera import OrbitCamera
from wrap3d.export_svg import export_panels_svg
from wrap3d.mesh import Mesh, fit_to_unit_cube, load_mesh
from wrap3d.unwrap import Panel, compute_uv_atlas, extract_panels

VERTEX_SHADER = """
#version 330
uniform mat4 mvp;
uniform mat4 model;
in vec3 in_position;
in vec3 in_normal;
out vec3 v_normal;
out vec3 v_world_pos;
void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    v_normal = mat3(model) * in_normal;
    v_world_pos = (model * vec4(in_position, 1.0)).xyz;
}
"""

FRAGMENT_SHADER = """
#version 330
uniform vec3 light_dir;
uniform vec3 base_color;
in vec3 v_normal;
in vec3 v_world_pos;
out vec4 f_color;
void main() {
    vec3 n = normalize(v_normal);
    float diffuse = max(dot(n, -normalize(light_dir)), 0.0);
    float ambient = 0.25;
    vec3 color = base_color * (ambient + diffuse * 0.75);
    f_color = vec4(color, 1.0);
}
"""


class Wrap3DViewer(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Wrap3D Prototype - Mesh Viewer"
    window_size = (1280, 800)
    aspect_ratio = None
    resizable = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera = OrbitCamera()
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )
        self.vao = None
        self.mesh: Mesh | None = None
        self.status_message = "No mesh loaded. Use File > Open or pass a path as argv[1]."
        self.wireframe = False
        self.panels: list[Panel] | None = None
        self.unwrap_status = ""

        imgui.create_context()
        self.imgui_renderer = PygletProgrammablePipelineRenderer(self.wnd._window)

        self._dragging = False
        self._panning = False
        self._last_mouse = (0.0, 0.0)

        initial_path = sys.argv[1] if len(sys.argv) > 1 else None
        if initial_path:
            self.load_mesh_from_path(initial_path)

    def load_mesh_from_path(self, path: str) -> None:
        try:
            mesh = fit_to_unit_cube(load_mesh(path))
        except Exception as exc:  # surfaced in the UI, not a crash
            self.status_message = f"Failed to load '{path}': {exc}"
            return

        self.mesh = mesh
        self.panels = None
        self.unwrap_status = ""
        self._upload_mesh(mesh)
        self.status_message = (
            f"Loaded '{Path(path).name}' — {mesh.vertex_count} verts, {mesh.face_count} tris"
        )

    def run_unwrap(self) -> None:
        if self.mesh is None:
            self.unwrap_status = "Load a mesh first."
            return
        try:
            uv = compute_uv_atlas(self.mesh)
            self.panels = extract_panels(self.mesh, uv)
            self.unwrap_status = f"Unwrapped into {len(self.panels)} panels."
        except Exception as exc:
            self.panels = None
            self.unwrap_status = f"Unwrap failed: {exc}"

    def export_svg(self, out_path: str) -> None:
        if not self.panels:
            self.unwrap_status = "Nothing to export — run Unwrap first."
            return
        try:
            export_panels_svg(self.panels, out_path)
            self.unwrap_status = f"Exported {len(self.panels)} panels to '{out_path}'."
        except Exception as exc:
            self.unwrap_status = f"Export failed: {exc}"

    def _upload_mesh(self, mesh: Mesh) -> None:
        interleaved = np.hstack([mesh.vertices, mesh.normals]).astype("f4")
        vbo = self.ctx.buffer(interleaved.tobytes())
        ibo = self.ctx.buffer(mesh.faces.astype("u4").tobytes())
        self.vao = self.ctx.vertex_array(
            self.program,
            [(vbo, "3f 3f", "in_position", "in_normal")],
            ibo,
        )

    def render(self, time: float, frametime: float) -> None:
        self.ctx.clear(0.12, 0.13, 0.15)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.wireframe = self.wireframe

        if self.vao is not None:
            aspect = self.wnd.size[0] / max(self.wnd.size[1], 1)
            model = np.identity(4, dtype="f4")
            view = np.array(self.camera.view_matrix())
            proj = np.array(self.camera.projection_matrix(aspect))
            mvp = proj @ view @ model

            self.program["mvp"].write(mvp.astype("f4").tobytes())
            self.program["model"].write(model.astype("f4").tobytes())
            self.program["light_dir"].value = (-0.4, -1.0, -0.3)
            self.program["base_color"].value = (0.65, 0.7, 0.85)
            self.vao.render()

        self._render_ui()

    def _render_ui(self) -> None:
        imgui.new_frame()
        imgui.begin("Wrap3D Prototype", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)
        imgui.text(self.status_message)
        imgui.separator()
        _, self.wireframe = imgui.checkbox("Wireframe", self.wireframe)
        if imgui.button("Reset Camera"):
            self.camera = OrbitCamera()
        imgui.text("Drag: orbit  |  Shift+Drag: pan  |  Scroll: zoom")

        imgui.separator()
        imgui.text("Unwrap")
        if imgui.button("Unwrap to Panels"):
            self.run_unwrap()
        if self.panels is not None:
            imgui.same_line()
            if imgui.button("Export SVG"):
                out_path = str(Path.cwd() / "panels.svg")
                self.export_svg(out_path)
        if self.unwrap_status:
            imgui.text_wrapped(self.unwrap_status)
        imgui.end()
        imgui.render()
        self.imgui_renderer.render(imgui.get_draw_data())

    # --- input handling -------------------------------------------------

    def mouse_press_event(self, x, y, button):
        self.imgui_renderer.mouse_press_event(x, y, button)
        if button == self.wnd.mouse.left:
            self._dragging = True
        elif button == self.wnd.mouse.right:
            self._panning = True
        self._last_mouse = (x, y)

    def mouse_release_event(self, x, y, button):
        self.imgui_renderer.mouse_release_event(x, y, button)
        self._dragging = False
        self._panning = False

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui_renderer.mouse_drag_event(x, y, dx, dy)
        if imgui.get_io().want_capture_mouse:
            return
        if self._dragging:
            self.camera.orbit(dx, -dy)
        elif self._panning:
            self.camera.pan(dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui_renderer.mouse_scroll_event(x_offset, y_offset)
        if not imgui.get_io().want_capture_mouse:
            self.camera.zoom(y_offset)

    def resize(self, width: int, height: int):
        self.imgui_renderer.resize(width, height)


def main() -> None:
    mglw.run_window_config(Wrap3DViewer)


if __name__ == "__main__":
    main()
