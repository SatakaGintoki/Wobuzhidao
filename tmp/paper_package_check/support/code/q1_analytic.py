"""Independent Bessel–Duhamel reference for the linear radial heat (or frozen-D moisture) problem."""
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
