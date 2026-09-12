"""Node-centered radial finite-volume operators for Problem 1."""
from __future__ import annotations

import numpy as np
from scipy.sparse import diags

from utils import CP, H, HM, K, R, RHO, moisture_diffusivity

OUTPUT_RADII_M = 0.001 * np.arange(21)


def graded_radial_nodes(level: int) -> np.ndarray:
    """Nodes denser near the surface; every 0.1 cm output radius remains a node.

    Interval subdivisions (before multiplying by ``level``):
    0–1.5 cm: 8; 1.5–1.8 cm: 16; 1.8–1.9 cm: 32; 1.9–2.0 cm: 64.
    Surface spacing at level L is 1e-3 / (64 L) metres.
    """
    level = int(level)
    if level < 1:
        raise ValueError("graded mesh level must be a positive integer")
    n_sub = np.full(20, 8 * level, dtype=int)
    n_sub[15:] = 16 * level
    n_sub[18] = 32 * level
    n_sub[19] = 64 * level
    pts = [0.0]
    for j in range(20):
        r0 = 0.001 * j
        r1 = 0.001 * (j + 1)
        m = int(n_sub[j])
        for k in range(1, m + 1):
            pts.append(r0 + (r1 - r0) * k / m)
    r = np.asarray(pts, dtype=float)
    r[0] = 0.0
    r[-1] = R
    return r


class RadialFVM:
    def __init__(self, N: int | None = None, r: np.ndarray | None = None):
        if r is not None:
            self.r = np.asarray(r, dtype=float)
            if self.r.ndim != 1 or self.r.size < 3:
                raise ValueError("r must be a 1-D array with at least 3 nodes")
            if abs(self.r[0]) > 1e-15 or abs(self.r[-1] - R) > 1e-14:
                raise ValueError("radial nodes must start at 0 and end at R")
            if np.any(np.diff(self.r) <= 0.0):
                raise ValueError("radial nodes must be strictly increasing")
        else:
            if N is None or int(N) < 2:
                raise ValueError("N must be at least 2")
            self.r = np.linspace(0.0, R, int(N) + 1)
        self.n_nodes = int(self.r.size)
        self.N = self.n_nodes - 1
        self.dr_face = np.diff(self.r)
        self.r_half = 0.5 * (self.r[:-1] + self.r[1:])
        a = np.empty(self.n_nodes)
        b = np.empty(self.n_nodes)
        a[0] = 0.0
        b[0] = self.r_half[0]
        a[-1] = self.r_half[-1]
        b[-1] = R
        if self.n_nodes > 2:
            a[1:-1] = self.r_half[:-1]
            b[1:-1] = self.r_half[1:]
        self.W = 0.5 * (b**2 - a**2)
        self.dr = float(self.dr_face.min())
        if abs(self.W.sum() - 0.5 * R**2) > 1e-14:
            raise RuntimeError("radial weights do not sum to R^2/2")

        self.M_heat = self._heat_matrix()
        self.M_heat_sparse = diags(
            [np.diag(self.M_heat, -1), np.diag(self.M_heat, 0), np.diag(self.M_heat, 1)],
            offsets=[-1, 0, 1],
            shape=self.M_heat.shape,
            format="csc",
        )
        self._heat_force_coef = (R * H) / (RHO * CP * self.W[-1])
        self._heat_force_index = self.n_nodes - 1

    def output_indices(self) -> np.ndarray:
        """Indices of 0, 0.1, ..., 2.0 cm nodes."""
        idx = np.empty(OUTPUT_RADII_M.size, dtype=int)
        for j, rc in enumerate(OUTPUT_RADII_M):
            k = int(np.argmin(np.abs(self.r - rc)))
            if abs(self.r[k] - rc) > 1e-12:
                raise ValueError(f"grid misses output radius {rc}, nearest {self.r[k]}")
            idx[j] = k
        return idx

    def _interior_face_coeff(self) -> np.ndarray:
        return self.r_half / self.dr_face

    def _heat_matrix(self) -> np.ndarray:
        n = self.n_nodes
        M = np.zeros((n, n))
        face = K * self._interior_face_coeff()
        den = RHO * CP * self.W
        M[0, 0] = -face[0] / den[0]
        M[0, 1] = face[0] / den[0]
        for i in range(1, n - 1):
            M[i, i - 1] = face[i - 1] / den[i]
            M[i, i + 1] = face[i] / den[i]
            M[i, i] = -(face[i - 1] + face[i]) / den[i]
        i = n - 1
        M[i, i - 1] = face[i - 1] / den[i]
        M[i, i] = (-face[i - 1] - R * H) / den[i]
        return M

    def heat_rhs(self, t: float, T: np.ndarray, Ta: float) -> np.ndarray:
        out = self.M_heat @ T
        out[self._heat_force_index] += self._heat_force_coef * Ta
        return out

    def heat_jac(self, t: float, T: np.ndarray):
        return self.M_heat_sparse

    def heat_jac_sparsity(self):
        n = self.n_nodes
        ones_m = np.ones(n - 1, dtype=float)
        ones_d = np.ones(n, dtype=float)
        return diags([ones_m, ones_d, ones_m], offsets=[-1, 0, 1], shape=(n, n), format="csc")

    def moisture_rhs(self, t: float, C: np.ndarray, Ca: float, D_const: float | None = None) -> np.ndarray:
        if D_const is None:
            D_node = moisture_diffusivity(C, protect=True)
        else:
            D_node = np.full_like(C, float(D_const))
        D_face = harmonic_mean(D_node[:-1], D_node[1:])
        F = -self.r_half * D_face * np.diff(C) / self.dr_face
        Cdot = np.empty_like(C)
        Cdot[0] = -F[0] / self.W[0]
        Cdot[1:-1] = (F[:-1] - F[1:]) / self.W[1:-1]
        F_surf = R * HM * (C[-1] - Ca)
        Cdot[-1] = (F[-1] - F_surf) / self.W[-1]
        return Cdot

    def moisture_jac_sparsity(self):
        return self.heat_jac_sparsity()

    def surface_heat_influx_density(self, T_s: float, Ta: float) -> float:
        """Heat into the solid per unit surface area, W/m^2."""
        return H * (Ta - T_s)

    def surface_moisture_outflux(self, C_s: float, Ca: float) -> float:
        """Outward moisture flux in the normalized (no rho_d) units, m/s * kg/kg."""
        return HM * (C_s - Ca)


def harmonic_mean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = np.zeros_like(a, dtype=float)
    both = (a > 0.0) & (b > 0.0)
    out[both] = 2.0 * a[both] * b[both] / (a[both] + b[both])
    return out
