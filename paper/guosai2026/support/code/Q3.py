# -*- coding: utf-8 -*-
"""问题 3：从原始附件复算答案数据。

运行 python Q3.py；检查环境 python Q3.py --check。
本文件内嵌本问所需的全部项目模块，模块源码在下方按文件名分段列出。
运行时自动展开到相对目录 _runtime/Q3/code，以支持源码哈希核验。
输入、输出均相对于本文件的位置，与当前工作目录无关。
方程、物性、网格、容差和验证判据沿用原正式求解程序。
"""
import argparse
import importlib
import os
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parent
QUESTION = 3
SOURCES = {}

# ========================================================================
# Module: utils.py
# ========================================================================
SOURCES['utils'] = r'''"""Shared paths and attachment readers for Problem A."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
ATTACH_DIR = DATA_DIR / "附件"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
REPORTS_DIR = ROOT / "reports"

# Appendix 2 (Problem 1)
R = 0.02
L = 0.25
RHO = 820.0
CP = 2600.0
K = 0.36
H = 25.0
HM = 8.0e-7
T0 = 28.0
C0 = 2.55
D_PREFACTOR = 7.0e-9
D_EXP_COEF = 0.89
T_END = 1800.0
ALPHA = K / (RHO * CP)


def moisture_diffusivity(C: np.ndarray | float, *, protect: bool = True) -> np.ndarray | float:
    """D(C) = 7e-9 exp(-0.89/C). Nonpositive C uses D=0 only as a solver-domain guard."""
    C_arr = np.asarray(C, dtype=float)
    out = np.zeros_like(C_arr, dtype=float)
    positive = C_arr > 0.0
    if np.any(positive):
        out[positive] = D_PREFACTOR * np.exp(-D_EXP_COEF / C_arr[positive])
    if not protect and np.any(~positive):
        raise ValueError("moisture diffusivity evaluated at nonpositive C without protection")
    if np.isscalar(C):
        return float(out)
    return out


def load_oven_table() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = ATTACH_DIR / "附件1.xlsx"
    wb = load_workbook(path, read_only=True, data_only=True)
    rows = list(wb.active.values)
    wb.close()
    data = np.asarray(rows[1:], dtype=float)
    t, Ta, Ca = data[:, 0], data[:, 1], data[:, 2]
    if t[0] != 0.0:
        raise ValueError(f"oven table must start at t=0, got {t[0]}")
    return t, Ta, Ca


class PiecewiseLinear:
    """Piecewise linear interpolant; kept for comparison, not used in Q1 production."""

    def __init__(self, t: np.ndarray, y: np.ndarray):
        self.t = np.asarray(t, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.kind = "linear"
        if self.t.ndim != 1 or self.y.shape != self.t.shape:
            raise ValueError("interpolant requires matching 1-D arrays")
        if np.any(np.diff(self.t) <= 0):
            raise ValueError("breakpoints must be strictly increasing")

    def __call__(self, t: float | np.ndarray) -> float | np.ndarray:
        return np.interp(t, self.t, self.y)

    def slope(self, t: float) -> float:
        t = float(t)
        if t <= self.t[0] or t >= self.t[-1]:
            if t >= self.t[-1]:
                dt = self.t[-1] - self.t[-2]
                return (self.y[-1] - self.y[-2]) / dt
            return (self.y[1] - self.y[0]) / (self.t[1] - self.t[0])
        i = int(np.searchsorted(self.t, t, side="right") - 1)
        i = min(i, len(self.t) - 2)
        return (self.y[i + 1] - self.y[i]) / (self.t[i + 1] - self.t[i])


class PchipOven:
    """Monotone piecewise cubic Hermite interpolant (PCHIP) through attachment knots."""

    def __init__(self, t: np.ndarray, y: np.ndarray):
        self.t = np.asarray(t, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.kind = "pchip"
        if self.t.ndim != 1 or self.y.shape != self.t.shape:
            raise ValueError("interpolant requires matching 1-D arrays")
        if np.any(np.diff(self.t) <= 0):
            raise ValueError("breakpoints must be strictly increasing")
        self._pchip = PchipInterpolator(self.t, self.y, extrapolate=False)
        self._deriv = self._pchip.derivative()

    def __call__(self, t: float | np.ndarray) -> float | np.ndarray:
        tt = np.clip(np.asarray(t, dtype=float), self.t[0], self.t[-1])
        val = self._pchip(tt)
        if np.ndim(t) == 0:
            return float(val)
        return np.asarray(val, dtype=float)

    def slope(self, t: float) -> float:
        tt = float(np.clip(t, self.t[0], self.t[-1]))
        return float(self._deriv(tt))
'''

# ========================================================================
# Module: delivery.py
# ========================================================================
SOURCES['delivery'] = r'''"""Fail-closed numerical delivery checks shared by Q1 and Q2."""
import json
from pathlib import Path


def make_gate(checks):
    checks = {name: bool(value) for name, value in checks.items()}
    return {"checks": checks, "failed_checks": [k for k, v in checks.items() if not v],
            "meets_delivery_gate": bool(checks) and all(checks.values())}


def require_delivery(validation, diagnostic_path):
    """Persist diagnostics first; never reach any production writer on failure."""
    path = Path(diagnostic_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validation, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    gate = validation["delivery_gate"]
    checks = gate.get("checks", {})
    if not checks or not all(value is True for value in checks.values()) or gate.get("meets_delivery_gate") is not True:
        raise RuntimeError("Delivery blocked; see " + str(path) + ": " + str(gate.get("failed_checks", [])))
'''

# ========================================================================
# Module: q1_analytic.py
# ========================================================================
SOURCES['q1_analytic'] = r'''"""Independent Bessel–Duhamel reference for the linear radial heat (or frozen-D moisture) problem."""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.special import j0, j1
from scipy.sparse import diags


def robin_eigenvalues(Bi: float, n_roots: int) -> np.ndarray:
    """Positive roots of lambda * J1(lambda) = Bi * J0(lambda)."""
    if Bi <= 0:
        raise ValueError("Biot number must be positive")
    n_roots = int(n_roots)

    def f(lam: float) -> float:
        return lam * j1(lam) - Bi * j0(lam)

    lam_max = (n_roots + 4) * np.pi
    grid = np.linspace(1e-10, lam_max, max(8000, 200 * n_roots))
    vals = grid * j1(grid) - Bi * j0(grid)
    roots: list[float] = []
    for i in range(len(grid) - 1):
        v0, v1 = vals[i], vals[i + 1]
        if not np.isfinite(v0) or not np.isfinite(v1):
            continue
        a, b = float(grid[i]), float(grid[i + 1])
        if v0 == 0.0:
            cand = a
        elif v0 * v1 < 0.0:
            cand = float(brentq(f, a, b, xtol=1e-14, maxiter=200))
        else:
            continue
        if not roots or abs(cand - roots[-1]) > 1e-10:
            roots.append(cand)
        if len(roots) >= n_roots:
            break
    if len(roots) < n_roots:
        raise RuntimeError(f"found only {len(roots)} Robin Bessel roots, need {n_roots}")
    return np.asarray(roots, dtype=float)


def expansion_coefficients(lam: np.ndarray) -> np.ndarray:
    j0l = j0(lam)
    j1l = j1(lam)
    return 2.0 * j1l / (lam * (j0l**2 + j1l**2))


class BesselDuhamel:
    def __init__(self, Bi: float, diffusivity: float, R: float, n_terms: int = 120):
        self.Bi = float(Bi)
        self.alpha = float(diffusivity)
        self.R = float(R)
        self.lam = robin_eigenvalues(self.Bi, n_terms)
        self.A = expansion_coefficients(self.lam)
        self.beta = self.alpha * self.lam**2 / self.R**2

    def radial_modes(self, r: np.ndarray) -> np.ndarray:
        """Return array shape (n_terms, n_r) of A_n J0(lambda_n r/R)."""
        r = np.asarray(r, dtype=float)
        return self.A[:, None] * j0(self.lam[:, None] * (r[None, :] / self.R))

    def evaluate(self, r: np.ndarray, t: float, env: Any, u0: float) -> np.ndarray:
        return self.evaluate_many(r, np.array([float(t)]), env, u0)[0]

    def evaluate_many(self, r: np.ndarray, times: np.ndarray, env: Any, u0: float) -> np.ndarray:
        """T = env(t) - sum A_n J0 I_n, with I' = -beta I + env'(t), I(0)=env(0)-u0.

        Valid for any C1 interpolant that exposes env.y, env.slope, and env(t).
        """
        r = np.asarray(r, dtype=float)
        times = np.asarray(times, dtype=float)
        if times.size == 0:
            return np.empty((0, r.size), dtype=float)
        modes = self.radial_modes(r)
        beta = self.beta
        I0 = np.full(beta.size, float(env.y[0] - u0))
        t_end = float(np.max(times))
        out = np.empty((times.size, r.size), dtype=float)
        zero = times == 0.0
        if np.all(zero):
            out[:] = u0
            return out
        t_eval = times[~zero]
        sol = solve_ivp(
            lambda t, I: -beta * I + env.slope(t),
            (0.0, max(t_end, 1e-30)),
            I0,
            method="BDF",
            jac=diags(-beta, format="csc"),
            rtol=1e-11,
            atol=1e-13,
            t_eval=t_eval,
            max_step=1.0,
            vectorized=False,
        )
        if not sol.success:
            raise RuntimeError(f"Bessel Duhamel ODE failed: {sol.message}")
        Ihist = sol.y.T
        env_t = np.array([float(env(t)) for t in t_eval], dtype=float)
        nonzero_vals = env_t[:, None] - Ihist @ modes
        out[zero] = u0
        out[~zero] = nonzero_vals
        return out


def converged_reference(Bi, diffusivity, R, r, times, env, u0, start_terms=320, tolerance=1e-8):
    """Double the modal truncation and explicitly check every requested point."""
    previous = BesselDuhamel(Bi, diffusivity, R, start_terms).evaluate_many(r, times, env, u0)
    history = []
    for terms in (start_terms * 2, start_terms * 4, start_terms * 8):
        current = BesselDuhamel(Bi, diffusivity, R, terms).evaluate_many(r, times, env, u0)
        error = float(np.max(np.abs(current - previous)))
        history.append({"terms": terms, "previous_terms": terms // 2, "max_abs_difference": error})
        if np.isfinite(error) and error <= tolerance:
            return current, {"passed": True, "tolerance": tolerance, "history": history, "terms": terms}
        previous = current
    return current, {"passed": False, "tolerance": tolerance, "history": history, "terms": terms}
'''

# ========================================================================
# Module: radial_fvm.py
# ========================================================================
SOURCES['radial_fvm'] = r'''"""Node-centered radial finite-volume operators for Problem 1."""
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
'''

# ========================================================================
# Module: reproduction_export.py
# ========================================================================
SOURCES['reproduction_export'] = r'''"""Portable Excel export from validated solver arrays; no external runtime."""
from copy import copy
import json
from pathlib import Path

import numpy as np
from openpyxl import load_workbook


def write_template(root, question, times, fields):
    root = Path(root)
    template = root / 'data' / '附件' / '附件3' / f'result{question}.xlsx'
    wb = load_workbook(template)
    if len(wb.worksheets) != len(fields):
        raise ValueError('Template sheet count does not match the output fields')
    times = np.asarray(times)
    if times.ndim != 1 or not np.isfinite(times).all() or not (np.diff(times) > 0).all():
        raise ValueError('Invalid output time sequence')
    for ws, values in zip(wb.worksheets, fields):
        values = np.asarray(values)
        expected = 22 if question == 4 else 21
        if values.shape != (len(times), expected):
            raise ValueError('Output shape does not match the requested radial grid')
        if np.isinf(values).any() or (question != 4 and np.isnan(values).any()):
            raise ValueError('Unexpected nonfinite output')
        header = ws.cell(1, 1).value
        surface = ws.cell(1, ws.max_column).value
        number_style = copy(ws.cell(2, 2)._style)
        header_style = copy(ws.cell(1, 2)._style)
        ws.delete_rows(1, ws.max_row)
        ws.append([header] + [j / 10 for j in range(21)] + ([surface] if question == 4 else []))
        for cell in ws[1]:
            cell._style = copy(header_style)
        for t, row in zip(times, values):
            ws.append([float(t)] + [None if np.isnan(v) else float(v) for v in row])
        for row in ws.iter_rows(min_row=2, min_col=2):
            for cell in row:
                cell._style = copy(number_style)
                cell.number_format = '0.0000'
        ws.freeze_panes = 'B2'
    wb.properties.creator = 'Team'
    wb.properties.lastModifiedBy = 'Team'
    dest = root / 'results' / f'result{question}.xlsx'
    dest.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dest)
    wb.close()
    print(f'Excel saved: results/result{question}.xlsx', flush=True)


def export_saved(root, question):
    root = Path(root)
    validation = json.loads((root / 'results' / f'q{question}_validation.json').read_text(encoding='utf-8'))
    if question == 4:
        if validation.get('pass') is not True or not validation.get('checks') or not all(v is True for v in validation['checks'].values()):
            raise RuntimeError('Q4 numerical validation did not pass')
    else:
        from delivery import require_delivery
        require_delivery(validation, root / 'results' / f'q{question}_export_validation.json')
        if question == 3:
            from q3_closeout import require_q3_delivery
            require_q3_delivery(validation, root / 'results' / 'q3_export_validation.json')
    with np.load(root / 'results' / f'q{question}_solution.npz') as z:
        if question in (1, 2):
            write_template(root, question, z['times'], [z['T_out'], z['C_out']])
        elif question == 3:
            write_template(root, question, z['excel_times'], [z['C_out']])
        else:
            write_template(root, question, z['times_s'][1:], [z['C_physical'][1:]])
'''

# ========================================================================
# Module: appendix3.py
# ========================================================================
SOURCES['appendix3'] = r'''"""Appendix 3 effective properties for Problems 2 and 3."""
from __future__ import annotations

import numpy as np

RHO_A = 650.0
RHO_B = 128.0
CP_A = 1450.0
CP_B = 2736.0
K_A = 0.21
K_B = 0.38
D_PREFACTOR = 2.4e-3
D_C_COEF = 0.45
D_T_COEF = 3850.0


def rho(C: np.ndarray | float) -> np.ndarray | float:
    return RHO_A + RHO_B * np.asarray(C, dtype=float)


def cp(C: np.ndarray | float) -> np.ndarray | float:
    C_arr = np.asarray(C, dtype=float)
    return CP_A + CP_B * C_arr / (1.0 + C_arr)


def conductivity(C: np.ndarray | float) -> np.ndarray | float:
    C_arr = np.asarray(C, dtype=float)
    return K_A + K_B * C_arr / (1.0 + C_arr)


def heat_capacity(C: np.ndarray | float) -> np.ndarray | float:
    return rho(C) * cp(C)


def conductivity_deriv(C: np.ndarray | float) -> np.ndarray | float:
    C_arr = np.asarray(C, dtype=float)
    return K_B / (1.0 + C_arr) ** 2


def heat_capacity_deriv(C: np.ndarray | float) -> np.ndarray | float:
    C_arr = np.asarray(C, dtype=float)
    return RHO_B * cp(C_arr) + rho(C_arr) * CP_B / (1.0 + C_arr) ** 2


def moisture_diffusivity_q2(
    C: np.ndarray | float,
    T_celsius: np.ndarray | float,
    *,
    protect: bool = True,
) -> np.ndarray | float:
    """D(C,T) with T in Celsius; Kelvin is used only inside the Arrhenius factor."""
    C_arr = np.asarray(C, dtype=float)
    T_arr = np.asarray(T_celsius, dtype=float)
    out = np.zeros(np.broadcast(C_arr, T_arr).shape, dtype=float)
    C_b, T_b = np.broadcast_arrays(C_arr, T_arr)
    positive = C_b > 0.0
    if np.any(positive):
        Tk = T_b[positive] + 273.15
        out[positive] = D_PREFACTOR * np.exp(-D_C_COEF / C_b[positive]) * np.exp(-D_T_COEF / Tk)
    if not protect and np.any(~positive):
        raise ValueError("q2 diffusivity evaluated at nonpositive C without protection")
    if np.ndim(C) == 0 and np.ndim(T_celsius) == 0:
        return float(np.asarray(out))
    return out


def diffusivity_partials(C: np.ndarray, T_celsius: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    D = np.asarray(moisture_diffusivity_q2(C, T_celsius, protect=True), dtype=float)
    C_arr = np.asarray(C, dtype=float)
    T_arr = np.asarray(T_celsius, dtype=float)
    dD_dC = np.zeros_like(D)
    dD_dT = np.zeros_like(D)
    ok = C_arr > 0.0
    dD_dC[ok] = D[ok] * (D_C_COEF / C_arr[ok] ** 2)
    Tk = T_arr + 273.15
    dD_dT[ok] = D[ok] * (D_T_COEF / Tk[ok] ** 2)
    return D, dD_dC, dD_dT
'''

# ========================================================================
# Module: radial_coupled.py
# ========================================================================
SOURCES['radial_coupled'] = r'''"""Coupled variable-property radial FVM for Problem 2."""
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
'''

# ========================================================================
# Module: problem2.py
# ========================================================================
SOURCES['problem2'] = r'''"""Problem 2: coupled variable-property radial drying for 0–3 h."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from scipy.integrate import solve_ivp

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from appendix3 import (
    conductivity,
    conductivity_deriv,
    diffusivity_partials,
    heat_capacity,
    heat_capacity_deriv,
    moisture_diffusivity_q2,
)
from q1_analytic import BesselDuhamel, converged_reference
from delivery import make_gate, require_delivery
from radial_coupled import CoupledRadialFVM
from radial_fvm import graded_radial_nodes
from utils import (
    C0,
    FIGURES_DIR,
    H,
    HM,
    L,
    R,
    RESULTS_DIR,
    T0,
    PchipOven,
    load_oven_table,
)

T_END = 10800.0
OUTPUT_RADII_M = 0.001 * np.arange(21)
TABLE_HOURS = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
TABLE_TIMES = 3600.0 * TABLE_HOURS
TABLE_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
TREF = 28.0


def load_q2_inputs() -> tuple[PchipOven, PchipOven, np.ndarray]:
    t, Ta, Ca = load_oven_table()
    mask = t <= T_END + 1e-12
    t, Ta, Ca = t[mask], Ta[mask], Ca[mask]
    if t.size != 181 or abs(t[-1] - T_END) > 1e-12:
        raise ValueError(f"expected 181 oven records on [0, 10800], got {t.size}, t_end={t[-1]}")
    if abs(Ta[0] - T0) > 1e-12:
        raise ValueError(f"Ta(0)={Ta[0]} != T0={T0}")
    Ta_fun = PchipOven(t, Ta)
    Ca_fun = PchipOven(t, Ca)
    for tj, yj in zip(t, Ta):
        if abs(float(Ta_fun(tj)) - float(yj)) > 1e-12:
            raise RuntimeError(f"PCHIP misses Ta knot t={tj}")
    for tj, yj in zip(t, Ca):
        if abs(float(Ca_fun(tj)) - float(yj)) > 1e-12:
            raise RuntimeError(f"PCHIP misses Ca knot t={tj}")
    return Ta_fun, Ca_fun, t


def integrate_coupled(fvm: CoupledRadialFVM, y0, t_end, Ta_fun, Ca_fun, rtol, atol, max_step,
                      D_const=None, source=None, t_eval=None):
    y0 = np.asarray(y0, dtype=float)
    n = fvm.n_nodes
    atol_arr = np.asarray(atol, dtype=float)
    if atol_arr.ndim == 0:
        atol_arr = np.concatenate([np.full(n, float(atol_arr)), np.full(n, float(atol_arr) * 0.01)])

    def rhs(t, y):
        ST = SC = None
        if source is not None:
            ST, SC = source(t, fvm.r)
        return fvm.rhs(t, y, float(Ta_fun(t)), float(Ca_fun(t)), D_const=D_const, ST=ST, SC=SC)

    if t_eval is None:
        t_eval = np.arange(1.0, t_end + 0.5, 1.0)
    sol = solve_ivp(
        rhs,
        (0.0, float(t_end)),
        y0,
        method="BDF",
        rtol=rtol,
        atol=atol_arr,
        max_step=max_step,
        t_eval=t_eval,
        dense_output=False,
        vectorized=False,
        jac_sparsity=fvm.jac_sparsity(),
    )
    if not sol.success:
        raise RuntimeError(f"coupled BDF failed: {sol.message}")
    times = np.concatenate([[0.0], sol.t])
    Y = np.vstack([y0, sol.y.T])
    return times, Y


def extract_output(fvm: CoupledRadialFVM, Y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = fvm.n_nodes
    idx = fvm.output_indices()
    T = Y[:, :n][:, idx]
    C = Y[:, n:][:, idx]
    return T, C


def compare_on_output(A, B, times) -> dict:
    diff = np.abs(A - B)
    k = int(np.argmax(diff))
    n_t, n_r = diff.shape
    i, j = divmod(k, n_r)
    paper_t = np.isin(times, TABLE_TIMES)
    paper_r = slice(None, None, 5) if n_r == 21 else slice(None)
    return {
        "max_abs": float(diff.max()),
        "max_time_s": float(times[i]),
        "max_radius_cm": 0.1 * j,
        "mean_abs": float(diff.mean()),
        "paper_table_max_abs": float(np.max(np.abs(A[paper_t][:, paper_r] - B[paper_t][:, paper_r]))),
    }


def four_decimal_stats(A, B, times) -> dict:
    Ar, Br = np.round(A, 4), np.round(B, 4)
    changed = Ar != Br
    paper_t = np.isin(times, TABLE_TIMES)
    paper_r = slice(None, None, 5) if A.shape[1] == 21 else slice(None)
    paper_changed = Ar[paper_t][:, paper_r] != Br[paper_t][:, paper_r]
    return {
        "changed_cells": int(np.sum(changed)),
        "total_cells": int(A.size),
        "paper_changed_cells": int(np.sum(paper_changed)),
        "paper_total_cells": int(paper_changed.size),
        "max_abs": float(np.max(np.abs(A - B))),
        "paper_table_max_abs": float(np.max(np.abs(A[paper_t][:, paper_r] - B[paper_t][:, paper_r]))),
    }


def manufactured_fields(r: np.ndarray, t: float) -> tuple[np.ndarray, np.ndarray]:
    x2 = (r / R) ** 2
    T = 28.0 + 2.0 * np.exp(-t / 600.0) * (1.0 + x2)
    C = 1.5 + 0.2 * np.exp(-t / 500.0) * (1.0 + x2)
    return T, C


def manufactured_env(r_surface: float, t: float) -> tuple[float, float]:
    T, C = manufactured_fields(np.array([r_surface]), t)
    Ts, Cs = float(T[0]), float(C[0])
    u = np.exp(-t / 600.0)
    v = np.exp(-t / 500.0)
    Tr = 4.0 / R * u
    Cr = 4.0 / R * v * 0.1  # C amplitude 0.2 vs T amplitude 2: Cr = 0.2*v*2r/R^2 at r=R -> 0.4 v / R
    Cr = 0.4 / R * v
    kn = float(conductivity(Cs))
    Dn = float(moisture_diffusivity_q2(Cs, Ts))
    Ta = Ts + kn * Tr / H
    Ca = Cs + Dn * Cr / HM
    return Ta, Ca


class ManufacturedOven:
    def __init__(self, kind: str):
        self.kind = kind

    def __call__(self, t):
        Ta, Ca = manufactured_env(R, float(t))
        return Ta if self.kind == "T" else Ca


def manufactured_sources(t: float, r: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    T, C = manufactured_fields(r, t)
    x2 = (r / R) ** 2
    u = np.exp(-t / 600.0)
    v = np.exp(-t / 500.0)
    Tt = 2.0 * (-1.0 / 600.0) * u * (1.0 + x2)
    Ct = 0.2 * (-1.0 / 500.0) * v * (1.0 + x2)
    Tr = 4.0 * r / (R ** 2) * u
    Trr = np.full_like(r, 4.0 / (R ** 2) * u)
    Cr = 0.4 * r / (R ** 2) * v
    Crr = np.full_like(r, 0.4 / (R ** 2) * v)
    lapT = np.empty_like(r)
    lapC = np.empty_like(r)
    center = r < 1e-16
    lapT[center] = 2.0 * Trr[center]
    lapC[center] = 2.0 * Crr[center]
    away = ~center
    lapT[away] = Trr[away] + Tr[away] / r[away]
    lapC[away] = Crr[away] + Cr[away] / r[away]
    kn = np.asarray(conductivity(C), dtype=float)
    kp = np.asarray(conductivity_deriv(C), dtype=float)
    Bn = np.asarray(heat_capacity(C), dtype=float)
    D, dD_dC, dD_dT = diffusivity_partials(C, T)
    ST = Bn * Tt - (kn * lapT + kp * Cr * Tr)
    SC = Ct - (D * lapC + dD_dC * Cr ** 2 + dD_dT * Tr * Cr)
    return ST, SC


def conservation_moisture(fvm, times, Y, Ca_fun) -> dict:
    n = fvm.n_nodes
    C = Y[:, n:]
    M = C @ fvm.W
    M0 = float(M[0])
    CN = C[:, -1]
    Ca = np.array([float(Ca_fun(t)) for t in times])
    I = float(np.trapezoid(HM * (CN - Ca), times))
    rhs = M0 - R * I
    Mt = float(M[-1])
    denom = max(abs(M0 - Mt), abs(R * I), 1e-18)
    return {"M0": M0, "M_end": Mt, "rhs": rhs, "relative_residual": abs(Mt - rhs) / denom}


def conservation_heat(fvm, times, Y, Ta_fun) -> dict:
    n = fvm.n_nodes
    T = Y[:, :n]
    C = Y[:, n:]
    Bn = np.asarray(heat_capacity(C), dtype=float)
    Bp = np.asarray(heat_capacity_deriv(C), dtype=float)
    E = 2.0 * np.pi * L * np.sum(fvm.W[None, :] * Bn * (T - TREF), axis=1)
    TN = T[:, -1]
    Ta = np.array([float(Ta_fun(t)) for t in times])
    Q = 2.0 * np.pi * R * L * H * float(np.trapezoid(Ta - TN, times))
    dC = np.gradient(C, times, axis=0)
    corr = 2.0 * np.pi * L * np.sum(fvm.W[None, :] * Bp * (T - TREF) * dC, axis=1)
    Icorr = float(np.trapezoid(corr, times))
    lhs = float(E[-1] - E[0] - Icorr)
    denom = max(abs(Q), abs(lhs), 1e-12)
    return {
        "E_end_minus_E0": float(E[-1] - E[0]),
        "composition_correction": Icorr,
        "Q_surface": Q,
        "relative_residual": abs(lhs - Q) / denom,
    }


def assert_physical(T_out, C_out, Ta_fun, Ca_fun) -> dict:
    Ta_max = float(np.max(Ta_fun.y))
    Ca_min = float(np.min(Ca_fun.y))
    info = {
        "T_min": float(T_out.min()),
        "T_max": float(T_out.max()),
        "C_min": float(C_out.min()),
        "C_max": float(C_out.max()),
        "T_below_28": float(max(0.0, 28.0 - T_out.min())),
        "T_above_Ta_max": float(max(0.0, T_out.max() - Ta_max)),
        "C_above_C0": float(max(0.0, C_out.max() - C0)),
        "C_below_Ca_min": float(max(0.0, Ca_min - C_out.min())),
        "Ta_range": [float(np.min(Ta_fun.y)), Ta_max],
        "Ca_range": [Ca_min, float(np.max(Ca_fun.y))],
    }
    info["T_bounds_ok"] = info["T_below_28"] <= 1e-6 and info["T_above_Ta_max"] <= 1e-4
    info["C_bounds_ok"] = info["C_above_C0"] <= 1e-8 and info["C_below_Ca_min"] <= 1e-8
    return info


def write_result_workbook(path: Path, T_out, C_out, times):
    radii_cm = 0.1 * np.arange(21)
    wb = Workbook()
    for title, arr in (("温度", T_out), ("水分浓度", C_out)):
        ws = wb.create_sheet(title)
        ws["A1"] = "时间\\到药材中心的距离"
        for j, rc in enumerate(radii_cm, start=2):
            ws.cell(1, j, float(rc))
        for i, t in enumerate(times):
            ws.cell(i + 2, 1, int(round(float(t))))
            for j in range(21):
                cell = ws.cell(i + 2, j + 2, float(arr[i, j]))
                cell.number_format = "0.0000"
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def write_paper_csv(path: Path, arr_out, times):
    t_idx = {float(t): i for i, t in enumerate(times)}
    r_idx = {round(0.1 * j, 10): j for j in range(21)}
    lines = ["t_h," + ",".join(f"r_{rc:g}cm" for rc in TABLE_RADII_CM)]
    for th, t in zip(TABLE_HOURS, TABLE_TIMES):
        row = [f"{th:g}"]
        i = t_idx[float(t)]
        for rc in TABLE_RADII_CM:
            j = r_idx[float(rc)]
            row.append(f"{arr_out[i, j]:.8f}")
        lines.append(",".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 9,
        "axes.labelsize": 10,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    return plt


def plot_figures(plt, fvm, times, Y, T_out, C_out, Ta_fun, Ca_fun):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    n = fvm.n_nodes
    r_cm = fvm.r * 100.0
    idx = {float(t): i for i, t in enumerate(times)}
    marks = TABLE_TIMES

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for t in marks:
        ax.plot(r_cm, Y[idx[float(t)], :n], lw=1.2, label=fr"$t={t/3600:g}\,\mathrm{{h}}$")
    ax.set_xlabel("半径 $r$ (cm)")
    ax.set_ylabel("温度 $T$ (°C)")
    ax.set_xlim(0, 2)
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q2_T_profiles.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for t in marks:
        ax.plot(r_cm, Y[idx[float(t)], n:], lw=1.2, label=fr"$t={t/3600:g}\,\mathrm{{h}}$")
    ax.set_xlabel("半径 $r$ (cm)")
    ax.set_ylabel(r"干基含水率 $C$ (kg/kg)")
    ax.set_xlim(0, 2)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q2_C_profiles.pdf")
    plt.close(fig)

    t_plot = times
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(t_plot / 3600.0, [Ta_fun(t) for t in t_plot], lw=1.0, ls="--", label="烘房 $T_a$")
    ax.plot(t_plot / 3600.0, T_out[:, -1], lw=1.2, label="表面")
    ax.plot(t_plot / 3600.0, T_out[:, 0], lw=1.2, label="中心")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel("温度 (°C)")
    ax.set_xlim(0, 3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q2_T_center_surface.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(t_plot / 3600.0, C_out[:, -1], lw=1.2, label="表面")
    ax.plot(t_plot / 3600.0, C_out[:, 0], lw=1.2, label="中心")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel(r"干基含水率 $C$ (kg/kg)")
    ax.set_xlim(0, 3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q2_C_center_surface.pdf")
    plt.close(fig)

    D_c = moisture_diffusivity_q2(C_out[:, 0], T_out[:, 0])
    D_s = moisture_diffusivity_q2(C_out[:, -1], T_out[:, -1])
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(t_plot / 3600.0, D_s, lw=1.2, label="表面 $D$")
    ax.plot(t_plot / 3600.0, D_c, lw=1.2, label="中心 $D$")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel(r"$D$ (m$^2$/s)")
    ax.set_xlim(0, 3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q2_D_center_surface.pdf")
    plt.close(fig)


def run_mms(level: int = 4) -> dict:
    r = graded_radial_nodes(level)
    fvm = CoupledRadialFVM(r)
    T0f, C0f = manufactured_fields(fvm.r, 0.0)
    y0 = fvm.pack(T0f, C0f)
    Ta_fun = ManufacturedOven("T")
    Ca_fun = ManufacturedOven("C")
    times, Y = integrate_coupled(
        fvm, y0, 100.0, Ta_fun, Ca_fun,
        rtol=1e-8, atol=1e-9, max_step=0.5,
        source=manufactured_sources,
        t_eval=np.arange(1.0, 100.5, 1.0),
    )
    n = fvm.n_nodes
    T_num, C_num = Y[:, :n], Y[:, n:]
    T_ex = np.stack([manufactured_fields(fvm.r, t)[0] for t in times])
    C_ex = np.stack([manufactured_fields(fvm.r, t)[1] for t in times])
    return {
        "level": level,
        "n_nodes": n,
        "T_max_abs": float(np.max(np.abs(T_num - T_ex))),
        "C_max_abs": float(np.max(np.abs(C_num - C_ex))),
        "T_end_max_abs": float(np.max(np.abs(T_num[-1] - T_ex[-1]))),
        "C_end_max_abs": float(np.max(np.abs(C_num[-1] - C_ex[-1]))),
    }


def main():
    t_wall0 = time.perf_counter()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    Ta_fun, Ca_fun, knots = load_q2_inputs()
    print("oven points", knots.size, "kind", Ta_fun.kind, "Ta(10800)=", Ta_fun(T_END), "Ca(10800)=", Ca_fun(T_END))
    D0 = float(moisture_diffusivity_q2(C0, T0))
    print("initial D", D0, "k", float(conductivity(C0)), "B", float(heat_capacity(C0)))

    print("manufactured-solution probe")
    mms = run_mms(4)
    print("MMS", mms)

    mesh_levels = [2, 4]
    rtol, atol_T, atol_C, max_step = 1e-9, 1e-8, 1e-10, 1.0
    solutions = {}
    for level in mesh_levels:
        r = graded_radial_nodes(level)
        fvm = CoupledRadialFVM(r)
        tag = f"G{level}"
        print(f"\n=== {tag} nodes={fvm.n_nodes} ===")
        y0 = fvm.pack(np.full(fvm.n_nodes, T0), np.full(fvm.n_nodes, C0))
        atol = np.concatenate([np.full(fvm.n_nodes, atol_T), np.full(fvm.n_nodes, atol_C)])
        times, Y = integrate_coupled(fvm, y0, T_END, Ta_fun, Ca_fun, rtol, atol, max_step)
        times_pos = times[times > 0]
        Y_pos = Y[times > 0]
        T_out, C_out = extract_output(fvm, Y_pos)
        solutions[level] = dict(
            tag=tag, fvm=fvm, times=times_pos, Y=Y_pos, Y_full=Y, times_full=times,
            T_out=T_out, C_out=C_out, n_nodes=fvm.n_nodes,
        )
        print("done", tag, "T", T_out.min(), T_out.max(), "C", C_out.min(), C_out.max(),
              "C(t=1,s)", C_out[0, -1], "C(3h,s)", C_out[-1, -1], "C(3h,c)", C_out[-1, 0])

    t = solutions[4]["times"]
    conv = {
        "T_G2_vs_G4": compare_on_output(solutions[2]["T_out"], solutions[4]["T_out"], t),
        "C_G2_vs_G4": compare_on_output(solutions[2]["C_out"], solutions[4]["C_out"], t),
    }
    fourdec = {
        "T_G2_vs_G4": four_decimal_stats(solutions[2]["T_out"], solutions[4]["T_out"], t),
        "C_G2_vs_G4": four_decimal_stats(solutions[2]["C_out"], solutions[4]["C_out"], t),
    }
    print("conv", conv)
    print("4dp", fourdec)
    paper_ok = fourdec["T_G2_vs_G4"]["paper_changed_cells"] == 0 and fourdec["C_G2_vs_G4"]["paper_changed_cells"] == 0
    abs_ok = conv["T_G2_vs_G4"]["max_abs"] <= 2e-5 and conv["C_G2_vs_G4"]["max_abs"] <= 2e-5
    need_g8 = not (paper_ok and abs_ok)
    if need_g8:
        print("G2 vs G4 not enough; running G8")
        level = 8
        r = graded_radial_nodes(level)
        fvm = CoupledRadialFVM(r)
        y0 = fvm.pack(np.full(fvm.n_nodes, T0), np.full(fvm.n_nodes, C0))
        atol = np.concatenate([np.full(fvm.n_nodes, atol_T), np.full(fvm.n_nodes, atol_C)])
        times, Y = integrate_coupled(fvm, y0, T_END, Ta_fun, Ca_fun, rtol, atol, max_step)
        times_pos = times[times > 0]
        Y_pos = Y[times > 0]
        T_out, C_out = extract_output(fvm, Y_pos)
        solutions[8] = dict(
            tag="G8", fvm=fvm, times=times_pos, Y=Y_pos, Y_full=Y, times_full=times,
            T_out=T_out, C_out=C_out, n_nodes=fvm.n_nodes,
        )
        t = solutions[8]["times"]
        conv["T_G4_vs_G8"] = compare_on_output(solutions[4]["T_out"], solutions[8]["T_out"], t)
        conv["C_G4_vs_G8"] = compare_on_output(solutions[4]["C_out"], solutions[8]["C_out"], t)
        fourdec["T_G4_vs_G8"] = four_decimal_stats(solutions[4]["T_out"], solutions[8]["T_out"], t)
        fourdec["C_G4_vs_G8"] = four_decimal_stats(solutions[4]["C_out"], solutions[8]["C_out"], t)
        print("conv G4 G8", conv["T_G4_vs_G8"], conv["C_G4_vs_G8"])
        pub_level = 8
        paper_ok = fourdec["T_G4_vs_G8"]["paper_changed_cells"] == 0 and fourdec["C_G4_vs_G8"]["paper_changed_cells"] == 0
        abs_ok = conv["T_G4_vs_G8"]["max_abs"] <= 2e-5 and conv["C_G4_vs_G8"]["max_abs"] <= 2e-5
    else:
        pub_level = 4 if fourdec["C_G2_vs_G4"]["changed_cells"] or fourdec["T_G2_vs_G4"]["changed_cells"] else 2
        if pub_level == 2:
            pub_level = 4
    pub = solutions[pub_level]
    fvm = pub["fvm"]
    times = pub["times"]
    print("publishing", pub["tag"], "paper_ok", paper_ok, "abs_ok", abs_ok)

    print("time refinement")
    y0 = fvm.pack(np.full(fvm.n_nodes, T0), np.full(fvm.n_nodes, C0))
    atol = np.concatenate([np.full(fvm.n_nodes, atol_T / 5), np.full(fvm.n_nodes, atol_C / 5)])
    t2, Y2 = integrate_coupled(fvm, y0, T_END, Ta_fun, Ca_fun, rtol / 5, atol, 0.5)
    T2, C2 = extract_output(fvm, Y2[t2 > 0])
    time_sens = {"T": compare_on_output(pub["T_out"], T2, times), "C": compare_on_output(pub["C_out"], C2, times)}
    time_4dp = {"T": four_decimal_stats(pub["T_out"], T2, times), "C": four_decimal_stats(pub["C_out"], C2, times)}
    print("time sens", time_sens)

    print("frozen-D moisture probe")
    D_freeze = D0
    Bi_m = HM * R / D_freeze
    C_ref, moisture_truncation = converged_reference(Bi_m, D_freeze, R, OUTPUT_RADII_M, times, Ca_fun, C0)
    y0f = fvm.pack(np.full(fvm.n_nodes, T0), np.full(fvm.n_nodes, C0))
    atol = np.concatenate([np.full(fvm.n_nodes, atol_T), np.full(fvm.n_nodes, atol_C)])
    tf, Yf = integrate_coupled(fvm, y0f, T_END, Ta_fun, Ca_fun, rtol, atol, max_step, D_const=D_freeze)
    _, C_frozen = extract_output(fvm, Yf[tf > 0])
    frozen = compare_on_output(C_frozen, C_ref, times)
    nl_vs_frozen = compare_on_output(pub["C_out"], C_frozen, times)
    print("frozen vs analytic", frozen)
    print("nonlinear vs frozen", nl_vs_frozen)

    n = fvm.n_nodes
    D_field = moisture_diffusivity_q2(pub["Y"][:, n:], pub["Y"][:, :n])
    D_stats = {
        "D0": D0,
        "D_min": float(np.min(D_field)),
        "D_max": float(np.max(D_field)),
        "D_min_over_D0": float(np.min(D_field) / D0),
        "D_max_over_D0": float(np.max(D_field) / D0),
        "center_C_end": float(pub["C_out"][-1, 0]),
        "surface_C_end": float(pub["C_out"][-1, -1]),
        "center_T_end": float(pub["T_out"][-1, 0]),
        "surface_T_end": float(pub["T_out"][-1, -1]),
    }
    print("D stats", D_stats)

    bounds = assert_physical(pub["Y_full"][:, :n], pub["Y_full"][:, n:], Ta_fun, Ca_fun)
    cons_C = conservation_moisture(fvm, pub["times_full"], pub["Y_full"], Ca_fun)
    cons_T = conservation_heat(fvm, pub["times_full"], pub["Y_full"], Ta_fun)
    print("bounds", bounds)
    print("conservation C", cons_C)
    print("conservation T", cons_T)

    delivery = make_gate({
        "space_abs": abs_ok,
        "space_paper": paper_ok,
        "all_finite": np.isfinite(pub["Y_full"]).all(),
        "manufactured_solution": mms["T_max_abs"] <= 2e-5 and mms["C_max_abs"] <= 2e-5,
        "time_abs": time_sens["T"]["max_abs"] <= 2e-5 and time_sens["C"]["max_abs"] <= 2e-5,
        "time_paper": time_4dp["T"]["paper_changed_cells"] == 0 and time_4dp["C"]["paper_changed_cells"] == 0,
        "temperature_bounds": bounds["T_bounds_ok"],
        "moisture_bounds": bounds["C_bounds_ok"],
        "moisture_reference_truncation": moisture_truncation["passed"],
        "frozen_reference_error": frozen["max_abs"] <= 2e-5,
        "heat_balance": cons_T["relative_residual"] <= 1e-6,
        "moisture_balance": cons_C["relative_residual"] <= 1e-6,
    })
    print("delivery", delivery)

    paper_T = {f"h{th:g}_r{rc:g}": float(pub["T_out"][int(t) - 1, int(round(rc / 0.1))])
               for th, t in zip(TABLE_HOURS, TABLE_TIMES) for rc in TABLE_RADII_CM}
    paper_C = {f"h{th:g}_r{rc:g}": float(pub["C_out"][int(t) - 1, int(round(rc / 0.1))])
               for th, t in zip(TABLE_HOURS, TABLE_TIMES) for rc in TABLE_RADII_CM}

    validation = {
        "result_version": "q2-closeout-v1",
        "interpolation": Ta_fun.kind,
        "published_mesh": pub["tag"],
        "published_n_nodes": pub["n_nodes"],
        "mesh_levels": list(solutions.keys()),
        "solver": "coupled-FVM+BDF",
        "rtol": rtol, "atol_T": atol_T, "atol_C": atol_C, "max_step": max_step,
        "mms": mms,
        "grid_convergence": conv,
        "four_decimal_grid": fourdec,
        "time_sensitivity": time_sens,
        "four_decimal_time": time_4dp,
        "delivery_gate": delivery,
        "reference_truncation_C": moisture_truncation,
        "frozen_D_moisture_vs_analytic": frozen,
        "nonlinear_C_vs_frozen_D": nl_vs_frozen,
        "D_variation": D_stats,
        "conservation_T_10800s": cons_T,
        "conservation_C_10800s": cons_C,
        "physical_bounds": bounds,
        "paper_table_T": paper_T,
        "paper_table_C": paper_C,
        "elapsed_s": time.perf_counter() - t_wall0,
        "python": sys.version,
        "end_face_2d": "skipped_by_plan",
    }
    require_delivery(validation, RESULTS_DIR / "diagnostics/q2_delivery/latest.json")
    np.savez(
        RESULTS_DIR / "q2_solution.npz",
        mesh_level=pub_level,
        n_nodes=pub["n_nodes"],
        times=times,
        r=fvm.r,
        output_radii_m=OUTPUT_RADII_M,
        checkpoint_times=np.r_[0., 1., 60., 100., TABLE_TIMES],
        T_checkpoints=pub["Y_full"][np.r_[0., 1., 60., 100., TABLE_TIMES].astype(int), :n],
        C_checkpoints=pub["Y_full"][np.r_[0., 1., 60., 100., TABLE_TIMES].astype(int), n:],
        T_out=pub["T_out"],
        C_out=pub["C_out"],
        interpolation=np.array(Ta_fun.kind),
        rtol=rtol, atol_T=atol_T, atol_C=atol_C, max_step=max_step,
    )
    write_result_workbook(RESULTS_DIR / "result2.xlsx", pub["T_out"], pub["C_out"], times)
    write_paper_csv(RESULTS_DIR / "q2_table_temperature.csv", pub["T_out"], times)
    write_paper_csv(RESULTS_DIR / "q2_table_moisture.csv", pub["C_out"], times)
    plt = setup_mpl()
    plot_figures(plt, fvm, times, pub["Y"], pub["T_out"], pub["C_out"], Ta_fun, Ca_fun)

    (RESULTS_DIR / "q2_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8",
    )
    print("elapsed_s", validation["elapsed_s"])
    print("wrote results to", RESULTS_DIR)



if __name__ == "__main__":
    main()
'''

# ========================================================================
# Module: q3_balance.py
# ========================================================================
SOURCES['q3_balance'] = r'''"""Continuous-solution balance integrals for the accepted Q3 effective model."""
import numpy as np
from numpy.polynomial.legendre import leggauss
from appendix3 import heat_capacity, heat_capacity_deriv, moisture_diffusivity_q2
from utils import R, L, H, HM


def audit_segment(fvm, sol, Ta_fun, Ca_fun, t_end=None, orders=(4,8)):
    if sol.sol is None:
        raise ValueError("balance audit requires a dense solution")
    n = fvm.n_nodes
    start = float(sol.sol.ts[0])
    end = float(sol.sol.ts[-1]) if t_end is None else float(t_end)
    if not start < end <= sol.sol.ts[-1]+1e-9:
        raise ValueError("audit outside dense-solution interval")
    edges = np.r_[sol.sol.ts[sol.sol.ts < end],end]
    edges = np.unique(edges)
    z0, z1 = sol.sol(start), sol.sol(end)
    factor = 2*np.pi*L
    def energy(z):
        return float(factor*np.dot(fvm.W,heat_capacity(z[n:])*(z[:n]-28.)))
    def quadrature(order):
        gx,gw=leggauss(order)
        total=np.zeros(3)
        for j in range(0,len(edges)-1,64):
            aa,bb=edges[j:-1][:64],edges[j+1:][:64]
            tt=((aa+bb)[:,None]/2+(bb-aa)[:,None]/2*gx).ravel()
            Y=sol.sol(tt);T,C=Y[:n],Y[n:]
            Ta,Ca=np.asarray(Ta_fun(tt)),np.asarray(Ca_fun(tt))
            D=moisture_diffusivity_q2(C,T)
            Df=2*D[:-1]*D[1:]/np.maximum(D[:-1]+D[1:],1e-300)
            F=-fvm.r_half[:,None]*Df*np.diff(C,axis=0)/fvm.dr_face[:,None]
            flows=np.vstack([np.zeros((1,len(tt))),F,R*HM*(C[-1]-Ca)])
            Cdot=-np.diff(flows,axis=0)/fvm.W[:,None]
            vals=np.vstack([R*HM*(C[-1]-Ca),factor*R*H*(Ta-T[-1]),
                factor*np.sum(fvm.W[:,None]*heat_capacity_deriv(C)*(T-28.)*Cdot,axis=0)])
            weights=((bb-aa)[:,None]/2*gw).ravel()
            total+=vals@weights
        return total
    integrals={str(o):quadrature(o).tolist() for o in orders}
    return {"start_s":start,"end_s":end,"accepted_intervals":len(edges)-1,
            "M_start":float(fvm.W@z0[n:]),"M_end":float(fvm.W@z1[n:]),
            "E_start":energy(z0),"E_end":energy(z1),"integrals_by_order":integrals}


def combine(parts):
    if not parts:
        raise ValueError('no balance segments')
    for left, right in zip(parts, parts[1:]):
        if abs(left['end_s']-right['start_s']) > 1e-9:
            raise ValueError('balance segments have a time gap or overlap')
        for field in ('M', 'E'):
            if not np.isclose(left[field+'_end'], right[field+'_start'], rtol=1e-12, atol=1e-14):
                raise ValueError('balance segments have a state discontinuity')
    I=np.sum([p['integrals_by_order']['8'] for p in parts],axis=0)
    I4=np.sum([p['integrals_by_order']['4'] for p in parts],axis=0)
    M0,M1=parts[0]['M_start'],parts[-1]['M_end']
    E0,E1=parts[0]['E_start'],parts[-1]['E_end']
    mass_denom=max(abs(M0-M1),abs(I[0]),1e-18)
    heat_denom=max(abs(E1-E0-I[2]),abs(I[1]),1e-12)
    return {
        'moisture':{'M0':M0,'M_end':M1,'surface_integral':float(I[0]),
                    'relative_residual':float(abs(M1-M0+I[0])/mass_denom)},
        'heat':{'E_end_minus_E0':E1-E0,'composition_correction':float(I[2]),'Q_surface':float(I[1]),
                'relative_residual':float(abs(E1-E0-I[2]-I[1])/heat_denom)},
        'quadrature_relative_difference':{'moisture':float(abs(I[0]-I4[0])/mass_denom),
            'heat_and_composition':float((abs(I[1]-I4[1])+abs(I[2]-I4[2]))/heat_denom)},
        'parts':parts,
        'interpretation':'Integrated effective equation with B_prime(C)*(T-28)*Cdot correction; not full multiphase energy conservation.'}
'''

# ========================================================================
# Module: problem3.py
# ========================================================================
SOURCES['problem3'] = r'''"""Problem 3: full coupled drying until every interior node is below 0.15 kg/kg."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from appendix3 import moisture_diffusivity_q2
from delivery import make_gate, require_delivery
from problem2 import conservation_heat, conservation_moisture, extract_output, setup_mpl
from radial_coupled import CoupledRadialFVM
from radial_fvm import graded_radial_nodes
from utils import (
    C0,
    FIGURES_DIR,
    RESULTS_DIR,
    T0,
    PchipOven,
    load_oven_table,
)

T_SWITCH = 14400.0
TA_AFTER = 50.0
CA_AFTER = 0.05
C_THRESH = 0.15
T_HARD_CAP = 21.0 * 24.0 * 3600.0
OUTPUT_RADII_M = 0.001 * np.arange(21)
TABLE_RADII_CM = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
EXCEL_DT = 60.0
TABLE_DT_H = 6.0
OVEN_N_EXPECTED = 241

# First-round baseline; recorded after the run, not treated as a prior user decision.
RTOL = 1e-9
ATOL_T = 1e-8
ATOL_C = 1e-10
MAX_STEP_EARLY = 2.0
MAX_STEP_LATE = 60.0


class ExtendedOven:
    """PCHIP through attachment 1 on [0, 4 h]; constant value strictly after 4 h."""

    def __init__(self, pchip: PchipOven, after_value: float, t_switch: float = T_SWITCH):
        self.pchip = pchip
        self.after = float(after_value)
        self.t_switch = float(t_switch)
        self.kind = pchip.kind
        self.t = pchip.t
        self.y = pchip.y

    def __call__(self, t):
        if np.ndim(t) == 0:
            tt = float(t)
            if tt <= self.t_switch:
                return float(self.pchip(tt))
            return self.after
        tt = np.asarray(t, dtype=float)
        out = np.empty_like(tt, dtype=float)
        inside = tt <= self.t_switch
        if np.any(inside):
            out[inside] = np.asarray(self.pchip(tt[inside]), dtype=float)
        out[~inside] = self.after
        return out


def load_q3_inputs() -> tuple[ExtendedOven, ExtendedOven, np.ndarray]:
    t, Ta, Ca = load_oven_table()
    if t.size != OVEN_N_EXPECTED or abs(t[-1] - T_SWITCH) > 1e-12:
        raise ValueError(f"expected {OVEN_N_EXPECTED} oven records ending at {T_SWITCH}, got {t.size}, t_end={t[-1]}")
    if abs(Ta[0] - T0) > 1e-12:
        raise ValueError(f"Ta(0)={Ta[0]} != T0={T0}")
    Ta_pchip = PchipOven(t, Ta)
    Ca_pchip = PchipOven(t, Ca)
    for tj, yj in zip(t, Ta):
        if abs(float(Ta_pchip(tj)) - float(yj)) > 1e-12:
            raise RuntimeError(f"PCHIP misses Ta knot t={tj}")
    for tj, yj in zip(t, Ca):
        if abs(float(Ca_pchip(tj)) - float(yj)) > 1e-12:
            raise RuntimeError(f"PCHIP misses Ca knot t={tj}")
    Ta_fun = ExtendedOven(Ta_pchip, TA_AFTER)
    Ca_fun = ExtendedOven(Ca_pchip, CA_AFTER)
    jump = {
        "Ta_at_4h": float(Ta_fun(T_SWITCH)),
        "Ca_at_4h": float(Ca_fun(T_SWITCH)),
        "Ta_after": float(Ta_fun(T_SWITCH + 1e-9)),
        "Ca_after": float(Ca_fun(T_SWITCH + 1e-9)),
    }
    print("oven 4h jump", jump, flush=True)
    return Ta_fun, Ca_fun, t


def atol_vector(n: int, atol_T: float = ATOL_T, atol_C: float = ATOL_C) -> np.ndarray:
    return np.concatenate([np.full(n, float(atol_T)), np.full(n, float(atol_C))])


def max_moisture_event(n_nodes: int):
    def event(t, y):
        return float(np.max(y[n_nodes:]) - C_THRESH)

    event.terminal = True
    event.direction = -1.0
    return event


def integrate_segment(
    fvm: CoupledRadialFVM,
    y0,
    t0: float,
    t1: float,
    Ta_fun,
    Ca_fun,
    rtol: float,
    atol: np.ndarray,
    max_step: float,
    *,
    t_eval=None,
    events=None,
    dense_output: bool = False,
    first_step=None,
    label: str = "",
    balance_audit: bool = False,
):
    n = fvm.n_nodes
    y0 = np.asarray(y0, dtype=float)
    t0 = float(t0)
    t1 = float(t1)
    if t1 <= t0 + 1e-15:
        raise ValueError(f"empty interval [{t0}, {t1}]")
    nfev = [0]
    t_print = [t0]
    t_wall0 = time.perf_counter()

    def rhs(t, y):
        nfev[0] += 1
        interval = 3600.0 if t < T_SWITCH + 12.0 * 3600.0 else 6.0 * 3600.0
        if t - t_print[0] >= interval:
            C = y[n:]
            imax = int(np.argmax(C))
            elapsed = time.perf_counter() - t_wall0
            print(
                f"    {label}t={t/3600.0:.3f} h  maxC={float(C[imax]):.6f}  "
                f"rmax={fvm.r[imax]*100:.4f} cm  nfev={nfev[0]}  wall={elapsed:.1f}s",
                flush=True,
            )
            t_print[0] = float(t)
        return fvm.rhs(t, y, float(Ta_fun(t)), float(Ca_fun(t)))

    kwargs = dict(
        fun=rhs,
        t_span=(t0, t1),
        y0=y0,
        method="BDF",
        rtol=rtol,
        atol=np.asarray(atol, dtype=float),
        max_step=max_step,
        dense_output=dense_output or balance_audit,
        vectorized=False,
        jac_sparsity=fvm.jac_sparsity(),
    )
    if t_eval is not None:
        te = np.asarray(t_eval, dtype=float)
        te = te[(te > t0 + 1e-14) & (te <= t1 + 1e-12)]
        if te.size:
            kwargs["t_eval"] = te
    if events is not None:
        kwargs["events"] = events
    if first_step is not None:
        kwargs["first_step"] = min(float(first_step), 0.5 * max_step, t1 - t0)

    sol = solve_ivp(**kwargs)
    if not sol.success:
        raise RuntimeError(f"coupled BDF failed on [{t0}, {t1}] {label}: {sol.message}")
    if balance_audit:
        from q3_balance import audit_segment
        sol.balance_audit = audit_segment(fvm, sol, Ta_fun, Ca_fun)
        if not dense_output:
            sol.sol = None
    return sol


def excel_times(t_rep: float) -> np.ndarray:
    t_rep = float(t_rep)
    grid = np.arange(EXCEL_DT, np.floor(t_rep / EXCEL_DT) * EXCEL_DT + 0.5 * EXCEL_DT, EXCEL_DT)
    if grid.size == 0 or grid[-1] < t_rep - 1e-12:
        times = np.concatenate([grid, [t_rep]]) if grid.size else np.array([t_rep])
    elif abs(grid[-1] - t_rep) <= 1e-9:
        times = grid
    else:
        times = np.concatenate([grid, [t_rep]])
    return times


def table_hours(t_rep_h: float) -> np.ndarray:
    t_rep_h = float(t_rep_h)
    hrs = np.arange(TABLE_DT_H, t_rep_h + 1e-12, TABLE_DT_H)
    if hrs.size == 0 or abs(hrs[-1] - t_rep_h) > 1e-10:
        hrs = np.concatenate([hrs, [t_rep_h]]) if hrs.size else np.array([t_rep_h])
    return hrs


def monitor_from_Y(fvm: CoupledRadialFVM, times: np.ndarray, Y: np.ndarray) -> dict:
    n = fvm.n_nodes
    C = Y[:, n:]
    imax = np.argmax(C, axis=1)
    M = C[np.arange(C.shape[0]), imax]
    rmax = fvm.r[imax]
    dC = np.diff(C, axis=1)
    # Allow tiny positive bumps from rounding; count clear interior increases.
    n_increase = int(np.sum(dC > 1e-10))
    center_is_max = imax == 0
    return {
        "times": times,
        "M": M,
        "rmax_m": rmax,
        "imax": imax,
        "center_is_max_frac": float(np.mean(center_is_max)),
        "n_radial_increases": n_increase,
        "C_center": C[:, 0].copy(),
        "C_surface": C[:, -1].copy(),
        "T_center": Y[:, 0].copy(),
        "T_surface": Y[:, n - 1].copy(),
    }


def locate_threshold(
    fvm: CoupledRadialFVM,
    Ta_fun,
    Ca_fun,
    t_left: float,
    y_left: np.ndarray,
    t_right: float,
    rtol: float,
    atol: np.ndarray,
):
    """Bracketed root of max_i C_i(t) - 0.15 on a locally refined dense interpolant."""
    n = fvm.n_nodes
    event = max_moisture_event(n)
    t_pad = max(30.0, 2.0 * (t_right - t_left))
    t_hi = t_right + t_pad
    sol = integrate_segment(
        fvm, y_left, t_left, t_hi, Ta_fun, Ca_fun, rtol, atol,
        max_step=0.5, events=event, dense_output=True, first_step=0.05,
        label="zoom ",
    )
    if sol.t_events is None or len(sol.t_events[0]) == 0:
        C_end = sol.y[n:, -1]
        raise RuntimeError(
            f"zoom missed threshold on [{t_left}, {t_hi}]; "
            f"maxC(end)={float(np.max(C_end))}"
        )
    t_solver = float(sol.t_events[0][0])
    y_solver = np.asarray(sol.y_events[0][0], dtype=float)

    def g(t):
        return float(np.max(sol.sol(float(t))[n:]) - C_THRESH)

    g_left = g(t_left)
    t_lo = t_left
    t_hi_root = float(sol.t[-1])
    g_hi = g(t_hi_root)
    if g_left <= 0.0:
        raise RuntimeError(f"zoom left end already <= threshold: t={t_left}, g={g_left}")
    if g_hi > 0.0 and abs(g_hi) <= 1e-8:
        t_star = t_solver
    elif g_hi > 0.0:
        raise RuntimeError(f"zoom right end still above threshold: t={t_hi_root}, g={g_hi}")
    else:
        t_star = float(brentq(g, t_lo, t_hi_root, xtol=1e-4, rtol=1e-12, maxiter=200))
    y_star = np.asarray(sol.sol(t_star), dtype=float)
    C_star = y_star[n:]
    imax = int(np.argmax(C_star))
    info = {
        "t_star_s": t_star,
        "t_star_h": t_star / 3600.0,
        "t_solver_event_s": t_solver,
        "event_solver_minus_brent_s": t_solver - t_star,
        "M_star": float(C_star[imax]),
        "g_star": float(C_star[imax] - C_THRESH),
        "rmax_star_m": float(fvm.r[imax]),
        "rmax_star_cm": float(fvm.r[imax] * 100.0),
        "imax_star": imax,
        "center_is_max": bool(imax == 0),
        "C_center_star": float(C_star[0]),
        "C_surface_star": float(C_star[-1]),
        "T_center_star": float(y_star[0]),
        "T_surface_star": float(y_star[n - 1]),
        "bracket_s": [float(t_left), float(t_hi_root)],
        "zoom_nfev": int(sol.nfev),
    }
    return t_star, y_star, sol, info, y_solver


def find_strict_report(eval_M, t_star: float, t_hi: float, margin: float = 0.0) -> dict:
    target = C_THRESH - float(margin)
    t_star = float(t_star)
    t_hi = float(t_hi)
    if not (np.isfinite([t_star, t_hi, margin]).all() and 0 <= margin < C_THRESH and t_hi > t_star):
        raise ValueError('invalid strict-report interval or margin')

    original_eval = eval_M
    def eval_M(t):
        if not t_star <= t <= t_hi:
            raise RuntimeError('strict report requested outside verified continuation')
        value = float(original_eval(t))
        if not np.isfinite(value):
            raise RuntimeError('nonfinite moisture in strict report')
        return value

    def h(t):
        return float(eval_M(t) - target)

    h0 = h(t_star)
    h1 = h(t_hi)
    if h1 >= 0.0:
        raise RuntimeError(f"M(t_hi)={eval_M(t_hi)} still >= {target}")
    if h0 < 0.0:
        t_cross = t_star
    else:
        t_cross = float(brentq(h, t_star, t_hi, xtol=1e-4, rtol=1e-12, maxiter=200))
    t_rep = float(np.floor(max(t_cross, t_star)) + 1.0)
    # Walk forward in seconds until unrounded moisture is strictly below the target.
    for _ in range(10000):
        if float(eval_M(t_rep)) < target:
            break
        t_rep += 1.0
    else:
        raise RuntimeError("failed to find integer-second report time below threshold")
    t_hour4 = np.ceil((t_rep / 3600.0) * 10000.0) / 10000.0
    t_hour4_s = 3600.0 * t_hour4
    if float(eval_M(t_hour4_s)) >= target:
        raise RuntimeError("four-decimal hour report does not satisfy the target")
    t_grid60 = EXCEL_DT * np.ceil(t_star / EXCEL_DT)
    if t_grid60 < t_rep:
        t_grid60 = EXCEL_DT * np.ceil(t_rep / EXCEL_DT)
    return {
        "t_cross_s": t_cross,
        "t_rep_s": float(t_rep),
        "t_rep_h": float(t_rep) / 3600.0,
        "M_rep": float(eval_M(t_rep)),
        "t_hour4_h": float(t_hour4),
        "t_hour4_s": float(t_hour4_s),
        "M_hour4": float(eval_M(t_hour4_s)),
        "t_grid60_s": float(t_grid60),
        "M_grid60": float(eval_M(t_grid60)),
        "margin": float(margin),
        "strict_below_rep": bool(float(eval_M(t_rep)) < C_THRESH),
        "strict_below_hour4": bool(float(eval_M(t_hour4_s)) < C_THRESH),
    }


def slope_at(eval_M, t: float, h: float = 1.0) -> float:
    return float(eval_M(t + h) - eval_M(t - h)) / (2.0 * h)


def run_case(
    level: int,
    Ta_fun,
    Ca_fun,
    t_max: float,
    rtol: float,
    atol_T: float,
    atol_C: float,
    max_step_early: float,
    max_step_late: float,
    tag: str,
    audit_balances: bool = False,
):
    r = graded_radial_nodes(level)
    fvm = CoupledRadialFVM(r)
    n = fvm.n_nodes
    print(f"\n=== {tag} nodes={n} t_max={t_max/3600:.2f} h ===", flush=True)
    y0 = fvm.pack(np.full(n, T0), np.full(n, C0))
    atol = atol_vector(n, atol_T, atol_C)
    t_eval_early = np.arange(EXCEL_DT, T_SWITCH + 0.5 * EXCEL_DT, EXCEL_DT)
    t_wall0 = time.perf_counter()
    sol1 = integrate_segment(
        fvm, y0, 0.0, T_SWITCH, Ta_fun, Ca_fun, rtol, atol,
        max_step=max_step_early, t_eval=t_eval_early, first_step=0.05, label=f"{tag} early ", balance_audit=audit_balances,
    )
    y_switch = sol1.y[:, -1]
    times1 = np.concatenate([[0.0], sol1.t])
    Y1 = np.vstack([y0, sol1.y.T])
    M_switch = float(np.max(y_switch[n:]))
    print(f"  {tag} 4h maxC={M_switch:.6f}  C_center={y_switch[n]:.6f}  wall={time.perf_counter()-t_wall0:.1f}s", flush=True)
    if M_switch <= C_THRESH:
        raise RuntimeError("threshold already reached at 4 h; unexpected for this model")

    event = max_moisture_event(n)
    t_eval_late = np.unique(np.r_[np.arange(T_SWITCH + EXCEL_DT, t_max, EXCEL_DT), t_max])
    sol2 = integrate_segment(
        fvm, y_switch, T_SWITCH, t_max, Ta_fun, Ca_fun, rtol, atol,
        max_step=max_step_late, t_eval=t_eval_late, events=event,
        first_step=0.2, label=f"{tag} late ", dense_output=audit_balances,
    )
    if sol2.t_events is None or len(sol2.t_events[0]) == 0:
        M_end = float(np.max(sol2.y[n:, -1]))
        print(f"  {tag} no event by {t_max/3600:.2f} h, maxC={M_end:.6f}; extending to hard cap", flush=True)
        if t_max >= T_HARD_CAP - 1.0:
            raise RuntimeError(f"{tag} still above threshold at {T_HARD_CAP/3600:.1f} h, maxC={M_end}")
        y_cont = sol2.y[:, -1]
        t_cont = float(sol2.t[-1])
        t_eval_cap = np.arange(t_cont + EXCEL_DT, T_HARD_CAP + 0.5 * EXCEL_DT, EXCEL_DT)
        sol2b = integrate_segment(
            fvm, y_cont, t_cont, T_HARD_CAP, Ta_fun, Ca_fun, rtol, atol,
            max_step=max_step_late, t_eval=t_eval_cap, events=event,
            first_step=0.2, label=f"{tag} cap ", dense_output=audit_balances,
        )
        if sol2b.t_events is None or len(sol2b.t_events[0]) == 0:
            raise RuntimeError(
                f"{tag} not dry at {T_HARD_CAP/3600:.1f} h, maxC={float(np.max(sol2b.y[n:, -1]))}"
            )
        times2 = np.concatenate([sol2.t[sol2.t > T_SWITCH + 1e-12], sol2b.t[sol2b.t > t_cont + 1e-12]])
        Y2 = np.vstack([sol2.y[:, sol2.t > T_SWITCH + 1e-12].T, sol2b.y[:, sol2b.t > t_cont + 1e-12].T])
        t_event_raw = float(sol2b.t_events[0][0])
        y_event_raw = np.asarray(sol2b.y_events[0][0], dtype=float)
    else:
        times2 = sol2.t[sol2.t > T_SWITCH + 1e-12]
        Y2 = sol2.y[:, sol2.t > T_SWITCH + 1e-12].T
        t_event_raw = float(sol2.t_events[0][0])
        y_event_raw = np.asarray(sol2.y_events[0][0], dtype=float)

    times = np.concatenate([times1, times2])
    Y = np.vstack([Y1, Y2])
    order = np.argsort(times)
    times, Y = times[order], Y[order]
    uniq = np.concatenate([[True], np.diff(times) > 1e-12])
    times, Y = times[uniq], Y[uniq]

    M_hist = np.max(Y[:, n:], axis=1)
    above = np.where(M_hist > C_THRESH + 1e-14)[0]
    if above.size == 0:
        raise RuntimeError(f"{tag} never above threshold")
    i_left = int(above[-1])
    t_left = float(times[i_left])
    y_left = Y[i_left]
    if t_left >= t_event_raw:
        i_left = max(0, i_left - 1)
        t_left = float(times[i_left])
        y_left = Y[i_left]
    t_star, y_star, sol_zoom, event_info, y_solver = locate_threshold(
        fvm, Ta_fun, Ca_fun, t_left, y_left, t_event_raw, rtol, atol,
    )
    event_info["t_event_raw_s"] = t_event_raw
    event_info["M_event_raw"] = float(np.max(y_event_raw[n:]))

    balance_parts = []
    if audit_balances:
        from q3_balance import audit_segment
        # Follow the same trajectory used for reporting, including the zoom restart.
        balance_parts = [sol1.balance_audit]
        if 'sol2b' in locals():
            balance_parts.append(audit_segment(fvm, sol2, Ta_fun, Ca_fun))
            late_sol = sol2b
        else:
            late_sol = sol2
        balance_parts.append(audit_segment(fvm, late_sol, Ta_fun, Ca_fun, t_end=t_left))
        balance_parts.append(audit_segment(fvm, sol_zoom, Ta_fun, Ca_fun, t_end=t_star))
        sol2.sol = None
        if 'sol2b' in locals():
            sol2b.sol = None

    t_pad = 3600.0
    sol_after = integrate_segment(
        fvm, y_star, t_star, t_star + t_pad, Ta_fun, Ca_fun, rtol, atol,
        max_step=min(max_step_late, 5.0), dense_output=True, first_step=0.05,
        label=f"{tag} after ",
    )

    def eval_M(t):
        return float(np.max(eval_y(float(t))[n:]))

    def eval_y(t):
        tt = float(t)
        if abs(tt - t_star) <= 1e-12:
            return y_star.copy()
        if tt < t_star:
            if tt < times[0]:
                raise ValueError(f"state requested before initial time: {tt}")
            if tt >= t_left:
                return np.asarray(sol_zoom.sol(tt), dtype=float)
            k = max(0, int(np.searchsorted(times, tt, side="right"))-1)
            if abs(times[k]-tt)<1e-8:
                return Y[k].copy()
            short = integrate_segment(fvm,Y[k],float(times[k]),tt,Ta_fun,Ca_fun,
                min(rtol,1e-10),atol/10,max_step=1.0,first_step=0.05,label="matched time ")
            return short.y[:,-1]
        if tt > float(sol_after.t[-1])+1e-9:
            raise ValueError(f"state requested beyond continuation: {tt}")
        return np.asarray(sol_after.sol(tt), dtype=float)

    dMdt = slope_at(eval_M, min(t_star + 2.0, t_star + 0.5 * t_pad), h=1.0)
    event_info["dMdt_per_s"] = dMdt
    event_info["dMdt_per_h"] = dMdt * 3600.0

    T_out, C_out = extract_output(fvm, Y)
    mon = monitor_from_Y(fvm, times, Y)
    elapsed = time.perf_counter() - t_wall0
    print(
        f"  {tag} t*={t_star/3600:.6f} h  rmax={event_info['rmax_star_cm']:.4f} cm  "
        f"M*={event_info['M_star']:.8f}  dM/dt={dMdt:.3e}/s  wall={elapsed:.1f}s",
        flush=True,
    )
    return dict(
        tag=tag, level=level, fvm=fvm, n_nodes=n, times=times, Y=Y,
        T_out=T_out, C_out=C_out, t_star=t_star, y_star=y_star,
        eval_M=eval_M, eval_y=eval_y, sol_after=sol_after, event=event_info,
        monitor=mon, elapsed_s=elapsed, rtol=rtol, atol_T=atol_T, atol_C=atol_C,
        max_step_early=max_step_early, max_step_late=max_step_late, t_max=t_max,
        y_switch=y_switch,
        balance_parts=balance_parts,
    )


def run_probe(Ta_fun, Ca_fun) -> dict:
    """Cheap uniform-mesh estimate of t* to size the production interval."""
    r = np.linspace(0.0, 0.02, 41)
    fvm = CoupledRadialFVM(r)
    n = fvm.n_nodes
    y0 = fvm.pack(np.full(n, T0), np.full(n, C0))
    atol = atol_vector(n, 1e-6, 1e-8)
    print("\n=== probe N=41 ===", flush=True)
    sol1 = integrate_segment(
        fvm, y0, 0.0, T_SWITCH, Ta_fun, Ca_fun, 1e-6, atol, max_step=30.0,
        first_step=0.2, label="probe early ",
    )
    event = max_moisture_event(n)
    sol2 = integrate_segment(
        fvm, sol1.y[:, -1], T_SWITCH, T_HARD_CAP, Ta_fun, Ca_fun, 1e-6, atol,
        max_step=120.0, events=event, first_step=1.0, label="probe late ",
    )
    if sol2.t_events is None or len(sol2.t_events[0]) == 0:
        raise RuntimeError(f"probe not dry by 14 d, maxC={float(np.max(sol2.y[n:, -1]))}")
    t_star = float(sol2.t_events[0][0])
    y_e = np.asarray(sol2.y_events[0][0], dtype=float)
    imax = int(np.argmax(y_e[n:]))
    info = {
        "n_nodes": n,
        "t_star_s": t_star,
        "t_star_h": t_star / 3600.0,
        "M_star": float(y_e[n + imax]),
        "rmax_cm": float(fvm.r[imax] * 100.0),
        "C_center": float(y_e[n]),
        "C_surface": float(y_e[-1]),
        "nfev": int(sol1.nfev + sol2.nfev),
    }
    print("probe", info, flush=True)
    return info


def overlap_q2(case) -> dict:
    path = RESULTS_DIR / "q2_solution.npz"
    if not path.exists():
        return {"available": False}
    z = np.load(path)
    fvm = case["fvm"]
    n = fvm.n_nodes
    idx = fvm.output_indices()
    t_check = np.array([1800.0, 3600.0, 7200.0, 9000.0])
    q2_times = np.asarray(z["times"], dtype=float)
    T_q2 = np.asarray(z["T_out"], dtype=float)
    C_q2 = np.asarray(z["C_out"], dtype=float)
    rows = {}
    for t in t_check:
        k = int(np.argmin(np.abs(case["times"] - t)))
        if abs(case["times"][k] - t) > 1e-8:
            rows[f"t{int(t)}"] = {"matched": False}
            continue
        jq = int(np.argmin(np.abs(q2_times - t)))
        if abs(q2_times[jq] - t) > 1e-8:
            rows[f"t{int(t)}"] = {"matched": False}
            continue
        T = case["Y"][k, :n][idx]
        C = case["Y"][k, n:][idx]
        rows[f"t{int(t)}"] = {
            "matched": True,
            "T_max_abs": float(np.max(np.abs(T - T_q2[jq]))),
            "C_max_abs": float(np.max(np.abs(C - C_q2[jq]))),
            "T_center_diff": float(T[0] - T_q2[jq, 0]),
            "C_center_diff": float(C[0] - C_q2[jq, 0]),
            "C_surface_diff": float(C[-1] - C_q2[jq, -1]),
        }
    return {"available": True, "note": "PCHIP stencils differ near 3 h endpoint", "checks": rows}


def sample_state(case, t: float) -> tuple[np.ndarray, np.ndarray]:
    fvm = case["fvm"]
    n = fvm.n_nodes
    y = case["eval_y"](float(t))
    T, C = y[:n], y[n:]
    return T, C


def output_row(fvm, C: np.ndarray) -> np.ndarray:
    return np.asarray(C[fvm.output_indices()], dtype=float)


def build_output_tables(case, t_rep: float) -> dict:
    fvm = case["fvm"]
    times_x = excel_times(t_rep)
    C_excel = np.empty((times_x.size, 21), dtype=float)
    T_excel = np.empty_like(C_excel)
    n = fvm.n_nodes
    idx = fvm.output_indices()
    t_star = case["t_star"]
    times = case["times"]
    Y = case["Y"]
    for i, t in enumerate(times_x):
        if t <= times[-1] + 1e-12 and t < t_star - 1e-9:
            j = int(np.argmin(np.abs(times - t)))
            if abs(times[j] - t) > 1.0:
                raise RuntimeError(f"missing 60 s sample at t={t}, nearest {times[j]}")
            T_excel[i] = Y[j, :n][idx]
            C_excel[i] = Y[j, n:][idx]
        else:
            y = case["eval_y"](float(t))
            T_excel[i] = y[:n][idx]
            C_excel[i] = y[n:][idx]
    hrs = table_hours(t_rep / 3600.0)
    C_table = np.empty((hrs.size, TABLE_RADII_CM.size), dtype=float)
    paper_map = {}
    r_idx = {round(0.1 * j, 10): j for j in range(21)}
    for i, th in enumerate(hrs):
        t = 3600.0 * float(th)
        k = int(np.argmin(np.abs(times_x - t)))
        if abs(times_x[k] - t) > 1.0 and abs(t - t_rep) > 1.0:
            # 6 h marks lie on the 60 s grid; end time may be the extra row.
            y = case["eval_y"](t) if t >= t_star - 1e-9 else None
            if y is None:
                j = int(np.argmin(np.abs(times - t)))
                row = Y[j, n:][idx]
            else:
                row = y[n:][idx]
        else:
            row = C_excel[k]
        for rc, col in zip(TABLE_RADII_CM, range(5)):
            C_table[i, col] = float(row[r_idx[float(rc)]])
            paper_map[f"h{th:.6g}_r{rc:g}"] = float(row[r_idx[float(rc)]])
    return {
        "excel_times": times_x,
        "C_excel": C_excel,
        "T_excel": T_excel,
        "table_hours": hrs,
        "C_table": C_table,
        "paper_C": paper_map,
    }


def write_result3_xlsx(path: Path, C_out: np.ndarray, times: np.ndarray, *, validation):
    """All numerical checks must pass before calling the workbook author."""
    from q3_closeout import export_workbook, require_q3_delivery
    require_q3_delivery(validation, RESULTS_DIR / "diagnostics/q3_closeout/pre_export.json")
    export_workbook(path, C_out, times, validation)


def write_table5_csv(path: Path, hours: np.ndarray, C_table: np.ndarray):
    lines = ["t_h," + ",".join(f"r_{rc:g}cm" for rc in TABLE_RADII_CM)]
    for th, row in zip(hours, C_table):
        bits = [f"{float(th):.8f}"] + [f"{float(v):.10f}" for v in row]
        lines.append(",".join(bits))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def physical_bounds(case, Ta_fun, Ca_fun) -> dict:
    n = case["n_nodes"]
    T = case["Y"][:, :n]
    C = case["Y"][:, n:]
    Ta_max = max(float(np.max(Ta_fun.y)), TA_AFTER)
    info = {
        "T_min": float(T.min()),
        "T_max": float(T.max()),
        "C_min": float(C.min()),
        "C_max": float(C.max()),
        "T_below_28": float(max(0.0, 28.0 - T.min())),
        "T_above_Ta_max": float(max(0.0, T.max() - Ta_max)),
        "C_above_C0": float(max(0.0, C.max() - C0)),
        "C_negative": float(max(0.0, -C.min())),
        "Ta_max": Ta_max,
        "Ca_range_knots": [float(np.min(Ca_fun.y)), float(np.max(Ca_fun.y))],
    }
    info["T_bounds_ok"] = info["T_below_28"] <= 1e-6 and info["T_above_Ta_max"] <= 0.05
    info["C_bounds_ok"] = info["C_above_C0"] <= 1e-8 and info["C_negative"] <= 1e-12
    return info


def plot_figures(plt, pub, tables, t_rep: float, Ta_fun):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fvm = pub["fvm"]
    n = fvm.n_nodes
    mon = pub["monitor"]
    t_h = mon["times"] / 3600.0
    t_star_h = pub["t_star"] / 3600.0
    t_rep_h = t_rep / 3600.0

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.axhline(C_THRESH, color="0.4", lw=1.0, ls="--", label=r"阈值 $0.15$")
    ax.plot(t_h, mon["M"], lw=1.2, label=r"全网格 $\max C$")
    ax.plot(t_h, mon["C_center"], lw=1.2, ls="-.", label="中心")
    ax.plot(t_h, mon["C_surface"], lw=1.2, ls=":", label="表面")
    ax.axvline(t_star_h, color="0.2", lw=0.8, ls=":")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel(r"干基含水率 $C$ (kg/kg)")
    ax.set_xlim(0, t_rep_h)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q3_C_max_history.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(t_h, mon["rmax_m"] * 100.0, lw=1.2)
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel(r"最大含水率位置 $r$ (cm)")
    ax.set_xlim(0, t_rep_h)
    ax.set_ylim(-0.02, 2.05)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q3_max_location.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    r_cm = fvm.r * 100.0
    hrs = tables["table_hours"]
    t_end_h = float(hrs[-1])
    if t_end_h > 72.0:
        show = np.arange(24.0, t_end_h + 1e-9, 24.0)
        if abs(show[-1] - t_end_h) > 1e-6:
            show = np.concatenate([show, [t_end_h]])
    elif hrs.size > 10:
        show = np.unique(np.concatenate([hrs[::2], hrs[-1:]]))
    else:
        show = hrs
    for th in show:
        t = 3600.0 * float(th)
        if t < pub["t_star"] - 1e-9:
            j = int(np.argmin(np.abs(pub["times"] - t)))
            C = pub["Y"][j, n:]
        else:
            C = pub["eval_y"](t)[n:]
        ax.plot(r_cm, C, lw=1.2, label=fr"$t={th:g}\,\mathrm{{h}}$")
    ax.set_xlabel("半径 $r$ (cm)")
    ax.set_ylabel(r"干基含水率 $C$ (kg/kg)")
    ax.set_xlim(0, 2)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q3_C_profiles.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    mask = mon["times"] >= pub["t_star"] - 6 * 3600.0
    if np.count_nonzero(mask) < 5:
        mask = np.ones_like(mon["times"], dtype=bool)
    ax.axhline(C_THRESH, color="0.4", lw=1.0, ls="--", label=r"阈值 $0.15$")
    ax.plot(t_h[mask], mon["M"][mask], lw=1.2, label=r"$\max C$")
    ax.axvline(t_star_h, color="0.2", lw=0.8, ls=":", label=fr"$t_*={t_star_h:.3f}\,\mathrm{{h}}$")
    ax.axvline(t_rep_h, color="0.2", lw=0.8, ls="-.", label=fr"$t_{{\mathrm{{rep}}}}={t_rep_h:.3f}\,\mathrm{{h}}$")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel(r"干基含水率 $C$ (kg/kg)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q3_event_zoom.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(t_h, [Ta_fun(t) for t in mon["times"]], lw=1.0, ls="--", label="烘房 $T_a$")
    ax.plot(t_h, mon["T_surface"], lw=1.2, label="表面")
    ax.plot(t_h, mon["T_center"], lw=1.2, label="中心")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel("温度 (°C)")
    ax.set_xlim(0, t_rep_h)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "q3_T_center_surface.pdf")
    plt.close(fig)


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, (float, int, str, bool)) or obj is None:
        return obj
    return str(obj)


def main(argv=None):
    from q3_closeout import main as closeout_main
    return closeout_main(argv)


if __name__ == '__main__':
    main()
'''

# ========================================================================
# Module: q3_closeout.py
# ========================================================================
SOURCES['q3_closeout'] = r'''"""Q3 closeout: matched-time convergence, continuous balances and gated delivery."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from delivery import make_gate,require_delivery
from q3_balance import audit_segment,combine
from utils import RESULTS_DIR,REPORTS_DIR,FIGURES_DIR,ROOT

DIAG=RESULTS_DIR/'diagnostics/q3_closeout'
REQUIRED_CHECKS = frozenset({
    'event_found', 'finite', 'strict_below_all_verified_grids',
    'strict_below_with_empirical_margin', 'moisture_bounds', 'temperature_bounds',
    'moisture_balance_1e-6', 'heat_balance_1e-6', 'quadrature_convergence_1e-7',
    'space_event_60s', 'time_event_60s', 'space_full_fields_2e-5',
    'time_full_fields_2e-5', 'table_four_decimals', 'q2_overlap',
})


def require_q3_delivery(validation, diagnostic_path):
    require_delivery(validation, diagnostic_path)
    if validation.get('result_version') != 'q3-closeout-v1' or not REQUIRED_CHECKS.issubset(validation['delivery_gate']['checks']):
        raise RuntimeError('Delivery blocked: missing Q3 checks or wrong result version')


def export_workbook(path, C_out, times, validation):
    require_q3_delivery(validation, DIAG / 'pre_export.json')
    from reproduction_export import write_template
    write_template(ROOT, 3, times, [C_out])


def save_case(case):
    f=case['fvm'];n=f.n_nodes
    np.savez_compressed(DIAG/(case['tag']+'.npz'),r=f.r,times=case['times'],Y=case['Y'],
        y_star=case['y_star'],t_star=case['t_star'])
    info={k:case[k] for k in ('tag','level','n_nodes','rtol','atol_T','atol_C','max_step_early','max_step_late','elapsed_s','event')}
    (DIAG/(case['tag']+'.json')).write_text(json.dumps(info,indent=2),encoding='utf-8')


def compare_fields(a,b):
    """Shared physical nodes and exactly matching stored times."""
    times,ia,ib=np.intersect1d(a['times'],b['times'],return_indices=True)
    ra,rb=a['fvm'].r,b['fvm'].r
    j=np.searchsorted(rb,ra)
    if np.max(abs(rb[j]-ra))>1e-13:
        raise RuntimeError('spatial meshes are not nested')
    na,nb=a['n_nodes'],b['n_nodes']
    # Batch to bound temporary array sizes for fine meshes.
    maxT=maxC=0.
    for start in range(0,len(times),128):
        ai,bi=ia[start:start+128],ib[start:start+128]
        maxT=max(maxT,float(np.max(abs(a['Y'][ai,:na]-b['Y'][bi,:nb][:,j]))))
        maxC=max(maxC,float(np.max(abs(a['Y'][ai,na:]-b['Y'][bi,nb:][:,j]))))
    return {'matched_times':len(times),'max_T':maxT,'max_C':maxC}


def main(argv=None):
    from problem3 import (load_q3_inputs,run_case,run_probe,RTOL,ATOL_T,ATOL_C,MAX_STEP_EARLY,
        MAX_STEP_LATE,find_strict_report,build_output_tables,physical_bounds,overlap_q2,
        write_result3_xlsx,write_table5_csv,plot_figures,setup_mpl,conservation_heat,conservation_moisture)
    parser=argparse.ArgumentParser();parser.add_argument('--probe-only',action='store_true')
    parser.add_argument('--no-xlsx',action='store_true',help='Save gated numerical evidence; export separately later.')
    args=parser.parse_args(argv)
    DIAG.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    Ta,Ca,knots=load_q3_inputs()
    if args.probe_only:
        print(json.dumps(run_probe(Ta,Ca)));return
    cases={}
    for level in (4,8,16):
        cases[level]=run_case(level,Ta,Ca,72*3600.,RTOL,ATOL_T,ATOL_C,MAX_STEP_EARLY,MAX_STEP_LATE,
                             tag=f'G{level}',audit_balances=(level==8))
        save_case(cases[level])
    pub,ref=cases[8],cases[16]
    tight=run_case(8,Ta,Ca,72*3600.,RTOL/5,ATOL_T/5,ATOL_C/5,MAX_STEP_EARLY/2,MAX_STEP_LATE/2,tag='G8t')
    save_case(tight)
    space=compare_fields(pub,ref);temporal=compare_fields(pub,tight)
    coarse_space=compare_fields(cases[4],pub)
    critical=pub['t_star']
    same={name:float(case['eval_M'](critical)) for name,case in [('G4',cases[4]),('G8',pub),('G16',ref),('G8t',tight)]}
    # The maximum differences are measured at the same physical time.
    err=max(abs(same['G8']-same['G16']),abs(same['G8']-same['G8t']))
    margin=2*err+1e-8
    zero_report=find_strict_report(pub['eval_M'],critical,critical+3500,margin=0.)
    report=find_strict_report(pub['eval_M'],critical,critical+3500,margin=margin)
    t_rep=report['t_hour4_s']  # Upward four-decimal-hour rounding retains the safety margin.
    report_M={name:float(case['eval_M'](t_rep)) for name,case in [('G8',pub),('G16',ref),('G8t',tight)]}
    tables=build_output_tables(pub,t_rep);other=build_output_tables(ref,t_rep)
    tight_tables=build_output_tables(tight,t_rep)
    table_changed=int(np.count_nonzero(np.round(tables['C_table'],4)!=np.round(other['C_table'],4)))
    table_time_changed=int(np.count_nonzero(np.round(tables['C_table'],4)!=np.round(tight_tables['C_table'],4)))
    output_space=float(np.max(abs(tables['C_excel']-other['C_excel'])))
    tail=audit_segment(pub['fvm'],pub['sol_after'],Ta,Ca,t_end=t_rep)
    balances=combine(pub['balance_parts']+[tail])
    checked_states = np.vstack([pub['Y'], pub['y_star'], pub['eval_y'](t_rep)])
    bounds=physical_bounds(dict(pub,Y=checked_states),Ta,Ca);overlap=overlap_q2(pub)
    overlap_ok=overlap.get('available',False) and all(c.get('matched',False) and c['T_max_abs']<2e-5 and c['C_max_abs']<2e-5 for c in overlap['checks'].values())
    event_space=abs(pub['t_star']-ref['t_star']);event_time=abs(pub['t_star']-tight['t_star'])
    gates={
        'event_found':abs(pub['event']['g_star'])<1e-8,
        'finite':bool(np.isfinite(checked_states).all() and np.isfinite(tables['C_excel']).all()
                      and np.isfinite(tables['T_excel']).all()),
        'strict_below_all_verified_grids':all(v<.15 for v in report_M.values()),
        'strict_below_with_empirical_margin':report_M['G8']+margin<.15,
        'moisture_bounds':bounds['C_bounds_ok'],'temperature_bounds':bounds['T_bounds_ok'],
        'moisture_balance_1e-6':balances['moisture']['relative_residual']<1e-6,
        'heat_balance_1e-6':balances['heat']['relative_residual']<1e-6,
        'quadrature_convergence_1e-7':max(balances['quadrature_relative_difference'].values())<1e-7,
        'space_event_60s':event_space<=60.,'time_event_60s':event_time<=60.,
        'space_full_fields_2e-5':max(space['max_T'],space['max_C'],output_space)<2e-5,
        'time_full_fields_2e-5':max(temporal['max_T'],temporal['max_C'])<2e-5,
        'table_four_decimals':table_changed==0 and table_time_changed==0,
        'q2_overlap':overlap_ok,
    }
    v={'result_version':'q3-closeout-v1','model':'q3-model-v1','result_status':'PUBLISHED',
       'published_mesh':'G8','published_n_nodes':pub['n_nodes'],'rtol':RTOL,'atol_T':ATOL_T,'atol_C':ATOL_C,
       'max_step_early':MAX_STEP_EARLY,'max_step_late':MAX_STEP_LATE,
       't_star_s':critical,'t_star_h':critical/3600.,'t_rep_s':t_rep,'t_rep_h':t_rep/3600.,
       'M_star':pub['event']['M_star'],'M_rep':report_M['G8'],'report_maxima':report_M,
       'matched_critical_time_maxima':same,'moisture_margin':margin,'margin_type':'empirical, not a rigorous PDE error bound',
       'report_zero_margin':zero_report,'report_with_margin':report,
       'space_fields':space,'time_fields':temporal,'coarse_space_fields':coarse_space,'output_space_max_C':output_space,
       'dt_space_s':event_space,'dt_time_s':event_time,
       'conservation_C':balances['moisture'],'conservation_T':balances['heat'],'continuous_balances':balances,
       'old_sampled_conservation_C':conservation_moisture(pub['fvm'],pub['times'],pub['Y'],Ca),
       'old_sampled_conservation_T':conservation_heat(pub['fvm'],pub['times'],pub['Y'],Ta),
       'physical_bounds':bounds,'q2_overlap':overlap,'table_four_decimal_changes':table_changed,
       'events':{f'G{k}':c['event'] for k,c in cases.items()}|{'G8t':tight['event']},
       'delivery_gate':make_gate(gates),'table_hours':tables['table_hours'].tolist(),
       'excel_nrows':len(tables['excel_times']),'paper_table_C':tables['paper_C'],
       'max_location_cm':pub['event']['rmax_star_cm'],'center_is_max_at_event':pub['event']['center_is_max'],
       'n_radial_increases':pub['monitor']['n_radial_increases'],
       'elapsed_s':time.perf_counter()-start,'python':sys.version,
       'source_sha256':{p:hashlib.sha256(((Path(__file__).parent / Path(p).name) if p.startswith('code/') else ROOT / p).read_bytes()).hexdigest() for p in
           ['code/problem3.py','code/q3_balance.py','code/q3_closeout.py','code/delivery.py',
            'code/reproduction_export.py',
            'code/radial_coupled.py','code/appendix3.py','data/附件/附件1.xlsx']}}
    print('CLOSEOUT',json.dumps({k:v[k] for k in ('t_star_h','t_rep_h','M_rep','dt_space_s','dt_time_s','conservation_C','conservation_T','delivery_gate')},ensure_ascii=False),flush=True)
    publish_results(pub, tables, v, Ta, no_xlsx=args.no_xlsx)
    print('Q3 CLOSEOUT NUMERICAL PASS',flush=True)


def publish_results(pub, tables, v, Ta, *, no_xlsx=False):
    from problem3 import write_result3_xlsx, write_table5_csv, plot_figures, setup_mpl
    require_q3_delivery(v,DIAG/'latest.json')
    t_rep, critical = v['t_rep_s'], v['t_star_s']
    # Commit production outputs only after every required numerical check passed.
    yend=pub['eval_y'](t_rep)
    np.savez_compressed(RESULTS_DIR/'q3_solution.npz',mesh_level=8,n_nodes=pub['n_nodes'],r=pub['fvm'].r,
        times=pub['times'],Y=pub['Y'],excel_times=tables['excel_times'],T_out=tables['T_excel'],C_out=tables['C_excel'],
        table_hours=tables['table_hours'],C_table=tables['C_table'],t_star=critical,t_rep=t_rep,
        y_star=pub['y_star'],y_end=yend,M_hist=pub['monitor']['M'],rmax_m=pub['monitor']['rmax_m'],
        C_center=pub['monitor']['C_center'],C_surface=pub['monitor']['C_surface'],
        T_center=pub['monitor']['T_center'],T_surface=pub['monitor']['T_surface'],
        rtol=v['rtol'],atol_T=v['atol_T'],atol_C=v['atol_C'],max_step_early=v['max_step_early'],max_step_late=v['max_step_late'],
        interpolation=np.array('pchip_then_constant'))
    (RESULTS_DIR/'q3_validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    write_table5_csv(RESULTS_DIR/'q3_table_moisture.csv',tables['table_hours'],tables['C_table'])
    if not no_xlsx:
        write_result3_xlsx(RESULTS_DIR/'result3.xlsx',tables['C_excel'],tables['excel_times'],validation=v)
    plot_figures(setup_mpl(),pub,tables,t_rep,Ta)


if __name__=='__main__':
    main()
'''

def prepare():
    code_dir = PACKAGE_ROOT / '_runtime' / f'Q{QUESTION}' / 'code'
    code_dir.mkdir(parents=True, exist_ok=True)
    for name, source in SOURCES.items():
        (code_dir / (name + '.py')).write_text(source, encoding='utf-8')
    sys.path.insert(0, str(code_dir))
    for folder in ('results', 'figures', 'reports'):
        (PACKAGE_ROOT / folder).mkdir(exist_ok=True)
    os.environ.setdefault('MPLBACKEND', 'Agg')
    for name in SOURCES:
        importlib.import_module(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check imports and original inputs without solving')
    parser.add_argument('--export-only', action='store_true', help='Export existing validated NPZ arrays; does not solve the model')
    args = parser.parse_args()
    prepare()
    from utils import load_oven_table
    load_oven_table()
    if QUESTION == 4:
        from problem4 import Inputs
        Inputs()
    if args.check:
        print(f'Q{QUESTION}: imports and input checks passed', flush=True)
        return
    from reproduction_export import export_saved
    if args.export_only:
        export_saved(PACKAGE_ROOT, QUESTION)
        return
    if QUESTION == 1:
        import problem1
        problem1.main()
    elif QUESTION == 2:
        import problem2
        problem2.main()
    elif QUESTION == 3:
        # The original delivery gate compares Q3 with independently computed Q2.
        if not (PACKAGE_ROOT / 'results' / 'q2_solution.npz').exists():
            print('Q3: computing Q2 first for the original overlap check', flush=True)
            import problem2
            problem2.main()
            export_saved(PACKAGE_ROOT, 2)
        import q3_closeout
        q3_closeout.main(['--no-xlsx'])
    else:
        import problem4
        import verify_q4_results
        for level, tight in ((2, False), (4, False), (4, True), (8, False), (16, False), (8, True)):
            problem4.run(level, tight)
        verify_q4_results.main()
    export_saved(PACKAGE_ROOT, QUESTION)
    print(f'Q{QUESTION}: full recomputation and Excel export completed', flush=True)


if __name__ == '__main__':
    main()
