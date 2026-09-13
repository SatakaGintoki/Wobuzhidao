"""Bounded Q3 end-face audit; node-centered annular FVM and streaming BDF."""
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
from scipy.integrate import BDF, solve_ivp
from scipy.optimize import brentq
from scipy.sparse import coo_matrix
from threadpoolctl import threadpool_limits

from appendix3 import conductivity, heat_capacity, moisture_diffusivity_q2
from problem3 import load_q3_inputs, T_SWITCH, TA_AFTER, CA_AFTER
from radial_coupled import CoupledRadialFVM
from radial_fvm import harmonic_mean
from utils import ATTACH_DIR, C0, T0, R, L, H, HM, RESULTS_DIR

OUT = RESULTS_DIR / "q3_axisymmetric"
THRESHOLD = 0.15
CAP = 72.0 * 3600.0
Z = L / 2.0


def nodes(intervals: int, extent: float, power: float) -> np.ndarray:
    if intervals < 4:
        raise ValueError("At least four intervals are required")
    u = np.linspace(0.0, 1.0, intervals + 1)
    x = extent * (1.0 - (1.0 - u) ** power)
    x[0], x[-1] = 0.0, extent
    return x


class AxisymmetricFVM:
    def __init__(self, r, z, end_scale=1.0):
        self.r, self.z = np.asarray(r, float), np.asarray(z, float)
        if (len(self.r) < 3 or len(self.z) < 3 or self.r[0] != 0 or self.z[0] != 0
                or self.r[-1] != R or self.z[-1] != Z
                or np.any(np.diff(self.r) <= 0) or np.any(np.diff(self.z) <= 0)
                or end_scale < 0):
            raise ValueError("Invalid half-cylinder grid or end coefficient")
        self.nr, self.nz = len(self.r), len(self.z)
        self.n = self.nr * self.nz
        self.rf = (self.r[:-1] + self.r[1:]) / 2.0
        self.zf = (self.z[:-1] + self.z[1:]) / 2.0
        self.wr = np.diff(np.r_[0., self.rf, R] ** 2) / 2.0
        self.wz = np.diff(np.r_[0., self.zf, Z])
        self.volume = self.wr[:, None] * self.wz[None, :]
        self.normalizer = R * R * Z / 2.0
        self.end_scale = float(end_scale)
        self.dr, self.dz = np.diff(self.r), np.diff(self.z)

    def pack(self, T, C):
        return np.stack((T, C), axis=-1).ravel()

    def unpack(self, y):
        a = np.asarray(y).reshape(self.nr, self.nz, 2)
        return a[:, :, 0], a[:, :, 1]

    def divergence(self, state, coefficient, ambient, exchange):
        fr = np.empty((self.nr + 1, self.nz))
        fz = np.empty((self.nr, self.nz + 1))
        fr[0] = 0.0
        fr[1:-1] = (-self.rf[:, None]
                     * harmonic_mean(coefficient[:-1], coefficient[1:])
                     * np.diff(state, axis=0) / self.dr[:, None])
        fr[-1] = R * exchange * (state[-1] - ambient)
        fz[:, 0] = 0.0
        fz[:, 1:-1] = (-harmonic_mean(coefficient[:, :-1], coefficient[:, 1:])
                       * np.diff(state, axis=1) / self.dz[None, :])
        fz[:, -1] = self.end_scale * exchange * (state[:, -1] - ambient)
        return -np.diff(fr, axis=0) / self.wr[:, None] - np.diff(fz, axis=1) / self.wz[None, :]

    def rhs(self, t, y, Ta, Ca):
        T, C = self.unpack(y)
        B = heat_capacity(C)
        k = conductivity(C)
        D = moisture_diffusivity_q2(C, T, protect=True)
        return self.pack(self.divergence(T, k, Ta, H) / B,
                         self.divergence(C, D, Ca, HM))

    def loss_rates(self, y, Ca):
        # Rates normalized by dry mass; the unknown uniform dry density cancels.
        C = self.unpack(y)[1]
        side = R * HM * np.dot(self.wz, C[-1] - Ca) / self.normalizer
        end = self.end_scale * HM * np.dot(self.wr, C[:, -1] - Ca) / self.normalizer
        return np.array([side, end])

    def mean_C(self, y):
        return float(np.sum(self.volume * self.unpack(y)[1]) / self.normalizer)

    def sparsity(self):
        ids = np.arange(self.n).reshape(self.nr, self.nz)
        pairs = [(ids.ravel(), ids.ravel())]
        for a, b in ((ids[:-1].ravel(), ids[1:].ravel()),
                     (ids[:, :-1].ravel(), ids[:, 1:].ravel())):
            pairs.extend(((a, b), (b, a)))
        rows, cols = [], []
        for a, b in pairs:
            for i in (0, 1):
                for j in (0, 1):
                    rows.append(2 * a + i)
                    cols.append(2 * b + j)
        row, col = np.concatenate(rows), np.concatenate(cols)
        return coo_matrix((np.ones(len(row)), (row, col)), shape=(2*self.n, 2*self.n)).tocsc()


def structural_checks():
    f = AxisymmetricFVM(nodes(12, R, 2), nodes(10, Z, 2.5))
    rr, zz = f.r[:, None] / R, f.z[None, :] / Z
    T = 32 + 8*rr**2 + 3*zz**2
    C = 1.8 - .4*rr**2 - .3*zz**2
    y = f.pack(T, C)
    dy = f.rhs(0, y, 50., .05)
    td, cd = f.unpack(dy)
    mass = abs(np.sum(f.volume*cd)/f.normalizer + f.loss_rates(y,.05).sum())
    heat_in = (R*H*np.dot(f.wz, 50-T[-1])
               + H*np.dot(f.wr, 50-T[:, -1]))
    heat = abs(np.sum(f.volume*heat_capacity(C)*td) - heat_in)

    f0 = AxisymmetricFVM(f.r, f.z, 0.0)
    radial = CoupledRadialFVM(f.r)
    t1, c1 = 30 + 7*(f.r/R)**2, 2 - .5*(f.r/R)**2
    uniform_z = f0.pack(np.broadcast_to(t1[:, None], (f.nr,f.nz)),
                        np.broadcast_to(c1[:, None], (f.nr,f.nz)))
    two = f0.unpack(f0.rhs(0,uniform_z,50.,.05))
    one = radial.unpack(radial.rhs(0,radial.pack(t1,c1),50.,.05))
    reduction = max(float(np.max(abs(a-b[:,None]))) for a,b in zip(two,one))

    # Constant-coefficient polynomial has a known cylindrical Laplacian (4+2).
    q = rr**2 + zz**2
    lap = f.divergence(q, np.ones_like(q), 0., 0.)
    exact = 4/R**2 + 2/Z**2
    # On a uniform grid the interior polynomial is exact; graded node averages are approximate.
    fu = AxisymmetricFVM(np.linspace(0,R,13), np.linspace(0,Z,11))
    q = (fu.r[:,None]/R)**2 + (fu.z[None,:]/Z)**2
    lap = fu.divergence(q, np.ones_like(q),0.,0.)
    polynomial = float(np.max(abs(lap[:-1,:-1]-exact))/exact)

    # Check all structurally nonzero derivative locations against a numerical Jacobian.
    pat = f.sparsity().toarray() != 0
    missing = 0.0
    eps = 1e-6
    for j in range(len(y)):
        shifted = y.copy()
        shifted[j] += eps
        diff = (f.rhs(0,shifted,50.,.05)-dy)/eps
        missing = max(missing, float(np.max(abs(diff[~pat[:,j]]), initial=0.0)))
    out = {"mass_rate_abs":float(mass), "effective_heat_rate_abs":float(heat),
           "sealed_rhs_vs_independent_radial_max_abs":float(reduction),
           "uniform_polynomial_relative_error":polynomial,
           "jacobian_missing_entry_max_abs":missing,
           "volume_relative_error":float(abs(f.volume.sum()/f.normalizer-1))}
    out["pass"] = bool(mass < 1e-12 and heat < 1e-10 and reduction < 1e-10
                       and polynomial < 1e-10 and missing < 1e-10)
    return out


def provenance():
    files = [Path(__file__), Path(__file__).with_name("appendix3.py"),
             Path(__file__).with_name("problem3.py"), Path(__file__).with_name("utils.py"),
             ATTACH_DIR / "附件1.xlsx", RESULTS_DIR / "q3_validation.json"]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def run(nr, nz, end_scale=1.0, tight=False, tag=None, cap=CAP):
    OUT.mkdir(parents=True, exist_ok=True)
    tag = tag or f"r{nr}_z{nz}_end{end_scale:g}" + ("_tight" if tight else "")
    f = AxisymmetricFVM(nodes(nr,R,2.0), nodes(nz,Z,2.5), end_scale)
    Ta_fun, Ca_fun, _ = load_q3_inputs()
    rtol = 1e-8 if tight else 1e-7
    atol = np.tile([1e-8 if tight else 1e-7, 1e-10 if tight else 1e-9],f.n)
    y = f.pack(np.full((f.nr,f.nz),T0), np.full((f.nr,f.nz),C0))
    sparsity = f.sparsity()
    history = []
    snapshots = {}
    snap_times = [12*3600., 36*3600., 48*3600.]
    loss4, loss8 = np.zeros(2), np.zeros(2)
    quad4, weight4 = leggauss(4)
    quad8, weight8 = leggauss(8)
    max_mass_res = 0.
    bounds = [T0,T0,C0,C0]
    max_radial_increase = max_axial_increase = max_center_gap = 0.
    sealed_axial_spread = 0.
    event_t, event_y = None, None
    accepted, nfev, njev, nlu = 0,0,0,0
    wall = time.perf_counter()
    print_clock = wall
    next_sample = 0.

    def record(t, state):
        nonlocal max_radial_increase, max_axial_increase, max_center_gap, sealed_axial_spread
        T,C = f.unpack(state)
        loc = np.unravel_index(np.argmax(C),C.shape)
        max_radial_increase = max(max_radial_increase,float(np.max(np.diff(C,axis=0))))
        max_axial_increase = max(max_axial_increase,float(np.max(np.diff(C,axis=1))))
        max_center_gap = max(max_center_gap,float(C.max()-C[0,0]))
        if end_scale == 0:
            sealed_axial_spread = max(sealed_axial_spread,float(np.ptp(C,axis=1).max()),
                                     float(np.ptp(T,axis=1).max()))
        history.append([t,C.max(),C[0,0],C[-1,0],C[0,-1],T[0,0],
                        f.mean_C(state),f.r[loc[0]],f.z[loc[1]]])

    for start,end in ((0.,min(T_SWITCH,cap)),(T_SWITCH,cap)):
        if start >= end or event_t is not None:
            continue
        late = start >= T_SWITCH
        def environment(t):
            return (TA_AFTER,CA_AFTER) if late else (float(Ta_fun(t)),float(Ca_fun(t)))
        def rhs(t,state):
            return f.rhs(t,state,*environment(t))
        dt = (5. if tight else 10.) if not late else (30. if tight else 60.)
        solver = BDF(rhs,start,y,end,rtol=rtol,atol=atol,max_step=dt,jac_sparsity=sparsity)
        previous_M = float(f.unpack(y)[1].max())
        while solver.status == "running":
            a = solver.t
            message = solver.step()
            if solver.status == "failed":
                raise RuntimeError(message)
            accepted += 1
            b = solver.t
            dense = solver.dense_output()
            T,C = f.unpack(solver.y)
            if not np.all(np.isfinite(solver.y)) or C.min() <= 0:
                raise RuntimeError("Nonfinite or nonpositive accepted state")
            bounds = [min(bounds[0],float(T.min())),max(bounds[1],float(T.max())),
                      min(bounds[2],float(C.min())),max(bounds[3],float(C.max()))]
            current_M = float(C.max())
            if previous_M > THRESHOLD and current_M <= THRESHOLD:
                event_t = brentq(lambda t:float(f.unpack(dense(t))[1].max()-THRESHOLD),a,b,
                                  xtol=1e-6,rtol=1e-13)
                event_y = dense(event_t)
                b = event_t
            for gx,gw,total in ((quad4,weight4,loss4),(quad8,weight8,loss8)):
                q = (a+b)/2+(b-a)/2*gx
                vals = dense(q)
                rates = np.array([f.loss_rates(vals[:,j],environment(t)[1]) for j,t in enumerate(q)])
                total += (b-a)/2*np.sum(gw[:,None]*rates,axis=0)
            state_b = event_y if event_t is not None else solver.y
            residual = abs(f.mean_C(state_b)-C0+loss8.sum())
            max_mass_res = max(max_mass_res,residual)
            while next_sample <= b+1e-8:
                if next_sample >= a-1e-8:
                    record(next_sample,dense(next_sample))
                next_sample += 600.
            for target in snap_times:
                if a < target <= b:
                    snapshots[f"t{int(target)}"] = dense(target).reshape(f.nr,f.nz,2)
            if time.perf_counter()-print_clock > 25:
                print(f"{tag}: t={b/3600:.3f} h maxC={f.unpack(state_b)[1].max():.8f} "
                      f"mass={residual:.2e} steps={accepted} wall={time.perf_counter()-wall:.1f}s",flush=True)
                print_clock = time.perf_counter()
            if event_t is not None:
                record(event_t,event_y)
                snapshots["event"] = event_y.reshape(f.nr,f.nz,2)
                break
            previous_M = current_M
        nfev += solver.nfev
        njev += solver.njev
        nlu += solver.nlu
        y = solver.y.copy()
    if event_t is None:
        raise RuntimeError(f"Threshold not reached before {cap/3600:g} hours")
    T,C = f.unpack(event_y)
    loc = np.unravel_index(np.argmax(C),C.shape)
    tolerance = 1e-7
    wet = np.argwhere(C.max()-C <= tolerance)
    meta = {"version":"q3-axisymmetric-v1","tag":tag,"nr":f.nr,"nz":f.nz,
            "unknowns":2*f.n,"end_scale":end_scale,"tight":tight,
            "r_mesh_power":2.0,"z_mesh_power":2.5,"rtol":rtol,
            "atol_T":float(atol[0]),"atol_C":float(atol[1]),
            "early_max_step_s":5. if tight else 10.,"late_max_step_s":30. if tight else 60.,
            "t_star_s":float(event_t),"t_star_h":float(event_t/3600),
            "event_max_C":float(C.max()),"event_center_C":float(C[0,0]),
            "event_argmax_rz_m":[float(f.r[loc[0]]),float(f.z[loc[1]])],
            "wet_region_tolerance_C":tolerance,
            "event_wet_region_max_rz_m":[float(f.r[wet[:,0]].max()),float(f.z[wet[:,1]].max())],
            "mean_C_event":f.mean_C(event_y),"side_loss_per_dry_mass":float(loss8[0]),
            "ends_loss_per_dry_mass":float(loss8[1]),
            "mass_balance_max_abs":max_mass_res,"mass_balance_relative_initial":max_mass_res/C0,
            "mass_balance_relative_loss":max_mass_res/(C0-f.mean_C(event_y)),
            "quadrature_4_vs_8_abs":float(np.max(abs(loss4-loss8))),
            "bounds_Tmin_Tmax_Cmin_Cmax":bounds,
            "sampled_max_radial_C_increase":max_radial_increase,
            "sampled_max_axial_C_increase":max_axial_increase,
            "sampled_max_C_minus_center":max_center_gap,
            "sealed_sampled_axial_spread":sealed_axial_spread,
            "accepted_steps":accepted,"nfev":nfev,"njev":njev,"nlu":nlu,
            "wall_s":time.perf_counter()-wall,"python":platform.python_version(),
            "numpy":np.__version__,"scipy":scipy.__version__,"source_sha256":provenance(),
            "history_columns":["time_s","max_C","center_C","side_mid_C","end_axis_C",
                               "center_T","mean_C","argmax_r_m","argmax_z_m"],
            "limitations":["effective no-latent baseline","equal end/side coefficients in open case",
                           "isotropic coefficients","identical end environments","Q3 only"]}
    meta["numerical_checks_pass"] = bool(max_mass_res/C0 < 1e-6 and abs(C.max()-.15) < 1e-9
                                         and bounds[2] > 0 and bounds[3] < C0+1e-7)
    np.savez_compressed(OUT/f"{tag}.npz",r=f.r,z=f.z,wr=f.wr,wz=f.wz,
                        history=np.asarray(history),**snapshots)
    (OUT/f"{tag}.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:meta[k] for k in ("tag","t_star_h","mass_balance_relative_loss",
                                         "event_argmax_rz_m","wall_s","numerical_checks_pass")}),flush=True)
    return meta


def paired_radial(nr=80,tight=False):
    f = CoupledRadialFVM(nodes(nr,R,2.0))
    Ta,Ca,_ = load_q3_inputs()
    y = f.pack(np.full(f.n_nodes,T0),np.full(f.n_nodes,C0))
    histories = []
    event_t = None
    start_wall = time.perf_counter()
    for a,b in ((0.,T_SWITCH),(T_SWITCH,CAP)):
        late = a >= T_SWITCH
        def rhs(t,state):
            return f.rhs(t,state,TA_AFTER if late else float(Ta(t)),CA_AFTER if late else float(Ca(t)))
        def event(t,state):
            return float(f.unpack(state)[1].max()-.15)
        event.terminal,event.direction = True,-1
        sol = solve_ivp(rhs,(a,b),y,method="BDF",rtol=1e-8 if tight else 1e-7,
                        atol=np.r_[np.full(f.n_nodes,1e-8 if tight else 1e-7),
                                   np.full(f.n_nodes,1e-10 if tight else 1e-9)],
                        max_step=(5. if tight else 10.) if not late else (30. if tight else 60.),
                        jac_sparsity=f.jac_sparsity(),dense_output=True,events=event)
        if not sol.success:
            raise RuntimeError(sol.message)
        ts = np.arange(a,sol.t[-1]+1e-8,600.)
        vals = sol.sol(ts)
        histories.extend(np.column_stack([ts,vals[f.n_nodes:].max(axis=0),vals[0]]).tolist())
        y = sol.y[:,-1]
        if len(sol.t_events[0]):
            event_t = float(sol.t_events[0][0])
            histories.append([event_t,float(y[f.n_nodes:].max()),float(y[0])])
            break
    if event_t is None:
        raise RuntimeError("Radial reference did not reach the threshold")
    label = f"radial_r{nr}"+("_tight" if tight else "")
    meta = {"tag":label,"nr":f.n_nodes,"tight":tight,"t_star_s":event_t,"t_star_h":event_t/3600,
            "wall_s":time.perf_counter()-start_wall,"source_sha256":provenance()}
    OUT.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(OUT/f"{label}.npz",r=f.r,event=y,history=np.asarray(histories))
    (OUT/f"{label}.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(meta),flush=True)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nr",type=int,default=80)
    parser.add_argument("--nz",type=int,default=40)
    parser.add_argument("--end-scale",type=float,default=1.)
    parser.add_argument("--tight",action="store_true")
    parser.add_argument("--checks",action="store_true")
    parser.add_argument("--radial",action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.checks:
            checks = structural_checks()
            OUT.mkdir(parents=True,exist_ok=True)
            (OUT/"structural_checks.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
            print(json.dumps(checks,indent=2))
            if not checks["pass"]:
                raise SystemExit(1)
        elif args.radial:
            paired_radial(args.nr,args.tight)
        else:
            run(args.nr,args.nz,args.end_scale,args.tight)
