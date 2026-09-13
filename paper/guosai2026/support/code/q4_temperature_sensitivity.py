"""Conditional late-temperature scenarios with the existing Appendix-4 operator."""
from pathlib import Path
import hashlib
import json
import time

import numpy as np
from scipy.integrate import solve_ivp
from numpy.polynomial.legendre import leggauss

from problem4 import Inputs, ShrinkingFVM, SWITCH, THRESHOLD, CAP
from radial_fvm import graded_radial_nodes
from utils import R, T0, C0, HM, RESULTS_DIR

OUT = RESULTS_DIR / 'diagnostics' / 'q4_temperature_sensitivity'


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = Inputs()
    rows = []
    gx, gw = leggauss(4)
    for level in (4, 8):
        fvm = ShrinkingFVM(graded_radial_nodes(level) / R)
        n = fvm.n
        atol = np.r_[np.full(n, 1e-8), np.full(n, 1e-10)]
        for geometry in ('fixed', 'shrink'):
            radius = (lambda t: R) if geometry == 'fixed' else inputs.radius
            initial = np.r_[np.full(n, T0), np.full(n, C0)]
            early = solve_ivp(
                lambda t, y: fvm.rhs(y, float(radius(t)), *inputs.environment(t)),
                (0., SWITCH), initial, method='BDF', rtol=1e-8, atol=atol,
                max_step=10., jac_sparsity=fvm.sparsity())
            if not early.success:
                raise RuntimeError(early.message)
            for temperature in (48., 50., 52.):
                started = time.perf_counter()
                def event(t, y):
                    return float(np.max(y[n:]) - THRESHOLD)
                event.terminal, event.direction = True, -1
                cap = 240 * 3600. if geometry == 'fixed' else CAP
                sol = solve_ivp(
                    lambda t, y: fvm.rhs(y, float(radius(t)), temperature, .05),
                    (SWITCH, cap), early.y[:, -1], method='BDF', rtol=1e-8,
                    atol=atol, max_step=60., jac_sparsity=fvm.sparsity(),
                    dense_output=True, events=event)
                if not sol.success or len(sol.t_events[0]) != 1:
                    raise RuntimeError('Scenario did not reach threshold within input coverage')
                critical = float(sol.t_events[0][0])
                loss = 0.
                for start in range(0, len(sol.t)-1, 128):
                    a, b = sol.t[start:-1][:128], sol.t[start+1:][:128]
                    ts = ((a+b)[:, None]/2 + (b-a)[:, None]/2*gx).ravel()
                    surface = sol.sol(ts)[-1]
                    rr = R if geometry == 'fixed' else inputs.radius(ts)
                    flux = 2*HM/rr*(surface-.05)
                    loss += float(np.sum(flux.reshape(-1, 4)*gw*(b-a)[:, None]/2))
                delta = float(2*np.dot(fvm.w, sol.y[n:, -1]-early.y[n:, -1]))
                residual = abs(delta+loss)/max(abs(delta), abs(loss), 1e-12)
                record = {
                    'level': level, 'geometry': geometry, 'late_T_C': temperature,
                    'critical_h': critical/3600., 'critical_s': critical,
                    'late_mass_relative_residual': residual,
                    'terminal_max_C': float(sol.y[n:, -1].max()),
                    'max_center_gap': float(np.max(sol.y[n:].max(axis=0)-sol.y[n])),
                    'finite': bool(np.all(np.isfinite(sol.y))),
                    'min_C': float(sol.y[n:].min()), 'wall_s': time.perf_counter()-started}
                if not record['finite'] or record['min_C'] < 0 or residual > 1e-6:
                    raise RuntimeError(record)
                rows.append(record)
                (OUT / f'{geometry}_G{level}_T{temperature:.0f}.json').write_text(
                    json.dumps(record, indent=2), encoding='utf-8')
                print(json.dumps(record), flush=True)
    comparisons = []
    for temperature in (48., 50., 52.):
        selected = [r for r in rows if r['late_T_C'] == temperature]
        values = {(r['geometry'], r['level']): r for r in selected}
        fixed = values['fixed', 8]['critical_h']
        shrink = values['shrink', 8]['critical_h']
        differences = {g: abs(values[g, 8]['critical_s']-values[g, 4]['critical_s'])
                       for g in ('fixed', 'shrink')}
        comparisons.append({'late_T_C': temperature, 'fixed_h': fixed, 'shrink_h': shrink,
                            'saving_h': fixed-shrink, 'saving_pct': 100*(1-shrink/fixed),
                            'grid_difference_s': differences})
    # The nominal scenario must independently reproduce the existing critical roots.
    baseline = next(r for r in comparisons if r['late_T_C'] == 50.)
    baseline_differences = {
        'fixed_s': abs(baseline['fixed_h']-129.8442292)*3600,
        'shrink_s': abs(baseline['shrink_h']-51.0871229810)*3600}
    result = {'scope': 'after 4 h only; Ca=0.05; prescribed R(t) held fixed across temperatures',
              'rows': rows, 'comparisons': comparisons,
              'baseline_difference_s': baseline_differences,
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (Path(__file__), Path(__file__).with_name('problem4.py'))},
              'pass': max(baseline_differences.values()) < .1 and
                      max(v for r in comparisons for v in r['grid_difference_s'].values()) < 3.}
    (OUT / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result['comparisons'], indent=2), flush=True)
    if not result['pass']:
        raise RuntimeError('Baseline or grid check failed')


if __name__ == '__main__':
    run()
