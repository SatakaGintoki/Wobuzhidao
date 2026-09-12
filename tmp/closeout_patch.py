from pathlib import Path
import shutil
import hashlib
import json

root = Path(__file__).resolve().parents[1]
archive = root / 'results/archive/pre-closeout-20260911'
archive.mkdir(parents=True, exist_ok=True)
paths = list((root/'results').glob('q[12]*')) + list((root/'results').glob('result[12].xlsx')) + list((root/'figures').glob('q[12]*.pdf'))
manifest = {}
for p in paths:
    dest = archive/p.relative_to(root)
    if dest.exists():
        raise RuntimeError('Archive already exists: '+str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    manifest[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
(archive/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

for q in (1,2):
    path = root/f'code/problem{q}.py'
    s = path.read_text(encoding='utf-8')
    s = s.replace('from q1_analytic import BesselDuhamel', 'from q1_analytic import BesselDuhamel, converged_reference\nfrom delivery import make_gate, require_delivery')
    s = s.replace('info["C_above_C0"] <= 1e-8 and C_out.min() >= -1e-8', 'info["C_above_C0"] <= 1e-8 and info["C_below_Ca_min"] <= 1e-8')
    if q == 1:
        s = s.replace('from scipy.integrate import solve_ivp', 'from scipy.integrate import solve_ivp, quad')
        start = s.index('    ts = np.linspace', s.index('def conservation_heat'))
        end = s.index('    denom = ', start)
        s = s[:start] + '''    flux = lambda x: float(Ta_fun(x)) - float(dense_state(pieces, x)[-1])
    Qraw, qerr = quad(flux, 0, t, points=Ta_fun.t[(Ta_fun.t > 0) & (Ta_fun.t < t)], epsabs=1e-9, epsrel=1e-10, limit=500)
    Q = 2.0 * np.pi * R * L * H * Qraw
''' + s[end:]
        start = s.index('    ts = np.linspace', s.index('def conservation_moisture'))
        end = s.index('    rhs = ', start)
        s = s[:start] + '''    flux = lambda x: HM * (float(dense_state(pieces, x)[-1]) - float(Ca_fun(x)))
    I, qerr = quad(flux, 0, t, points=Ca_fun.t[(Ca_fun.t > 0) & (Ca_fun.t < t)], epsabs=1e-14, epsrel=1e-10, limit=500)
''' + s[end:]
        s = s.replace('"relative_residual": abs(E - Q) / denom,', '"relative_residual": abs(E - Q) / denom,\n        "quadrature_abs_error": qerr, "quadrature": "adaptive QUADPACK on PCHIP intervals",')
        s = s.replace('"relative_residual": abs(MC - rhs) / denom,', '"relative_residual": abs(MC - rhs) / denom,\n        "quadrature_abs_error": qerr, "quadrature": "adaptive QUADPACK on PCHIP intervals",')
        old = '''    heat_ref = BesselDuhamel(Bi=Bi, diffusivity=ALPHA, R=R, n_terms=120)
    T_ref = heat_ref.evaluate_many(OUTPUT_RADII_M, times, Ta_fun, T0)'''
        s = s.replace(old, '    T_ref, heat_truncation = converged_reference(Bi, ALPHA, R, OUTPUT_RADII_M, times, Ta_fun, T0, start_terms=120)')
        s = s.replace('    moist_ref = BesselDuhamel(Bi=Bi_m, diffusivity=D0, R=R, n_terms=120)\n    C_ref = moist_ref.evaluate_many(OUTPUT_RADII_M, times, Ca_fun, C0)', '    C_ref, moisture_truncation = converged_reference(Bi_m, D0, R, OUTPUT_RADII_M, times, Ca_fun, C0)')
        s = s.replace('bounds = assert_physical(pub["T_out"], pub["C_out"], Ta_fun, Ca_fun)', 'bounds = assert_physical(pub["YT"], pub["YC"], Ta_fun, Ca_fun)')
        extra = '''        "space_abs": abs_2e5,
        "space_paper": paper_4dp_stable,
        "all_finite": np.isfinite(pub["YT"]).all() and np.isfinite(pub["YC"]).all(),
        "heat_reference_truncation": heat_truncation["passed"],
        "heat_reference_error": bessel_T["max_abs"] <= 2e-5,
'''
        s = s.replace('        T_full=pub["YT"],', '        checkpoint_times=np.r_[0., TABLE_TIMES],\n        T_checkpoints=np.vstack([pub["T_init"], pub["YT"][TABLE_TIMES.astype(int)-1]]),\n        C_checkpoints=np.vstack([pub["C_init"], pub["YC"][TABLE_TIMES.astype(int)-1]]),\n        T_full=pub["YT"],')
    else:
        s = s.replace('    moist_ref = BesselDuhamel(Bi=Bi_m, diffusivity=D_freeze, R=R, n_terms=80)\n    C_ref = moist_ref.evaluate_many(OUTPUT_RADII_M, times, Ca_fun, C0)', '    C_ref, moisture_truncation = converged_reference(Bi_m, D_freeze, R, OUTPUT_RADII_M, times, Ca_fun, C0)')
        s = s.replace('bounds = assert_physical(pub["T_out"], pub["C_out"], Ta_fun, Ca_fun)', 'bounds = assert_physical(pub["Y_full"][:, :n], pub["Y_full"][:, n:], Ta_fun, Ca_fun)')
        extra = '''        "space_abs": abs_ok,
        "space_paper": paper_ok,
        "all_finite": np.isfinite(pub["Y_full"]).all(),
        "manufactured_solution": mms["T_max_abs"] <= 2e-5 and mms["C_max_abs"] <= 2e-5,
'''
        s = s.replace('        r=fvm.r,', '        r=fvm.r,\n        output_radii_m=OUTPUT_RADII_M,\n        checkpoint_times=np.r_[0., 1., 60., 100., TABLE_TIMES],\n        T_checkpoints=pub["Y_full"][np.r_[0., 1., 60., 100., TABLE_TIMES].astype(int), :n],\n        C_checkpoints=pub["Y_full"][np.r_[0., 1., 60., 100., TABLE_TIMES].astype(int), n:],')
        start = s.index('def plot_figures')
        a = s.index('    ax.legend(', start)
        b = s.index('\n', a)
        s = s[:a] + '    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.02))' + s[b:]
    start = s.index('    delivery = {', s.index('def main'))
    end = s.index('    print("delivery", delivery)', start)
    s = s[:start] + '''    delivery = make_gate({
''' + extra + '''        "time_abs": time_sens["T"]["max_abs"] <= 2e-5 and time_sens["C"]["max_abs"] <= 2e-5,
        "time_paper": time_4dp["T"]["paper_changed_cells"] == 0 and time_4dp["C"]["paper_changed_cells"] == 0,
        "temperature_bounds": bounds["T_bounds_ok"],
        "moisture_bounds": bounds["C_bounds_ok"],
        "moisture_reference_truncation": moisture_truncation["passed"],
        "frozen_reference_error": frozen["max_abs"] <= 2e-5,
        "heat_balance": cons_T["relative_residual"] <= 1e-6,
        "moisture_balance": cons_C["relative_residual"] <= 1e-6,
    })
''' + s[end:]
    start = s.index('    np.savez(', s.index('def main'))
    end = s.index('    paper_T = ', start)
    writers = s[start:end]
    s = s[:start] + s[end:]
    s = s.replace(f'"result_version": "q{q}-baseline-v{2 if q==1 else 1}"', f'"result_version": "q{q}-closeout-v1"')
    s = s.replace('        "frozen_D_moisture_vs_analytic": frozen,', '        "reference_truncation_C": moisture_truncation,\n        "frozen_D_moisture_vs_analytic": frozen,')
    if q == 1:
        s = s.replace('        "bessel_temperature": bessel_T,', '        "reference_truncation_T": heat_truncation,\n        "bessel_temperature": bessel_T,')
    pos = s.index(f'    (RESULTS_DIR / "q{q}_validation.json").write_text')
    s = s[:pos] + f'    require_delivery(validation, RESULTS_DIR / "diagnostics/q{q}_delivery/latest.json")\n' + writers + s[pos:]
    start = s.index('    if not delivery["meets_delivery_gate"]:', pos)
    end = s.index('\n\n', start)
    s = s[:start] + s[end:]
    path.write_text(s, encoding='utf-8')
