"""Simple orbit camera: yaw/pitch around a target, scroll to zoom."""
from __future__ import annotations

import numpy as np
from pyrr import Matrix44


class OrbitCamera:
    def __init__(self, target=(0.0, 0.0, 0.0), distance: float = 4.0):
        self.target = np.array(target, dtype=np.float32)
        self.distance = distance
        self.yaw = -90.0  # degrees, around Y
        self.pitch = 20.0  # degrees, clamped
        self.fov = 45.0

    def orbit(self, dx: float, dy: float, sensitivity: float = 0.3) -> None:
        self.yaw += dx * sensitivity
        self.pitch = float(np.clip(self.pitch + dy * sensitivity, -89.0, 89.0))

    def zoom(self, delta: float) -> None:
        self.distance = float(np.clip(self.distance - delta * 0.3, 0.5, 50.0))

    def pan(self, dx: float, dy: float, sensitivity: float = 0.01) -> None:
        forward = self._forward()
        right = np.cross(forward, np.array([0.0, 1.0, 0.0], dtype=np.float32))
        right /= np.linalg.norm(right) + 1e-8
        up = np.cross(right, forward)
        self.target += (-right * dx + up * dy) * sensitivity * self.distance

    def _forward(self) -> np.ndarray:
        yaw_r = np.radians(self.yaw)
        pitch_r = np.radians(self.pitch)
        x = np.cos(pitch_r) * np.cos(yaw_r)
        y = np.sin(pitch_r)
        z = np.cos(pitch_r) * np.sin(yaw_r)
        return np.array([x, y, z], dtype=np.float32)

    @property
    def position(self) -> np.ndarray:
        return self.target - self._forward() * self.distance

    def view_matrix(self) -> Matrix44:
        return Matrix44.look_at(self.position, self.target, (0.0, 1.0, 0.0), dtype="f4")

    def projection_matrix(self, aspect: float) -> Matrix44:
        return Matrix44.perspective_projection(self.fov, aspect, 0.05, 200.0, dtype="f4")
