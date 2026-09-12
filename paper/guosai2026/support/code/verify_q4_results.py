"""Validate Q4 at matched times; produce source tables and figures after gates."""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator
from problem4 import OUT, Inputs, ShrinkingFVM, THRESHOLD, SWITCH
from problem2 import setup_mpl
from utils import RESULTS_DIR, FIGURES_DIR, REPORTS_DIR


def load(label):
    return np.load(OUT/f"{label}.npz"), json.loads((OUT/f"{label}.json").read_text(encoding="utf-8"))


def state_at(data, meta, t, inputs):
    """Match a new time via short BDF restart from a saved full state, not nearest-time comparison."""
    times = data["times_s"]
    i = int(np.searchsorted(times,t,side="right")-1)
    if abs(times[i]-t) < 1e-8:
        return data["Y"][i].copy()
    f = ShrinkingFVM(data["xi"])
    n = f.n
    assert times[i] >= SWITCH  # New event/report times are in the late constant environment.
    sol = solve_ivp(lambda tt,y:f.rhs(y,float(inputs.radius(tt)),50.,0.05),
                    (times[i],t),data["Y"][i],method="BDF",jac_sparsity=f.sparsity(),
                    rtol=min(meta["rtol"],1e-10),atol=np.r_[np.full(n,1e-10),np.full(n,1e-12)],
                    max_step=1.)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y[:,-1]


def physical_values(xi, Y, times, inputs, spacing=.001):
    n = len(xi)
    fixed = np.arange(21)*.001 if spacing == .001 else np.arange(5)*.005
    radii = inputs.radius(times)
    out = np.full((len(times),len(fixed)+1),np.nan)
    for i,(row,rr) in enumerate(zip(Y,radii)):
        good = fixed <= rr+1e-14
        out[i,:len(fixed)][good] = PchipInterpolator(xi,row[n:],extrapolate=False)(np.minimum(fixed[good]/rr,1.))
        out[i,-1] = row[-1]
    return out, radii, fixed


def main():
    inputs = Inputs()
    labels = ["G2","G4","G8","G4_tight","G16","G8_tight"]
    datasets = {k:load(k) for k in labels}
    production, reference, tightened = "G8", "G16", "G8_tight"
    a,ma = datasets[production]
    b,mb = datasets[reference]
    c,mc = datasets[tightened]
    n,m = len(a["xi"]),len(b["xi"])
    if not np.array_equal(a["times_s"],b["times_s"]) or not np.allclose(a["xi"],b["xi"][::2],atol=1e-14,rtol=0):
        raise RuntimeError("grids or sampling times are not nested")
    spatial_T = float(np.max(abs(a["Y"][:,:n]-b["Y"][:,:m:2])))
    spatial_C = float(np.max(abs(a["Y"][:,n:]-b["Y"][:,m::2])))
    temporal_T = float(np.max(abs(a["Y"][:,:n]-c["Y"][:,:n])))
    temporal_C = float(np.max(abs(a["Y"][:,n:]-c["Y"][:,n:])))
    # Production was refined after one table cell straddled a rounding boundary.
    critical = ma["event_s"]
    t_rep = math.ceil((max(ma["event_s"],mb["event_s"],mc["event_s"])+2.)/.36)*.36
    checked = (production,reference,tightened)
    at_critical = {k:state_at(d,md,critical,inputs) for k,(d,md) in datasets.items() if k in checked}
    at_report = {k:state_at(d,md,t_rep,inputs) for k,(d,md) in datasets.items() if k in checked}
    maxima = {k:float(z[len(datasets[k][0]["xi"]):].max()) for k,z in at_report.items()}
    critical_max = {k:float(z[len(datasets[k][0]["xi"]):].max()) for k,z in at_critical.items()}
    event_C_error = max(abs(critical_max[production]-critical_max[reference]),
                        abs(critical_max[production]-critical_max[tightened]))
    empirical_margin = 2*event_C_error + 1e-8
    idx = a["times_s"] < t_rep
    tt = np.r_[a["times_s"][idx],t_rep]
    YY = np.vstack([a["Y"][idx],at_report[production]])
    C_phys,radii,fixed = physical_values(a["xi"],YY,tt,inputs)
    C8,_,_ = physical_values(b["xi"],np.vstack([b["Y"][idx],at_report[reference]]),tt,inputs)
    physical_C_error = float(np.nanmax(abs(C_phys-C8)))
    table_times = np.r_[np.arange(21600.,t_rep,21600.),t_rep]
    table_ids = [int(np.argmin(abs(tt-t))) for t in table_times]
    table_C,table_R,table_fixed = physical_values(a["xi"],YY[table_ids],table_times,inputs,spacing=.005)
    # Dedicated table comparison includes the actual moving surface and ignores paired domain blanks.
    table8,_,_ = physical_values(b["xi"],np.vstack([b["Y"][idx],at_report[reference]])[table_ids],table_times,inputs,spacing=.005)
    finite_table = np.isfinite(table_C)
    table_changed = int(np.count_nonzero(np.round(table_C[finite_table],4)!=np.round(table8[finite_table],4)))
    bounds_pass = all(md["bounds_Tmin_Tmax_Cmin_Cmax"][2]>=-1e-10 and md["bounds_Tmin_Tmax_Cmin_Cmax"][3]<2.550000001 for _,md in datasets.values())
    gates = {
        "input_and_model_tests":all(md["model_checks"]["pass"] for _,md in datasets.values()),
        "spatial_fields_2e-5":max(spatial_T,spatial_C,physical_C_error)<2e-5,
        "temporal_fields_2e-5":max(temporal_T,temporal_C)<2e-5,
        "spatial_event_1s":abs(ma["event_s"]-mb["event_s"])<1.,
        "temporal_event_1s":abs(ma["event_s"]-mc["event_s"])<1.,
        "mass_relative_1e-6":all(md["mass_relative_error"]<1e-6 for _,md in datasets.values()),
        "heat_equation_residual_1e-6":all(md["heat_equation_residual_max"]<1e-6 for _,md in datasets.values()),
        "physical_bounds":bounds_pass,
        "strict_report_all_checked_grids":all(v<THRESHOLD for v in maxima.values()),
        "strict_report_empirical_margin":maxima[production]+empirical_margin<THRESHOLD,
        "event_within_observed_radius":t_rep<=259200.,
        "table_four_decimals":table_changed==0,
    }
    summary = {"version":"q4-baseline-v1","model":"q4-model-v1","production":production, "result_status":"PENDING",
               "critical_s":critical,"critical_h":critical/3600.,"report_s":t_rep,"report_h":t_rep/3600.,
               "report_radius_cm":float(inputs.radius(t_rep)*100),"report_maxima":maxima,"same_time_critical_maxima":critical_max,
               "empirical_C_margin":empirical_margin,"event_spatial_difference_s":abs(ma["event_s"]-mb["event_s"]),
               "event_time_difference_s":abs(ma["event_s"]-mc["event_s"]),
               "max_spatial_T_C":[spatial_T,spatial_C],"max_temporal_T_C":[temporal_T,temporal_C],
               "max_output_physical_C_difference":physical_C_error,"table_changed_four_decimal_cells":table_changed,
               "checks":gates,"pass":all(gates.values()),"runs":{k:md for k,(_,md) in datasets.items()},
               "heat_validation_scope":"weighted equation residual, not full multiphase energy conservation",
               "strict_margin_scope":"empirical grid/time differences, not a rigorous PDE error bound"}
    (RESULTS_DIR/"q4_validation.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    if not summary["pass"]:
        raise RuntimeError(f"Q4 output blocked: {gates}")
    np.savez_compressed(RESULTS_DIR/"q4_solution.npz",times_s=tt,xi=a["xi"],Y=YY,
                        radius_m=radii,physical_radii_m=fixed,C_physical=C_phys,
                        table_times_s=table_times,table_C=table_C,critical_state=at_critical[production],report_state=at_report[production])
    def safe(v):
        return None if not np.isfinite(v) else float(v)
    rows = [[float(t)]+[safe(v) for v in row] for t,row in zip(tt[1:],C_phys[1:])]
    payload = {"sheet":"Sheet1","headers":["时间/s\\距离/cm"]+[float(r*100) for r in fixed]+["药材表面"],
               "rows":rows,"report_h":t_rep/3600.}
    (OUT/"excel_payload.json").write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    with (RESULTS_DIR/"q4_table6.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f);writer.writerow(["时间/h"]+[f"{r*100:g} cm" for r in table_fixed]+["药材表面","表面半径/cm"])
        for t,row,rr in zip(table_times,table_C,table_R):
            writer.writerow([f"{t/3600:.4f}"]+["" if np.isnan(v) else f"{v:.4f}" for v in row]+[f"{rr*100:.6f}"])
    with (RESULTS_DIR/"q4_radius_output.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f);writer.writerow(["时间/s","半径/cm"]);writer.writerows(zip(tt,radii*100))
    plt=setup_mpl();FIGURES_DIR.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(6.2,3.8))
    ax.plot(tt/3600,YY[:,n],label="中心（全域最大值）")
    ax.plot(tt/3600,YY[:,-1],label="表面")
    ax.axhline(.15,color="0.3",linestyle="--",label="达标阈值")
    ax.axvline(critical/3600,color="0.6",linestyle=":")
    ax.set(xlabel="时间 / h",ylabel="干基含水率 / (kg/kg)",xlim=(0,t_rep/3600))
    ax.legend(frameon=False);fig.tight_layout()
    fig.savefig(FIGURES_DIR/"q4_C_history.pdf");fig.savefig(FIGURES_DIR/"q4_C_history.png",dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.2,3.8))
    for t,i,rr in zip(table_times,table_ids,table_R):
        ax.plot(a["xi"]*rr*100,YY[i,n:],label=f"{t/3600:.2f} h")
    ax.set(xlabel="到药材中心的距离 / cm",ylabel="干基含水率 / (kg/kg)")
    ax.legend(frameon=False,ncol=3,fontsize=7);fig.tight_layout()
    fig.savefig(FIGURES_DIR/"q4_C_profiles.pdf");fig.savefig(FIGURES_DIR/"q4_C_profiles.png",dpi=160);plt.close(fig)
    # Small visible table companion; this is a result record, not paper prose.
    headers=["时间/h","0 cm","0.5 cm","1.0 cm","1.5 cm","2.0 cm","表面","表面半径/cm"]
    lines=["# 第四问表6（基线结果，待审）","", "|"+"|".join(headers)+"|", "|"+"|".join(["---"]*len(headers))+"|"]
    for t,row,rr in zip(table_times,table_C,table_R):
        lines.append("|"+"|".join([f"{t/3600:.4f}"]+["—" if np.isnan(v) else f"{v:.4f}" for v in row]+[f"{rr*100:.6f}"])+"|")
    lines += ["", "—表示该固定半径在当前药材区域之外。表面列对应各时刻真实外半径。末行以未舍入值通过严格阈值检查；四位显示可能仍为0.1500。"]
    (REPORTS_DIR/"Q4_TABLE6.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("critical_h","report_h","report_radius_cm","report_maxima","event_spatial_difference_s","pass")},ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
