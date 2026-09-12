"""Q4: prescribed radial shrinkage, material-coordinate FVM and BDF.

Run a bounded, source-preserving baseline with --level 2/4/8 [--tight].
No radius extrapolation; output here is internal numerical evidence, not Excel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy
from numpy.polynomial.legendre import leggauss
from openpyxl import load_workbook
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator
from scipy.sparse import lil_matrix

from radial_fvm import graded_radial_nodes, harmonic_mean
from utils import ATTACH_DIR, RESULTS_DIR, C0, T0, H, HM, R, load_oven_table

CAP = 259200.0
SWITCH = 14400.0
THRESHOLD = 0.15
OUT = RESULTS_DIR / "q4_baseline"


def properties(C, T):
    C, T = np.asarray(C), np.asarray(T)
    # Only protect nonphysical implicit-iteration probes; stored states are audited.
    Cp = np.maximum(C, 1e-12)
    rho = 760.0 + 90.0 * Cp
    cp = 1850.0 + 2150.0 * Cp / (1.0 + Cp)
    k = 0.12 + 0.20 * Cp / (1.0 + Cp)
    D = 4.2e-4 * np.exp(-0.30 / Cp) * np.exp(-3850.0 / (T + 273.15))
    return rho * cp, k, D


class Inputs:
    def __init__(self):
        t, Ta, Ca = load_oven_table()
        if t.size != 241 or t[0] != 0 or t[-1] != SWITCH:
            raise ValueError("unexpected oven input coverage")
        self.Ta = PchipInterpolator(t, Ta, extrapolate=False)
        self.Ca = PchipInterpolator(t, Ca, extrapolate=False)
        wb = load_workbook(ATTACH_DIR / "附件2.xlsx", read_only=True, data_only=True)
        radius_rows = list(wb.active.values)
        wb.close()
        a = np.asarray(radius_rows[1:], dtype=float)
        self.rt, self.rv = a[:, 0], a[:, 1] / 100.0
        if (a.shape != (145, 2) or not np.all(np.isfinite(a))
                or np.any(np.diff(self.rt) <= 0) or np.any(np.diff(self.rv) > 0)
                or self.rt[0] != 0 or self.rt[-1] != CAP or self.rv[0] != R):
            raise ValueError("unexpected radius input")
        self.radius = PchipInterpolator(self.rt, self.rv, extrapolate=False)
        self.audit = {"radius_records": len(a), "radius_range_m": [float(self.rv[0]), float(self.rv[-1])],
                      "radius_cap_s": CAP, "oven_records": len(t), "radius_input_headers": list(radius_rows[0]),
                      "radius_node_error_m": float(np.max(abs(self.radius(self.rt) - self.rv))),
                      "oven_node_error": float(max(np.max(abs(self.Ta(t)-Ta)), np.max(abs(self.Ca(t)-Ca))))}
        self.audit["source_sha256"] = {
            name: hashlib.sha256((ATTACH_DIR / name).read_bytes()).hexdigest()
            for name in ("附件1.xlsx", "附件2.xlsx")}

    def environment(self, t, late=False):
        if late or t > SWITCH:
            return 50.0, 0.05
        return float(self.Ta(t)), float(self.Ca(t))


class ShrinkingFVM:
    def __init__(self, xi):
        self.xi = np.asarray(xi, dtype=float)
        if self.xi[0] != 0 or self.xi[-1] != 1 or np.any(np.diff(self.xi) <= 0):
            raise ValueError("invalid material mesh")
        self.n = len(xi)
        self.faces = (self.xi[:-1] + self.xi[1:]) / 2
        edges = np.r_[0., self.faces, 1.]
        self.w = np.diff(edges**2) / 2
        self.dx = np.diff(self.xi)

    def sparsity(self):
        J = lil_matrix((2*self.n, 2*self.n))
        for i in range(self.n):
            for j in range(max(0, i-1), min(self.n, i+2)):
                J[i, j] = J[i, self.n+j] = J[self.n+i, j] = J[self.n+i, self.n+j] = 1
        return J.tocsc()

    def rhs(self, y, radius, Ta, Ca, hm=HM, ht=H):
        T, C = y[:self.n], y[self.n:]
        B, k, D = properties(C, T)
        FT = np.r_[0., -self.faces*harmonic_mean(k[:-1], k[1:])*np.diff(T)/self.dx,
                   radius*ht*(T[-1]-Ta)]
        FC = np.r_[0., -self.faces*harmonic_mean(D[:-1], D[1:])*np.diff(C)/self.dx,
                   radius*hm*(C[-1]-Ca)]
        Tdot = -np.diff(FT) / (radius**2 * self.w * B)
        Cdot = -np.diff(FC) / (radius**2 * self.w)
        return np.r_[Tdot, Cdot]


def model_checks(inputs):
    fvm = ShrinkingFVM(np.linspace(0., 1., 41))
    x = fvm.xi
    y = np.r_[35.+10*x*x, 1.7-1.2*x*x]
    rr = float(inputs.radius(21600.))
    dy = fvm.rhs(y, rr, 50., 0.05)
    mass_error = abs(2*np.dot(fvm.w, dy[fvm.n:]) + 2*HM/rr*(y[-1]-0.05))
    B, k, D = properties(y[fvm.n:], y[:fvm.n])
    heat_error = abs(np.dot(fvm.w*B, dy[:fvm.n]) + H/rr*(y[fvm.n-1]-50.))
    # Independent dimensional-volume assembly on the same physical annuli.
    rp = rr*x
    rf = (rp[:-1]+rp[1:])/2
    volumes = np.diff(np.r_[0., rf, rr]**2)/2
    flows_T = np.r_[0., -rf*harmonic_mean(k[:-1], k[1:])*np.diff(y[:fvm.n])/np.diff(rp), rr*H*(y[fvm.n-1]-50.)]
    flows_C = np.r_[0., -rf*harmonic_mean(D[:-1], D[1:])*np.diff(y[fvm.n:])/np.diff(rp), rr*HM*(y[-1]-0.05)]
    reference = np.r_[-np.diff(flows_T)/(volumes*B), -np.diff(flows_C)/volumes]
    fixed_error = float(np.max(abs(dy-reference)))
    uniform = np.r_[np.full(fvm.n, T0), np.full(fvm.n, C0)]
    pure = solve_ivp(lambda t,z: fvm.rhs(z, float(inputs.radius(t)), T0, C0, hm=0., ht=0.),
                     (0., CAP), uniform, method="BDF", jac_sparsity=fvm.sparsity(),
                     rtol=1e-9, atol=1e-11)
    pure_error = float(np.max(abs(pure.y-uniform[:,None])))
    checks = {"instant_mass_abs": float(mass_error), "instant_heat_abs": float(heat_error),
              "fixed_physical_operator_abs": fixed_error, "pure_shrinkage_uniform_abs": pure_error,
              "pure_shrinkage_success": bool(pure.success)}
    checks["pass"] = bool(mass_error < 1e-12 and heat_error < 1e-6 and fixed_error < 1e-10
                          and pure_error < 1e-10 and pure.success)
    return checks


def run(level=2, tight=False):
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = Inputs()
    basic = model_checks(inputs)
    if not basic["pass"]:
        raise RuntimeError(f"model checks failed: {basic}")
    fvm = ShrinkingFVM(graded_radial_nodes(level)/R)
    n = fvm.n
    rtol = 1e-9 if tight else 1e-8
    atol = np.r_[np.full(n, 1e-9 if tight else 1e-8), np.full(n, 1e-11 if tight else 1e-10)]
    label = f"G{level}" + ("_tight" if tight else "")
    y0 = np.r_[np.full(n, T0), np.full(n, C0)]
    times, states = [np.array([0.])], [y0[None,:]]
    segments, events, event_states = [], [], []
    mass_loss = 0.
    max_mass_error = 0.
    bounds = [float("inf"), -float("inf"), float("inf"), -float("inf")]
    radial_increase = 0.
    heat_residual_max = 0.
    wall = time.perf_counter()
    event = lambda t,y: float(np.max(y[n:])-THRESHOLD)
    event.direction = -1.
    event.terminal = False
    breaks = np.unique(np.r_[0., SWITCH, np.arange(21600., CAP+1., 21600.)])
    gx, gw = leggauss(4)
    for a,b in zip(breaks[:-1], breaks[1:]):
        late = a >= SWITCH
        def rhs(t,y):
            Ta,Ca = inputs.environment(t, late=late)
            return fvm.rhs(y, float(inputs.radius(t)), Ta, Ca)
        max_step = (5. if tight else 10.) if not late else (30. if tight else 60.)
        sol = solve_ivp(rhs, (a,b), y0, method="BDF", rtol=rtol, atol=atol,
                        jac_sparsity=fvm.sparsity(), max_step=max_step,
                        dense_output=True, events=event)
        if not sol.success:
            raise RuntimeError(sol.message)
        ts = np.arange(a+60., b+0.1, 60.)
        ys = sol.sol(ts).T
        times.append(ts)
        states.append(ys)
        if len(sol.t_events[0]):
            events.extend(sol.t_events[0].tolist())
            event_states.extend(sol.y_events[0].tolist())
        # Quadrature on accepted BDF step intervals; 4-point Gaussian rule.
        integral = 0.
        for start in range(0, len(sol.t)-1, 128):
            aa, bb = sol.t[start:-1][:128], sol.t[start+1:][:128]
            qq = ((aa+bb)[:,None]/2 + (bb-aa)[:,None]/2*gx).ravel()
            surface = sol.sol(qq)[-1]
            ca = np.full_like(qq, 0.05) if late else inputs.Ca(qq)
            loss = 2*HM/inputs.radius(qq)*(surface-ca)
            integral += float(np.sum(loss.reshape(-1,4)*gw*(bb-aa)[:,None]/2))
        mass_loss += integral
        y0 = sol.y[:,-1]
        mass_error = abs(float(2*np.dot(fvm.w,y0[n:])-C0+mass_loss))
        max_mass_error = max(max_mass_error, mass_error)
        TT, CC = sol.y[:n], sol.y[n:]
        bounds = [min(bounds[0],float(TT.min())), max(bounds[1],float(TT.max())),
                  min(bounds[2],float(CC.min())), max(bounds[3],float(CC.max()))]
        radial_increase = max(radial_increase,float(np.max(np.diff(CC,axis=0))))
        # Audit sampled heat-equation weighted residual, not d(rho*cp*T)/dt.
        for tcheck in (a,(a+b)/2,b):
            z = sol.sol(tcheck)
            dz = rhs(tcheck,z)
            B,_,_ = properties(z[n:],z[:n])
            Ta,_ = inputs.environment(tcheck,late=late)
            heat_error = abs(float(np.dot(fvm.w*B,dz[:n])+H/float(inputs.radius(tcheck))*(z[n-1]-Ta)))
            heat_residual_max = max(heat_residual_max,heat_error)
        segments.append({"start_s":float(a),"end_s":float(b),"steps":len(sol.t)-1,
                         "nfev":sol.nfev,"nlu":sol.nlu,"mass_abs_error":mass_error})
        print(f"{label}: {b/3600:g}h maxC={y0[n:].max():.8f} mass_err={mass_error:.2e} wall={time.perf_counter()-wall:.1f}s",flush=True)
    tt, yy = np.concatenate(times), np.vstack(states)
    meta = {"label":label,"level":level,"tight":tight,"nodes":n,"rtol":rtol,
            "atol_T":float(atol[0]),"atol_C":float(atol[n]),"early_max_step_s":5. if tight else 10.,
            "late_max_step_s":30. if tight else 60.,"event_s":events[0] if events else None,
            "event_h":events[0]/3600 if events else None,"end_maxC":float(yy[-1,n:].max()),
            "max_mass_abs_error":max_mass_error,"mass_relative_error":max_mass_error/C0,
            "heat_equation_residual_max":heat_residual_max,"bounds_Tmin_Tmax_Cmin_Cmax":bounds,
            "max_outward_C_increase":radial_increase,"segments":segments,"input_audit":inputs.audit,
            "model_checks":basic,"wall_s":time.perf_counter()-wall,
            "python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,
            "model":"q4-model-v1","radius_extrapolation":False,
            "source_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    np.savez_compressed(OUT/f"{label}.npz",times_s=tt,Y=yy,xi=fvm.xi,w=fvm.w,
                        radius_m=inputs.radius(tt),events_s=np.array(events),event_states=np.array(event_states))
    (OUT/f"{label}.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:meta[k] for k in ("label","event_h","end_maxC","mass_relative_error","wall_s")}),flush=True)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--level",type=int,default=2)
    parser.add_argument("--tight",action="store_true")
    args = parser.parse_args()
    run(args.level,args.tight)
