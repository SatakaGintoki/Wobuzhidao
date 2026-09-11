"""Shared paths and attachment readers for Problem A."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[1]
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
