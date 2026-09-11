"""Appendix 3 effective properties for Problems 2 and 3."""
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
