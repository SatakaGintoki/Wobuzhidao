"""Coupled variable-property radial FVM for Problem 2."""
from __future__ import annotations

import numpy as np
from scipy.sparse import lil_matrix

from appendix3 import conductivity, heat_capacity, moisture_diffusivity_q2
from radial_fvm import RadialFVM, harmonic_mean
from utils import H, HM, R


class CoupledRadialFVM:
    def __init__(self, r: np.ndarray):
        geom = RadialFVM(r=r)
        self.r = geom.r
        self.W = geom.W
        self.r_half = geom.r_half
        self.dr_face = geom.dr_face
        self.n_nodes = geom.n_nodes
        self.N = geom.N
        self._geom = geom

    def output_indices(self) -> np.ndarray:
        return self._geom.output_indices()

    def pack(self, T: np.ndarray, C: np.ndarray) -> np.ndarray:
        return np.concatenate([T, C])

    def unpack(self, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n = self.n_nodes
        return y[:n], y[n:]

    def rhs(
        self,
        t: float,
        y: np.ndarray,
        Ta: float,
        Ca: float,
        *,
        D_const: float | None = None,
        ST: np.ndarray | None = None,
        SC: np.ndarray | None = None,
    ) -> np.ndarray:
        T, C = self.unpack(y)
        kn = np.asarray(conductivity(C), dtype=float)
        Bn = np.asarray(heat_capacity(C), dtype=float)
        if D_const is None:
            Dn = np.asarray(moisture_diffusivity_q2(C, T, protect=True), dtype=float)
        else:
            Dn = np.full_like(C, float(D_const))
        k_face = harmonic_mean(kn[:-1], kn[1:])
        D_face = harmonic_mean(Dn[:-1], Dn[1:])
        FT = -self.r_half * k_face * np.diff(T) / self.dr_face
        FC = -self.r_half * D_face * np.diff(C) / self.dr_face
        Tdot = np.empty_like(T)
        Cdot = np.empty_like(C)
        Tdot[0] = -FT[0] / (Bn[0] * self.W[0])
        Cdot[0] = -FC[0] / self.W[0]
        Tdot[1:-1] = (FT[:-1] - FT[1:]) / (Bn[1:-1] * self.W[1:-1])
        Cdot[1:-1] = (FC[:-1] - FC[1:]) / self.W[1:-1]
        FTsurf = R * H * (T[-1] - Ta)
        FCsurf = R * HM * (C[-1] - Ca)
        Tdot[-1] = (FT[-1] - FTsurf) / (Bn[-1] * self.W[-1])
        Cdot[-1] = (FC[-1] - FCsurf) / self.W[-1]
        if ST is not None:
            Tdot = Tdot + ST / Bn
        if SC is not None:
            Cdot = Cdot + SC
        return self.pack(Tdot, Cdot)

    def jac_sparsity(self):
        n = self.n_nodes
        J = lil_matrix((2 * n, 2 * n), dtype=float)
        for i in range(n):
            js = [i]
            if i > 0:
                js.append(i - 1)
            if i + 1 < n:
                js.append(i + 1)
            for j in js:
                J[i, j] = 1.0
                J[i, n + j] = 1.0
                J[n + i, j] = 1.0
                J[n + i, n + j] = 1.0
        return J.tocsc()
