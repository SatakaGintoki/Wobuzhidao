"""Problem 3: full coupled drying until every interior node is below 0.15 kg/kg."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from appendix3 import moisture_diffusivity_q2
from delivery import make_gate
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
        dense_output=dense_output,
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
    t_rep = float(max(t_cross, np.ceil(t_star + 1e-9)))
    # Walk forward in seconds until unrounded moisture is strictly below the target.
    for _ in range(10000):
        if float(eval_M(t_rep)) < target:
            break
        t_rep += 1.0
    else:
        raise RuntimeError("failed to find integer-second report time below threshold")
    t_hour4 = np.ceil((t_star / 3600.0) * 10000.0) / 10000.0
    t_hour4_s = 3600.0 * t_hour4
    if t_hour4_s < t_rep:
        t_hour4_s = t_rep
        t_hour4 = t_hour4_s / 3600.0
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
        max_step=max_step_early, t_eval=t_eval_early, first_step=0.05, label=f"{tag} early ",
    )
    y_switch = sol1.y[:, -1]
    times1 = np.concatenate([[0.0], sol1.t])
    Y1 = np.vstack([y0, sol1.y.T])
    M_switch = float(np.max(y_switch[n:]))
    print(f"  {tag} 4h maxC={M_switch:.6f}  C_center={y_switch[n]:.6f}  wall={time.perf_counter()-t_wall0:.1f}s", flush=True)
    if M_switch <= C_THRESH:
        raise RuntimeError("threshold already reached at 4 h; unexpected for this model")

    event = max_moisture_event(n)
    t_eval_late = np.arange(T_SWITCH + EXCEL_DT, t_max + 0.5 * EXCEL_DT, EXCEL_DT)
    sol2 = integrate_segment(
        fvm, y_switch, T_SWITCH, t_max, Ta_fun, Ca_fun, rtol, atol,
        max_step=max_step_late, t_eval=t_eval_late, events=event,
        first_step=0.2, label=f"{tag} late ",
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
            first_step=0.2, label=f"{tag} cap ",
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

    t_pad = 3600.0
    sol_after = integrate_segment(
        fvm, y_star, t_star, t_star + t_pad, Ta_fun, Ca_fun, rtol, atol,
        max_step=min(max_step_late, 5.0), dense_output=True, first_step=0.05,
        label=f"{tag} after ",
    )

    def eval_M(t):
        tt = float(t)
        if tt <= t_star + 1e-12:
            return float(np.max(y_star[n:]))
        if tt > float(sol_after.t[-1]) + 1e-12:
            raise ValueError(f"eval_M beyond continuation {tt}")
        return float(np.max(sol_after.sol(tt)[n:]))

    def eval_y(t):
        tt = float(t)
        if abs(tt - t_star) <= 1e-12:
            return y_star.copy()
        if tt < t_star:
            k = int(np.searchsorted(times, tt))
            k = min(max(k, 0), times.size - 1)
            if k > 0 and abs(times[k] - tt) > abs(times[k - 1] - tt):
                k -= 1
            if abs(times[k] - tt) > 1.0:
                raise ValueError(f"no stored state near t={tt}")
            return Y[k].copy()
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
        if abs(case["times"][k] - t) > 1.0:
            rows[f"t{int(t)}"] = {"matched": False}
            continue
        jq = int(np.argmin(np.abs(q2_times - t)))
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
    y = case["eval_y"](float(t)) if float(t) >= case["t_star"] - 1e-9 else None
    if y is None:
        k = int(np.argmin(np.abs(case["times"] - t)))
        if abs(case["times"][k] - t) > 0.51 * EXCEL_DT:
            # Linear blend of nearest stored states for 6 h table times on the 60 s grid.
            k = int(np.searchsorted(case["times"], t))
            k = min(max(k, 1), case["times"].size - 1)
        y = case["Y"][k]
        if abs(case["times"][k] - t) > 1e-8 and 0 < k < case["times"].size:
            # If t is on the 60 s production grid it should hit exactly.
            j = int(np.argmin(np.abs(case["times"] - t)))
            y = case["Y"][j]
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


def write_result3_xlsx(path: Path, C_out: np.ndarray, times: np.ndarray):
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("水分浓度")
    header = ["时间\\到药材中心的距离"] + [float(0.1 * j) for j in range(21)]
    ws.append(header)
    for i, t in enumerate(times):
        tv = float(t)
        t_cell = WriteOnlyCell(ws, value=int(round(tv)) if abs(tv - round(tv)) < 1e-8 else tv)
        if abs(tv - round(tv)) < 1e-8:
            t_cell.number_format = "0"
        else:
            t_cell.number_format = "0.000"
        row = [t_cell]
        for j in range(21):
            cell = WriteOnlyCell(ws, value=float(C_out[i, j]))
            cell.number_format = "0.0000"
            row.append(cell)
        ws.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args(argv)
    t_wall0 = time.perf_counter()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    diag_dir = RESULTS_DIR / "diagnostics/q3_delivery"
    diag_dir.mkdir(parents=True, exist_ok=True)

    Ta_fun, Ca_fun, knots = load_q3_inputs()
    print(
        "knots", knots.size, "Ta(4h)=", Ta_fun(T_SWITCH), "Ta(4h+)=", Ta_fun(T_SWITCH + 1e-6),
        "Ca(4h)=", Ca_fun(T_SWITCH), "Ca(4h+)=", Ca_fun(T_SWITCH + 1e-6),
        flush=True,
    )
    probe = run_probe(Ta_fun, Ca_fun)
    t_max = min(T_HARD_CAP, probe["t_star_s"] * 1.8 + 12.0 * 3600.0)
    print(f"production t_max={t_max/3600:.2f} h", flush=True)
    if args.probe_only:
        payload = {"probe": probe, "t_max_s": t_max, "elapsed_s": time.perf_counter() - t_wall0}
        (RESULTS_DIR / "q3_probe.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=float), encoding="utf-8"
        )
        print("probe-only done", payload["elapsed_s"], flush=True)
        return

    cases = {}
    for level in (2, 4):
        cases[level] = run_case(
            level, Ta_fun, Ca_fun, t_max, RTOL, ATOL_T, ATOL_C,
            MAX_STEP_EARLY, MAX_STEP_LATE, tag=f"G{level}",
        )

    pub = cases[4]
    print("\n=== time refinement on G4 ===", flush=True)
    tight = run_case(
        4, Ta_fun, Ca_fun, t_max, RTOL / 5.0, ATOL_T / 5.0, ATOL_C / 5.0,
        max(0.5, MAX_STEP_EARLY / 2.0), max(2.0, MAX_STEP_LATE / 2.0), tag="G4t",
    )

    dt_space = cases[4]["t_star"] - cases[2]["t_star"]
    dt_time = tight["t_star"] - cases[4]["t_star"]
    dMdt = abs(pub["event"]["dMdt_per_s"])
    # Moisture discrepancy of G2 vs G4 at the published critical time, via G2 stored field.
    t4 = pub["t_star"]
    j2 = int(np.argmin(np.abs(cases[2]["times"] - t4)))
    M2_at_t4 = float(np.max(cases[2]["Y"][j2, cases[2]["n_nodes"]:]))
    M4 = pub["event"]["M_star"]
    margin = max(abs(M2_at_t4 - M4), 5e-6)
    if dMdt > 0:
        eta_t_s = margin / dMdt
    else:
        eta_t_s = float("nan")
    report = find_strict_report(pub["eval_M"], pub["t_star"], pub["t_star"] + 3500.0, margin=0.0)
    try:
        report_m = find_strict_report(pub["eval_M"], pub["t_star"], pub["t_star"] + 3500.0, margin=margin)
    except Exception as exc:
        report_m = {"error": str(exc), "margin": margin}
    # Report the first integer second with unrounded max C strictly below 0.15.
    # Spatial/time discrepancies are reliability evidence, not a shift of t_rep.
    t_rep = float(report["t_rep_s"])
    M_rep = float(pub["eval_M"](t_rep))
    print(
        f"t*_G2={cases[2]['t_star']/3600:.6f} h  t*_G4={pub['t_star']/3600:.6f} h  "
        f"t*_G4t={tight['t_star']/3600:.6f} h  dt_space={dt_space:.4f}s  dt_time={dt_time:.4f}s",
        flush=True,
    )
    print(f"t_rep={t_rep/3600:.6f} h  M_rep={M_rep:.10f}  margin={margin:.3e}  eta_t={eta_t_s:.3f}s", flush=True)

    tables = build_output_tables(pub, t_rep)
    bounds = physical_bounds(pub, Ta_fun, Ca_fun)
    cons_C = conservation_moisture(pub["fvm"], pub["times"], pub["Y"], Ca_fun)
    cons_T = conservation_heat(pub["fvm"], pub["times"], pub["Y"], Ta_fun)
    overlap = overlap_q2(pub)
    print("bounds", bounds, flush=True)
    print("conservation C", cons_C, flush=True)
    print("conservation T", cons_T, flush=True)
    print("overlap Q2", overlap, flush=True)

    C_excel = tables["C_excel"]
    max_after = float(np.max(C_excel[-1]))
    def M_at_hour(case, hour):
        t = 3600.0 * float(hour)
        j = int(np.argmin(np.abs(case["times"] - t)))
        return {
            "t_nearest_s": float(case["times"][j]),
            "M": float(np.max(case["Y"][j, case["n_nodes"]:])),
            "C_center": float(case["Y"][j, case["n_nodes"]]),
            "C_surface": float(case["Y"][j, -1]),
        }

    hours_snap = (6, 12, 24, 48, 72, 96, 120, 168, 216)
    snapshots = {f"{h}h": M_at_hour(pub, h) for h in hours_snap if 3600.0 * h < pub["t_star"] - 1.0}
    space_ok = abs(dt_space) <= 3600.0
    time_ok = abs(dt_time) <= 3600.0
    overlap_ok = True
    if overlap.get("available"):
        c25 = overlap["checks"].get("t9000", {})
        overlap_ok = bool(c25.get("matched")) and c25.get("C_max_abs", 1.0) <= 5e-4
    delivery = make_gate({
        "event_found": True,
        "finite": bool(np.isfinite(pub["Y"]).all() and np.isfinite(C_excel).all()),
        "strict_below": bool(M_rep < C_THRESH and max_after < C_THRESH),
        "center_nonnegative": bounds["C_bounds_ok"],
        "temperature_bounds": bounds["T_bounds_ok"],
        "moisture_balance": cons_C["relative_residual"] <= 1e-4,
        "heat_balance": cons_T["relative_residual"] <= 1e-4,
        "space_event_60s": space_ok,
        "time_event_60s": time_ok,
        "q2_overlap_2.5h": overlap_ok,
        "max_location_recorded": pub["event"]["rmax_star_cm"] >= 0.0,
    })
    print("delivery", delivery, flush=True)

    y_end = pub["eval_y"](t_rep)
    n = pub["n_nodes"]
    validation = {
        "result_version": "q3-baseline-v1",
        "model": "q3-model-v1",
        "interpolation": "pchip_then_constant_50C_0.05",
        "published_mesh": pub["tag"],
        "published_n_nodes": pub["n_nodes"],
        "solver": "coupled-FVM+BDF+bracketed-event",
        "rtol": RTOL, "atol_T": ATOL_T, "atol_C": ATOL_C,
        "max_step_early": MAX_STEP_EARLY, "max_step_late": MAX_STEP_LATE,
        "probe": probe,
        "t_star_s": pub["t_star"],
        "t_star_h": pub["t_star"] / 3600.0,
        "t_rep_s": t_rep,
        "t_rep_h": t_rep / 3600.0,
        "M_star": pub["event"]["M_star"],
        "M_rep": M_rep,
        "threshold": C_THRESH,
        "event_G2": cases[2]["event"],
        "event_G4": pub["event"],
        "event_G4_tight": tight["event"],
        "dt_space_s": dt_space,
        "dt_time_s": dt_time,
        "dt_space_h": dt_space / 3600.0,
        "dt_time_h": dt_time / 3600.0,
        "moisture_margin": margin,
        "eta_t_s": eta_t_s,
        "report_zero_margin": report,
        "report_with_margin": report_m,
        "max_location_cm": pub["event"]["rmax_star_cm"],
        "center_is_max_at_event": pub["event"]["center_is_max"],
        "monitor_center_is_max_frac": pub["monitor"]["center_is_max_frac"],
        "n_radial_increases": pub["monitor"]["n_radial_increases"],
        "conservation_C": cons_C,
        "conservation_T": cons_T,
        "physical_bounds": bounds,
        "q2_overlap": overlap,
        "delivery_gate": delivery,
        "paper_table_C": tables["paper_C"],
        "table_hours": tables["table_hours"].tolist(),
        "excel_nrows": int(tables["excel_times"].size),
        "M_snapshots": snapshots,
        "C_end_output": C_excel[-1].tolist(),
        "C_end_internal_max": float(np.max(y_end[n:])),
        "elapsed_s": time.perf_counter() - t_wall0,
        "python": sys.version,
        "env_after_4h": {"Ta": TA_AFTER, "Ca": CA_AFTER},
        "cases_elapsed_s": {k: cases[k]["elapsed_s"] for k in cases} | {"G4t": tight["elapsed_s"]},
    }
    (diag_dir / "latest.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, default=float), encoding="utf-8"
    )
    hard = (
        delivery["checks"]["event_found"]
        and delivery["checks"]["finite"]
        and delivery["checks"]["strict_below"]
        and delivery["checks"]["center_nonnegative"]
    )
    if not hard:
        raise RuntimeError("hard Q3 checks failed: " + str(delivery["failed_checks"]))

    np.savez(
        RESULTS_DIR / "q3_solution.npz",
        mesh_level=4,
        n_nodes=pub["n_nodes"],
        r=pub["fvm"].r,
        times=pub["times"],
        excel_times=tables["excel_times"],
        T_out=tables["T_excel"],
        C_out=tables["C_excel"],
        table_hours=tables["table_hours"],
        C_table=tables["C_table"],
        t_star=pub["t_star"],
        t_rep=t_rep,
        y_star=pub["y_star"],
        y_end=y_end,
        M_hist=pub["monitor"]["M"],
        rmax_m=pub["monitor"]["rmax_m"],
        C_center=pub["monitor"]["C_center"],
        C_surface=pub["monitor"]["C_surface"],
        T_center=pub["monitor"]["T_center"],
        T_surface=pub["monitor"]["T_surface"],
        interpolation=np.array("pchip_then_constant"),
        rtol=RTOL, atol_T=ATOL_T, atol_C=ATOL_C,
        max_step_early=MAX_STEP_EARLY, max_step_late=MAX_STEP_LATE,
    )
    write_result3_xlsx(RESULTS_DIR / "result3.xlsx", C_excel, tables["excel_times"])
    write_table5_csv(RESULTS_DIR / "q3_table_moisture.csv", tables["table_hours"], tables["C_table"])
    plt = setup_mpl()
    plot_figures(plt, pub, tables, t_rep, Ta_fun)
    (RESULTS_DIR / "q3_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, default=float), encoding="utf-8"
    )
    print("elapsed_s", validation["elapsed_s"], flush=True)
    print("wrote results to", RESULTS_DIR, flush=True)
    print(
        f"ANSWER t*={pub['t_star']/3600:.6f} h  t_rep={t_rep/3600:.6f} h  "
        f"rmax={pub['event']['rmax_star_cm']:.4f} cm  gate={delivery['meets_delivery_gate']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
