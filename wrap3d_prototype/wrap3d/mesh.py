"""Mesh loading and normalization for the viewer.

Uses trimesh for broad format support (OBJ, STL, PLY, glTF, ...) and
returns plain numpy arrays so the renderer doesn't depend on trimesh's
internal types.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh


@dataclass
class Mesh:
    vertices: np.ndarray  # (N, 3) float32
    normals: np.ndarray  # (N, 3) float32
    faces: np.ndarray  # (M, 3) uint32, triangulated
    source_path: Path

    @property
    def vertex_count(self) -> int:
        return self.vertices.shape[0]

    @property
    def face_count(self) -> int:
        return self.faces.shape[0]


def load_mesh(path: str | Path) -> Mesh:
    path = Path(path)
    loaded = trimesh.load(path, force="mesh", process=False)
    if not isinstance(loaded, trimesh.Trimesh):
        raise ValueError(f"'{path}' did not load as a single triangle mesh")

    vertices = loaded.vertices.astype(np.float32)
    faces = loaded.faces.astype(np.uint32)
    normals = loaded.vertex_normals.astype(np.float32)

    return Mesh(vertices=vertices, normals=normals, faces=faces, source_path=path)


def fit_to_unit_cube(mesh: Mesh) -> Mesh:
    """Recenter and rescale so the mesh fits in a [-1, 1] cube, for consistent framing."""
    bbox_min = mesh.vertices.min(axis=0)
    bbox_max = mesh.vertices.max(axis=0)
    center = (bbox_min + bbox_max) / 2.0
    extent = (bbox_max - bbox_min).max()
    scale = 2.0 / extent if extent > 0 else 1.0

    centered = (mesh.vertices - center) * scale
    return Mesh(
        vertices=centered.astype(np.float32),
        normals=mesh.normals,
        faces=mesh.faces,
        source_path=mesh.source_path,
    )
