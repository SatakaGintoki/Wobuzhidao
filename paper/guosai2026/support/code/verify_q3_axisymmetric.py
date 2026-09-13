"""Audit Q3 dimensional comparisons without updating the four official solutions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from q3_axisymmetric import OUT
from utils import RESULTS_DIR


def read_case(label):
    return json.loads((OUT/f"{label}.json").read_text(encoding="utf-8"))


def summarize(production="r160_z80_end1", tight="r160_z80_end1_tight"):
    original = json.loads((RESULTS_DIR/"q3_validation.json").read_text(encoding="utf-8"))
    structural = json.loads((OUT/"structural_checks.json").read_text(encoding="utf-8"))
    labels = ["r80_z40_end1","r160_z40_end1","r80_z80_end1",production,tight]
    labels = list(dict.fromkeys(labels))
    cases = {label:read_case(label) for label in labels}
    sealed = read_case("r80_z40_end0")
    radial80 = read_case("radial_r80")
    rows = []
    for label,d in cases.items():
        radial = read_case(f"radial_r{d['nr']-1}" + ("_tight" if d["tight"] else ""))
        delta = d["t_star_s"]-radial["t_star_s"]
        rows.append({"label":label,"nr":d["nr"],"nz":d["nz"],"t_star_h":d["t_star_h"],
                     "paired_radial_h":radial["t_star_h"],"end_effect_s":delta,
                     "end_effect_pct":100*delta/radial["t_star_s"],
                     "difference_from_official_s":d["t_star_s"]-original["t_star_s"],
                     "mass_relative_loss":d["mass_balance_relative_loss"],"wall_s":d["wall_s"]})
    base = cases[production]
    numerical = {
        "radial_refinement_at_z40_s":cases["r160_z40_end1"]["t_star_s"]-cases["r80_z40_end1"]["t_star_s"],
        "radial_refinement_at_z80_s":cases["r160_z80_end1"]["t_star_s"]-cases["r80_z80_end1"]["t_star_s"],
        "axial_refinement_at_r80_s":cases["r80_z80_end1"]["t_star_s"]-cases["r80_z40_end1"]["t_star_s"],
        "axial_refinement_at_r160_s":cases["r160_z80_end1"]["t_star_s"]-cases["r160_z40_end1"]["t_star_s"],
        "time_tightening_s":cases[tight]["t_star_s"]-base["t_star_s"],
        "sealed_2d_vs_paired_1d_s":sealed["t_star_s"]-radial80["t_star_s"],
    }
    production_radial = read_case(f"radial_r{base['nr']-1}")
    relative_to_original = 100*(base["t_star_s"]-original["t_star_s"])/original["t_star_s"]
    source_checks = {}
    for label,d in {**cases,"sealed":sealed,"radial80":radial80}.items():
        source_checks[label] = all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha
                                   for p,sha in d["source_sha256"].items())
    full_fields = {}
    fine = np.load(OUT/"r160_z80_end1.npz")
    for label,axis in (("r80_z80_end1",0),("r160_z40_end1",1),(tight,None)):
        other = np.load(OUT/f"{label}.npz")
        errors = np.zeros(2)
        for key in ("t43200","t129600","t172800"):
            selected = fine[key][::2] if axis == 0 else fine[key][:,::2] if axis == 1 else fine[key]
            errors = np.maximum(errors,np.max(abs(selected-other[key]),axis=(0,1)))
        full_fields[label] = {"max_T_difference_C":float(errors[0]),"max_C_difference":float(errors[1]),
                              "times_h":[12,36,48],"comparison":"shared nodes at identical physical times"}
    snapshots = np.load(OUT/f"{production}.npz")
    radial_arrays = np.load(OUT/f"radial_r{base['nr']-1}.npz")
    h2, h1 = snapshots["history"],radial_arrays["history"]
    times,i2,i1 = np.intersect1d(h2[:,0],h1[:,0],return_indices=True)
    difference = h2[i2,1]-h1[i1,1]
    snapshot_stats = {}
    for key in ("t43200","t129600","t172800","event"):
        C = snapshots[key][:,:,1]
        snapshot_stats[key] = {"center_C":float(C[0,0]),"side_mid_C":float(C[-1,0]),
                               "end_axis_C":float(C[0,-1]),"corner_C":float(C[-1,-1]),
                               "min_C":float(C.min()),"max_C":float(C.max())}
    gates = {
        "structural_checks":structural["pass"],
        "source_hashes_match":all(source_checks.values()),
        "sealed_trajectory_reduction":abs(numerical["sealed_2d_vs_paired_1d_s"])<.1
                                      and sealed["sealed_sampled_axial_spread"]<1e-6,
        "all_cases_mass_and_physical_checks":all(d["numerical_checks_pass"] for d in cases.values()),
        "quadrature_check":all(d["quadrature_4_vs_8_abs"]<1e-6 for d in cases.values()),
        "radial_event_change_below_0_1pct":abs(numerical["radial_refinement_at_z80_s"])/base["t_star_s"]<.001,
        "axial_event_change_below_0_1pct":abs(numerical["axial_refinement_at_r160_s"])/base["t_star_s"]<.001,
        "time_event_change_below_0_01pct":abs(numerical["time_tightening_s"])/base["t_star_s"]<.0001,
        "event_at_center_with_tolerance":all(d["event_max_C"]-d["event_center_C"]<1e-7 for d in cases.values()),
        "sampled_center_controls":all(d["sampled_max_C_minus_center"]<1e-7 for d in cases.values()),
    }
    summary = {"version":"q3-axisymmetric-v1","production":production,"time_check":tight,
               "official_1d_t_star_h":original["t_star_h"],"official_1d_t_rep_h":original["t_rep_h"],
               "production_2d_t_star_h":base["t_star_h"],
               "production_paired_1d_t_star_h":production_radial["t_star_h"],
               "production_vs_official_pct":relative_to_original,
               "paired_end_effect_s":base["t_star_s"]-production_radial["t_star_s"],
               "paired_end_effect_pct":100*(base["t_star_s"]-production_radial["t_star_s"])/production_radial["t_star_s"],
               "paired_common_600s_max_C_difference":float(abs(difference).max()),
               "common_samples":len(times),"snapshot_stats":snapshot_stats,"convergence":numerical,
               "shared_node_field_checks":full_fields,
               "sealed_axial_spread":sealed["sealed_sampled_axial_spread"],
               "max_mass_relative_loss":max(d["mass_balance_relative_loss"] for d in cases.values()),
               "production_mean_C_event":base["mean_C_event"],
               "production_end_loss_fraction":base["ends_loss_per_dry_mass"]/(base["ends_loss_per_dry_mass"]+base["side_loss_per_dry_mass"]),
               "wet_region_tolerance_C":base["wet_region_tolerance_C"],
               "production_wet_region_max_rz_m":base["event_wet_region_max_rz_m"],
               "rows":rows,"gates":gates,"pass":all(gates.values()),
               "interpretation":"Dimensional sensitivity of the stipulated effective Q3 model; not experimental validation or a rigorous PDE error bound.",
               "q4_scope":"Not extended; Q3 evidence does not validate the Q4 time-saving percentage."}
    deltas = {row["label"]:row["end_effect_s"] for row in rows}
    summary["paired_effect_convergence_s"] = {
        "radial_at_z40":deltas["r160_z40_end1"]-deltas["r80_z40_end1"],
        "radial_at_z80":deltas["r160_z80_end1"]-deltas["r80_z80_end1"],
        "axial_at_r80":deltas["r80_z80_end1"]-deltas["r80_z40_end1"],
        "axial_at_r160":deltas["r160_z80_end1"]-deltas["r160_z40_end1"],
        "time":deltas[tight]-deltas[production],
    }
    (OUT/"comparison.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    with (OUT/"comparison.csv").open("w",newline="",encoding="utf-8-sig") as fh:
        writer=csv.DictWriter(fh,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    np.savetxt(OUT/"paired_history.csv",np.column_stack([times,h1[i1,1],h2[i2,1],difference]),delimiter=",",
               header="time_s,max_C_1d,max_C_2d,difference_2d_minus_1d",comments="")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not summary["pass"]:
        raise RuntimeError("Dimensional comparison verification failed")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--production",default="r160_z80_end1")
    parser.add_argument("--tight",default="r160_z80_end1_tight")
    args=parser.parse_args()
    summarize(args.production,args.tight)
