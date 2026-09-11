"""Bounded model-selection diagnostic; never writes the official result1.

Prescribes baseline moisture loss, then solves ONLY the constant-property heat
equation. This tests adding surface latent heat without changing mass transfer.
The air humidity interpretation and pressure are diagnostic assumptions.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csc_matrix, lil_matrix

from radial_fvm import RadialFVM
from utils import ROOT, R, L, RHO, CP, H, HM, C0, T0, load_oven_table


def main():
    src = ROOT / 'results/q1_solution.npz'
    source_hash = hashlib.sha256(src.read_bytes()).hexdigest()
    base = np.load(src)
    ts = np.r_[0., base['times']]
    cs = np.r_[C0, base['C_full'][:, -1]]
    ot, ta, ca = load_oven_table()
    rho_d = RHO / (1 + C0)  # Initial wet density interpretation, fixed volume.
    area, volume = 2*np.pi*R*L, np.pi*R**2*L
    # NISTIR 5078 Table 1, first page. MPa -> Pa; log-linear interpolation.
    sat_t = np.r_[0.01, np.arange(1., 51.)]
    sat_p = 1e6 * np.array([
        .0006117,.0006571,.0007060,.0007581,.0008135,.0008726,
        .0009354,.0010021,.0010730,.0011483,.0012282,.0013130,
        .0014028,.0014981,.0015990,.0017058,.0018188,.0019384,
        .0020647,.0021983,.0023393,.0024882,.0026453,.0028111,
        .0029858,.0031699,.0033639,.0035681,.0037831,.0040092,
        .0042470,.0044969,.0047596,.0050354,.0053251,.0056290,
        .0059479,.0062823,.0066328,.0070002,.0073849,.0077878,
        .0082096,.0086508,.0091124,.0095950,.010099,.010627,
        .011177,.011752,.012352])
    w = np.interp(ts, ot, ca)
    air_t = np.interp(ts, ot, ta)
    pva = 101325*w/(.621945+w)
    dew = np.interp(np.log(pva), np.log(sat_p), sat_t)
    records, solutions = [], {}
    for N, latent in [(160, 0.), (160, 2.4e6), (320, 2.4e6),
                      (160, 2.38e6), (160, 2.50e6)]:
        fvm = RadialFVM(N)
        n = N+1
        mat = csc_matrix(fvm.M_heat)
        jac = lil_matrix((n+2, n+2))
        jac[:n, :n] = mat
        jac[n, n-1] = -area*H
        jac = jac.tocsc()

        def rhs(t, y):
            ambient = np.interp(t, ot, ta)
            js = rho_d*HM*(np.interp(t, ts, cs)-np.interp(t, ot, ca))
            out = np.empty(n+2)
            out[:n] = mat @ y[:n]
            out[n-1] += fvm._heat_force_coef*ambient
            out[n-1] -= R*latent*js/(RHO*CP*fvm.W[-1])
            out[n] = area*H*(ambient-y[n-1])
            out[n+1] = area*latent*js
            return out

        sol = solve_ivp(rhs, (0., 1800.), np.r_[np.full(n,T0),0.,0.],
                        method='BDF', jac=jac, t_eval=ts,
                        rtol=1e-8, atol=1e-9, max_step=1.)
        if not sol.success:
            raise RuntimeError(sol.message)
        temp = sol.y[:n].T
        mean = temp @ (fvm.W/fvm.W.sum())
        energy = RHO*CP*volume*(mean-T0)
        residual = energy - (sol.y[n]-sol.y[n+1])
        surface = temp[:, -1]
        conflict = (surface < dew) & (cs > w)
        tag = f'N{N}_Lv{int(latent)}'
        rec = dict(tag=tag, N=N, Lv_J_kg=latent,
                   final_center_C=float(temp[-1, 0]),
                   final_surface_C=float(surface[-1]),
                   min_surface_C=float(surface.min()),
                   min_surface_time_s=float(ts[surface.argmin()]),
                   final_mean_C=float(mean[-1]),
                   convective_energy_J=float(sol.y[n,-1]),
                   latent_energy_J=float(sol.y[n+1,-1]),
                   sensible_energy_J=float(energy[-1]),
                   max_energy_residual_J=float(np.max(np.abs(residual))),
                   dewpoint_conflict_samples=int(conflict.sum()),
                   first_conflict_sample_s=float(ts[conflict][0]) if conflict.any() else None)
        records.append(rec)
        solutions[tag] = temp
        print(json.dumps(rec), flush=True)

    main_temp = solutions['N320_Lv2400000']
    grid_error = np.max(np.abs(main_temp[:, ::2]-solutions['N160_Lv2400000']))
    # Baseline N640 is sampled at N160 nodes for an independent implementation check.
    zero_error = np.max(np.abs(solutions['N160_Lv0'][1:]-base['T_full'][:, ::4]))
    pressure_cases = []
    for pressure in (80000.,101325.,120000.):
        pv = pressure*w/(.621945+w)
        td = np.interp(np.log(pv),np.log(sat_p),sat_t)
        mask = (main_temp[:, -1] < td) & (cs > w)
        pressure_cases.append(dict(pressure_Pa=pressure,
                              dewpoint_initial_C=float(td[0]),
                              dewpoint_final_C=float(td[-1]),
                              conflict_samples=int(mask.sum())))
    report = dict(purpose='Exploratory feasibility screening, not official predictions',
                  source=str(src), source_sha256=source_hash,
                  assumptions=['rho=820 interpreted as initial wet density',
                               'fixed initial heat capacity and cylinder volume',
                               'prescribed moisture from original N640 solution, interpolated at 1 s',
                               'humidity w=kg water/kg dry air; ideal moist air; sea-level pressure for main check',
                               'surface evaporation only; NIST pure-water saturation limits'],
                  saturation_source='https://www.nist.gov/document/nistir5078-tab1pdf',
                  grid160_320_max_temperature_difference_C=float(grid_error),
                  no_latent_vs_baseline640_max_difference_C=float(zero_error),
                  dewpoint_initial_C=float(dew[0]),dewpoint_final_C=float(dew[-1]),
                  pressure_cases=pressure_cases, runs=records)
    out = ROOT/'results/diagnostics/q1_latent_upgrade'
    out.mkdir(parents=True,exist_ok=True)
    (out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    np.savetxt(out/'temperature_screening.csv',np.column_stack([
        ts,air_t,cs,dew,solutions['N160_Lv0'][:,0],solutions['N160_Lv0'][:,-1],
        main_temp[:,0],main_temp[:,-1]]),delimiter=',',comments='',
        header='time_s,air_T_C,surface_C_drybasis,air_dewpoint_C,baseline_center_T_C,baseline_surface_T_C,latent_center_T_C,latent_surface_T_C')
    assert hashlib.sha256(src.read_bytes()).hexdigest() == source_hash
    print(json.dumps({k:v for k,v in report.items() if k not in ('runs','assumptions')},indent=2))


if __name__ == '__main__':
    main()
