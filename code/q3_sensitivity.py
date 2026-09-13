"""Bounded Q3 sensitivity analysis for late environment and hm."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np

import problem3
import radial_coupled
from utils import H, HM

OUT = Path(problem3.RESULTS_DIR) / "diagnostics/q3_sensitivity"

# hm_scale is applied for the whole trajectory; Ta/Ca use the 4 h switch.
CASES = [
    ("baseline", 50.0, 0.05, 1.0),
    ("Ta_minus2", 48.0, 0.05, 1.0),
    ("Ta_plus2", 52.0, 0.05, 1.0),
    ("hm_minus20pct", 50.0, 0.05, 0.8),
    ("hm_plus20pct", 50.0, 0.05, 1.2),
    ("Ca_minus10pct", 50.0, 0.045, 1.0),
    ("Ca_plus10pct", 50.0, 0.055, 1.0),
]


def make_case_functions(Ta0, Ca0, hm_scale):
    Ta_base, Ca_base, _ = problem3.load_q3_inputs()

    class Late:
        def __init__(self, base, after):
            self.base, self.after = base, float(after)

        def __call__(self, t):
            if np.ndim(t) == 0:
                return float(self.base(t)) if float(t) <= problem3.T_SWITCH else self.after
            t = np.asarray(t, dtype=float)
            return np.where(t <= problem3.T_SWITCH, self.base(t), self.after)

    return Late(Ta_base, Ta0), Late(Ca_base, Ca0), hm_scale


def run_case_sensitivity(level, Ta_fun, Ca_fun, hm_scale, tag):
    """Use the production integrator with a scaled surface mass-transfer coefficient."""
    original = problem3.CoupledRadialFVM.rhs

    def rhs_scaled(self, t, y, Ta, Ca, **kwargs):
        # run_case supplies boundary functions; scale only the prescribed hm.
        n = self.n_nodes
        T, C = self.unpack(y)
        kn = np.asarray(radial_coupled.conductivity(C), dtype=float)
        Bn = np.asarray(radial_coupled.heat_capacity(C), dtype=float)
        Dn = np.asarray(radial_coupled.moisture_diffusivity_q2(C, T, protect=True), dtype=float)
        kf = radial_coupled.harmonic_mean(kn[:-1], kn[1:])
        Df = radial_coupled.harmonic_mean(Dn[:-1], Dn[1:])
        FT = -self.r_half*kf*np.diff(T)/self.dr_face
        FC = -self.r_half*Df*np.diff(C)/self.dr_face
        td = np.empty_like(T); cd = np.empty_like(C)
        td[0] = -FT[0]/(Bn[0]*self.W[0]); cd[0] = -FC[0]/self.W[0]
        td[1:-1] = (FT[:-1]-FT[1:])/(Bn[1:-1]*self.W[1:-1])
        cd[1:-1] = (FC[:-1]-FC[1:])/self.W[1:-1]
        radius = float(self.r[-1])
        fts = radius*H*(T[-1]-Ta)
        fcs = radius*(HM*hm_scale)*(C[-1]-Ca)
        td[-1] = (FT[-1]-fts)/(Bn[-1]*self.W[-1]); cd[-1] = (FC[-1]-fcs)/self.W[-1]
        return self.pack(td, cd)

    problem3.CoupledRadialFVM.rhs = rhs_scaled
    try:
        return problem3.run_case(level, Ta_fun, Ca_fun, 72*3600., problem3.RTOL,
            problem3.ATOL_T, problem3.ATOL_C, problem3.MAX_STEP_EARLY,
            problem3.MAX_STEP_LATE, tag=tag, audit_balances=False)
    finally:
        problem3.CoupledRadialFVM.rhs = original


def run_one(tag, ta, ca, scale):
    taf, caf, hs = make_case_functions(ta, ca, scale)
    result = run_case_sensitivity(8, taf, caf, hs, tag)
    record = {
        "case": tag, "Ta_after_C": ta, "Ca_after": ca, "hm_scale": scale,
        "hm_window": "full_horizon", "Ca_window": "after_4h", "Ta_window": "after_4h",
        "t_star_s": float(result["t_star"]), "t_star_h": float(result["t_star"]/3600),
        "M_star": float(result["event"]["M_star"]), "rmax_star_cm": float(result["event"]["rmax_star_cm"]),
        "nodes": int(result["n_nodes"]), "rtol": problem3.RTOL,
        "atol_T": problem3.ATOL_T, "atol_C": problem3.ATOL_C,
    }
    (OUT / f"{tag}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    np.savez_compressed(OUT / f"{tag}.npz", times=result["times"], Y=result["Y"], r=result["fvm"].r,
                        t_star=result["t_star"], y_star=result["y_star"])
    return record


def write_summary(rows):
    base = next(r["t_star_h"] for r in rows if r["case"] == "baseline")
    for row in rows:
        row["relative_change_pct"] = 100.0 * (row["t_star_h"] - base) / base
    (OUT / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["case,Ta_after_C,Ca_after,hm_scale,t_star_h,relative_change_pct"]
    lines += [f"{r['case']},{r['Ta_after_C']},{r['Ca_after']},{r['hm_scale']},{r['t_star_h']:.6f},{r['relative_change_pct']:.3f}" for r in rows]
    (OUT / "summary.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--rerun", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = CASES if args.only is None else [c for c in CASES if c[0] in args.only]
    rows = []
    for tag, ta, ca, scale in wanted:
        existing = OUT / f"{tag}.json"
        if existing.exists() and not args.rerun:
            rows.append(json.loads(existing.read_text(encoding="utf-8")))
            continue
        rows.append(run_one(tag, ta, ca, scale))
    if args.only is not None:
        by_tag = {r["case"]: r for r in rows}
        ordered = []
        for tag, ta, ca, scale in CASES:
            path = OUT / f"{tag}.json"
            if tag in by_tag:
                ordered.append(by_tag[tag])
            elif path.exists():
                ordered.append(json.loads(path.read_text(encoding="utf-8")))
        rows = ordered
    write_summary(rows)
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
