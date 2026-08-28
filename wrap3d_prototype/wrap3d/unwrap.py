"""UV unwrapping: segment a mesh into charts and flatten them to 2D panels.

Wraps xatlas (chart segmentation + LSCM-style parametrization + packing)
and reorganizes the result into per-chart panels, which is the unit
Wrap3D-style flat-pattern export actually operates on.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xatlas

from wrap3d.mesh import Mesh


@dataclass
class UVResult:
    vertices: np.ndarray  # (N', 3) float32, remapped from source mesh (charts can split verts)
    uvs: np.ndarray  # (N', 2) float32, packed atlas UVs in [0, 1]
    indices: np.ndarray  # (M, 3) uint32, into vertices/uvs


@dataclass
class Panel:
    """A single flattened chart, in its own local 2D coordinate space (not atlas-packed)."""

    chart_id: int
    positions_2d: np.ndarray  # (K, 2) float32, local flattened coords, mesh-scale units
    indices: np.ndarray  # (T, 3) uint32, into positions_2d
    source_vertex_ids: np.ndarray  # (K,) uint32, index into original mesh.vertices


def compute_uv_atlas(mesh: Mesh) -> UVResult:
    vmapping, indices, uvs = xatlas.parametrize(mesh.vertices, mesh.faces)
    vertices = mesh.vertices[vmapping]
    return UVResult(
        vertices=vertices.astype(np.float32),
        uvs=uvs.astype(np.float32),
        indices=indices.astype(np.uint32),
    )


def extract_panels(mesh: Mesh, uv: UVResult) -> list[Panel]:
    """Split the packed atlas into per-chart panels, each rescaled to real mesh-space
    dimensions (undoing xatlas's [0,1] packing) so exported panels are true to size.
    """
    # xatlas doesn't expose chart ids directly through this binding, so charts are
    # recovered here as UV-connected components: triangles sharing a UV edge belong
    # to the same chart, since packing never lets separate charts touch in UV space.
    n = uv.uvs.shape[0]
    parent = np.arange(n)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for tri in uv.indices:
        union(tri[0], tri[1])
        union(tri[1], tri[2])

    roots = np.array([find(i) for i in range(n)])
    unique_roots = np.unique(roots)

    panels: list[Panel] = []
    for chart_id, root in enumerate(unique_roots):
        vert_mask = roots == root
        local_vert_ids = np.nonzero(vert_mask)[0]
        remap = {v: k for k, v in enumerate(local_vert_ids)}

        tri_mask = vert_mask[uv.indices[:, 0]]
        chart_tris = uv.indices[tri_mask]
        local_tris = np.array(
            [[remap[v] for v in tri] for tri in chart_tris], dtype=np.uint32
        )

        # Flatten via a similarity transform per triangle fit is overkill for a
        # prototype; instead scale each panel's UV footprint to match the average
        # edge-length ratio between its 3D and UV edges, which keeps panels roughly
        # true-to-scale for real-world cutting/printing.
        uv_local = uv.uvs[local_vert_ids]
        pos_3d = uv.vertices[local_vert_ids]
        scale = _estimate_uv_to_world_scale(pos_3d, uv_local, local_tris)
        positions_2d = uv_local * scale

        panels.append(
            Panel(
                chart_id=chart_id,
                positions_2d=positions_2d.astype(np.float32),
                indices=local_tris,
                source_vertex_ids=local_vert_ids.astype(np.uint32),
            )
        )

    return panels


def _estimate_uv_to_world_scale(
    pos_3d: np.ndarray, uv_2d: np.ndarray, tris: np.ndarray
) -> float:
    if tris.shape[0] == 0:
        return 1.0
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    world_len = np.linalg.norm(pos_3d[a] - pos_3d[b], axis=1)
    uv_len = np.linalg.norm(uv_2d[a] - uv_2d[b], axis=1)
    valid = uv_len > 1e-8
    if not np.any(valid):
        return 1.0
    return float(np.median(world_len[valid] / uv_len[valid]))
