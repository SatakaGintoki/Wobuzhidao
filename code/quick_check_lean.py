"""Bounded kernel, short integration and sample export checks for lean scripts."""
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import numpy as np
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'paper' / 'guosai2026' / '支撑材料_按问复现'
TMP = ROOT / '_tmp' / 'lean_quick_check'
TMP.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'code'))
from radial_fvm import RadialFVM
from radial_coupled import CoupledRadialFVM
from problem4 import ShrinkingFVM


class StopAfterCheck(Exception):
    pass


def check(q):
    path = PACKAGE / f'Q{q}.py'
    compile(path.read_text(encoding='utf-8'), path.name, 'exec')
    spec = importlib.util.spec_from_file_location(f'lean_q{q}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = {'question': q, 'syntax_imports': True, 'lines': len(path.read_text(encoding='utf-8').splitlines())}
    original_integrate = module.integrate

    def intercept(rhs, interval, initial, **options):
        scope = inspect.currentframe().f_back.f_locals
        nodes = scope['r'] if q != 4 else scope['xi']
        n = len(nodes)
        initial = np.asarray(initial)
        trial = np.linspace(28, 45, n)
        moisture = np.linspace(2.0, 0.8, n)
        Ta, Ca = module.environment(1800 if q == 1 else 10800 if q == 2 else 14400)
        expected = RadialFVM(r=nodes) if q == 1 else CoupledRadialFVM(nodes) if q in (2, 3) else ShrinkingFVM(nodes)
        if q == 1:
            pairs = [(rhs(100, trial), expected.heat_rhs(100, trial, float(Ta(100)))),
                     (scope['moisture'](100, moisture), expected.moisture_rhs(100, moisture, float(Ca(100))))]
        elif q in (2, 3):
            y = np.r_[trial, moisture]
            pairs = [(rhs(100, y), expected.rhs(100, y, float(Ta(100)), float(Ca(100))))]
        else:
            y = np.r_[trial, moisture]
            pairs = [(rhs(100, y), expected.rhs(y, float(scope['radius'](100)), float(Ta(100)), float(Ca(100))))]
        for a, b in pairs:
            np.testing.assert_allclose(a, b, rtol=1e-12, atol=1e-9)
        record['core_rhs_matches_original'] = True
        small = {k: v for k, v in options.items() if k not in ('t_eval', 'dense_output', 'events')}
        sol = original_integrate(rhs, (0, 1), initial, t_eval=[1.0], **small)
        if not np.isfinite(sol.y).all():
            raise AssertionError('Nonfinite short solution')
        if q == 1:
            mopts = dict(rtol=1e-10, atol=1e-12, max_step=.5,
                         jac_sparsity=expected.moisture_jac_sparsity(), t_eval=[1.0])
            water = original_integrate(scope['moisture'], (0, 1), np.full(n, 2.55), **mopts)
            assert np.isfinite(water.y).all()
        record['one_second_actual_integration'] = True
        if q in (3, 4):
            with np.load(ROOT / 'results' / f'q{q}_solution.npz') as z:
                if q == 3:
                    start, y0 = float(z['t_star']), z['y_star'].copy()
                    end, target = float(z['t_rep']), z['y_end'].copy()
                    tail_rhs = rhs
                else:
                    start = float(z['times_s'][-2])
                    end = float(z['times_s'][-1])
                    y0, target = z['Y'][-2].copy(), z['report_state'].copy()
                    tail_rhs = lambda t, y: scope['rhs'](t, y, True)
                tail = original_integrate(tail_rhs, (start, end), y0, rtol=1e-10,
                    atol=np.r_[np.full(n, 1e-10), np.full(n, 1e-12)], max_step=1.,
                    jac_sparsity=module.coupled_sparsity(n))
                error = float(np.max(abs(tail.y[:, -1]-target)))
                assert error < 2e-5 and float(np.max(tail.y[n:, -1])) < .15
                record['near_finish_max_difference'] = error
        raise StopAfterCheck

    module.integrate = intercept
    try:
        module.main()
    except StopAfterCheck:
        pass
    module.OUT = TMP / f'Q{q}'
    with np.load(ROOT / 'results' / f'q{q}_solution.npz') as z:
        t = z['excel_times'] if q == 3 else z['times_s'][1:] if q == 4 else z['times']
        ids = [0, len(t)//2, len(t)-1]
        fields = [z['T_out'][ids], z['C_out'][ids]] if q in (1, 2) else [z['C_out'][ids]] if q == 3 else [z['C_physical'][1:][ids]]
        module.save_excel(q, t[ids], fields)
        wb = load_workbook(module.OUT / f'result{q}.xlsx', read_only=True, data_only=True)
        for ws, field in zip(wb, fields):
            values = np.array([[np.nan if v is None else v for v in row[1:]] for row in list(ws.values)[1:]])
            np.testing.assert_allclose(values, field, rtol=0, atol=1e-12, equal_nan=True)
        wb.close()
    record['three_row_excel_roundtrip'] = True
    print(json.dumps(record), flush=True)
    return record


records = [check(q) for q in range(1, 5)]
result = {'scope': 'Syntax/imports; original RHS comparison; 1 second solves; Q3/Q4 near-finish restarts; 3-row Excel exports. Not a full rerun.', 'checks': records, 'pass': True}
(ROOT / 'reports' / 'LEAN_CODE_QUICK_CHECK.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
