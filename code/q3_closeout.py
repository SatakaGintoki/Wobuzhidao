"""Q3 closeout: matched-time convergence, continuous balances and gated delivery."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from delivery import make_gate,require_delivery
from q3_balance import audit_segment,combine
from utils import RESULTS_DIR,REPORTS_DIR,FIGURES_DIR,ROOT

DIAG=RESULTS_DIR/'diagnostics/q3_closeout'
NODE=Path('C:/Users/chens/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
BUILDER=ROOT/'tmp/q3_export/build.mjs'
REQUIRED_CHECKS = frozenset({
    'event_found', 'finite', 'strict_below_all_verified_grids',
    'strict_below_with_empirical_margin', 'moisture_bounds', 'temperature_bounds',
    'moisture_balance_1e-6', 'heat_balance_1e-6', 'quadrature_convergence_1e-7',
    'space_event_60s', 'time_event_60s', 'space_full_fields_2e-5',
    'time_full_fields_2e-5', 'table_four_decimals', 'q2_overlap',
})


def require_q3_delivery(validation, diagnostic_path):
    require_delivery(validation, diagnostic_path)
    if validation.get('result_version') != 'q3-closeout-v1' or not REQUIRED_CHECKS.issubset(validation['delivery_gate']['checks']):
        raise RuntimeError('Delivery blocked: missing Q3 checks or wrong result version')


def export_workbook(path,C_out,times,validation):
    require_q3_delivery(validation,DIAG/'pre_export.json')
    data={'sheet':'水分浓度','headers':['时间\\到药材中心的距离']+[round(.1*j,1) for j in range(21)],
          'rows':[[float(t)]+list(map(float,row)) for t,row in zip(times,C_out)],'path':str(path.resolve())}
    (DIAG/'excel_payload.json').write_text(json.dumps(data,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    subprocess.run([str(NODE),str(BUILDER)],cwd=ROOT,check=True)


def save_case(case):
    f=case['fvm'];n=f.n_nodes
    np.savez_compressed(DIAG/(case['tag']+'.npz'),r=f.r,times=case['times'],Y=case['Y'],
        y_star=case['y_star'],t_star=case['t_star'])
    info={k:case[k] for k in ('tag','level','n_nodes','rtol','atol_T','atol_C','max_step_early','max_step_late','elapsed_s','event')}
    (DIAG/(case['tag']+'.json')).write_text(json.dumps(info,indent=2),encoding='utf-8')


def compare_fields(a,b):
    """Shared physical nodes and exactly matching stored times."""
    times,ia,ib=np.intersect1d(a['times'],b['times'],return_indices=True)
    ra,rb=a['fvm'].r,b['fvm'].r
    j=np.searchsorted(rb,ra)
    if np.max(abs(rb[j]-ra))>1e-13:
        raise RuntimeError('spatial meshes are not nested')
    na,nb=a['n_nodes'],b['n_nodes']
    # Batch to bound temporary array sizes for fine meshes.
    maxT=maxC=0.
    for start in range(0,len(times),128):
        ai,bi=ia[start:start+128],ib[start:start+128]
        maxT=max(maxT,float(np.max(abs(a['Y'][ai,:na]-b['Y'][bi,:nb][:,j]))))
        maxC=max(maxC,float(np.max(abs(a['Y'][ai,na:]-b['Y'][bi,nb:][:,j]))))
    return {'matched_times':len(times),'max_T':maxT,'max_C':maxC}


def main(argv=None):
    from problem3 import (load_q3_inputs,run_case,run_probe,RTOL,ATOL_T,ATOL_C,MAX_STEP_EARLY,
        MAX_STEP_LATE,find_strict_report,build_output_tables,physical_bounds,overlap_q2,
        write_result3_xlsx,write_table5_csv,plot_figures,setup_mpl,conservation_heat,conservation_moisture)
    parser=argparse.ArgumentParser();parser.add_argument('--probe-only',action='store_true')
    parser.add_argument('--no-xlsx',action='store_true',help='Save gated numerical evidence; export separately later.')
    args=parser.parse_args(argv)
    DIAG.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    Ta,Ca,knots=load_q3_inputs()
    if args.probe_only:
        print(json.dumps(run_probe(Ta,Ca)));return
    cases={}
    for level in (4,8,16):
        cases[level]=run_case(level,Ta,Ca,72*3600.,RTOL,ATOL_T,ATOL_C,MAX_STEP_EARLY,MAX_STEP_LATE,
                             tag=f'G{level}',audit_balances=(level==8))
        save_case(cases[level])
    pub,ref=cases[8],cases[16]
    tight=run_case(8,Ta,Ca,72*3600.,RTOL/5,ATOL_T/5,ATOL_C/5,MAX_STEP_EARLY/2,MAX_STEP_LATE/2,tag='G8t')
    save_case(tight)
    space=compare_fields(pub,ref);temporal=compare_fields(pub,tight)
    coarse_space=compare_fields(cases[4],pub)
    critical=pub['t_star']
    same={name:float(case['eval_M'](critical)) for name,case in [('G4',cases[4]),('G8',pub),('G16',ref),('G8t',tight)]}
    # The maximum differences are measured at the same physical time.
    err=max(abs(same['G8']-same['G16']),abs(same['G8']-same['G8t']))
    margin=2*err+1e-8
    zero_report=find_strict_report(pub['eval_M'],critical,critical+3500,margin=0.)
    report=find_strict_report(pub['eval_M'],critical,critical+3500,margin=margin)
    t_rep=report['t_hour4_s']  # Upward four-decimal-hour rounding retains the safety margin.
    report_M={name:float(case['eval_M'](t_rep)) for name,case in [('G8',pub),('G16',ref),('G8t',tight)]}
    tables=build_output_tables(pub,t_rep);other=build_output_tables(ref,t_rep)
    tight_tables=build_output_tables(tight,t_rep)
    table_changed=int(np.count_nonzero(np.round(tables['C_table'],4)!=np.round(other['C_table'],4)))
    table_time_changed=int(np.count_nonzero(np.round(tables['C_table'],4)!=np.round(tight_tables['C_table'],4)))
    output_space=float(np.max(abs(tables['C_excel']-other['C_excel'])))
    tail=audit_segment(pub['fvm'],pub['sol_after'],Ta,Ca,t_end=t_rep)
    balances=combine(pub['balance_parts']+[tail])
    checked_states = np.vstack([pub['Y'], pub['y_star'], pub['eval_y'](t_rep)])
    bounds=physical_bounds(dict(pub,Y=checked_states),Ta,Ca);overlap=overlap_q2(pub)
    overlap_ok=overlap.get('available',False) and all(c.get('matched',False) and c['T_max_abs']<2e-5 and c['C_max_abs']<2e-5 for c in overlap['checks'].values())
    event_space=abs(pub['t_star']-ref['t_star']);event_time=abs(pub['t_star']-tight['t_star'])
    gates={
        'event_found':abs(pub['event']['g_star'])<1e-8,
        'finite':bool(np.isfinite(checked_states).all() and np.isfinite(tables['C_excel']).all()
                      and np.isfinite(tables['T_excel']).all()),
        'strict_below_all_verified_grids':all(v<.15 for v in report_M.values()),
        'strict_below_with_empirical_margin':report_M['G8']+margin<.15,
        'moisture_bounds':bounds['C_bounds_ok'],'temperature_bounds':bounds['T_bounds_ok'],
        'moisture_balance_1e-6':balances['moisture']['relative_residual']<1e-6,
        'heat_balance_1e-6':balances['heat']['relative_residual']<1e-6,
        'quadrature_convergence_1e-7':max(balances['quadrature_relative_difference'].values())<1e-7,
        'space_event_60s':event_space<=60.,'time_event_60s':event_time<=60.,
        'space_full_fields_2e-5':max(space['max_T'],space['max_C'],output_space)<2e-5,
        'time_full_fields_2e-5':max(temporal['max_T'],temporal['max_C'])<2e-5,
        'table_four_decimals':table_changed==0 and table_time_changed==0,
        'q2_overlap':overlap_ok,
    }
    v={'result_version':'q3-closeout-v1','model':'q3-model-v1','result_status':'PUBLISHED',
       'published_mesh':'G8','published_n_nodes':pub['n_nodes'],'rtol':RTOL,'atol_T':ATOL_T,'atol_C':ATOL_C,
       'max_step_early':MAX_STEP_EARLY,'max_step_late':MAX_STEP_LATE,
       't_star_s':critical,'t_star_h':critical/3600.,'t_rep_s':t_rep,'t_rep_h':t_rep/3600.,
       'M_star':pub['event']['M_star'],'M_rep':report_M['G8'],'report_maxima':report_M,
       'matched_critical_time_maxima':same,'moisture_margin':margin,'margin_type':'empirical, not a rigorous PDE error bound',
       'report_zero_margin':zero_report,'report_with_margin':report,
       'space_fields':space,'time_fields':temporal,'coarse_space_fields':coarse_space,'output_space_max_C':output_space,
       'dt_space_s':event_space,'dt_time_s':event_time,
       'conservation_C':balances['moisture'],'conservation_T':balances['heat'],'continuous_balances':balances,
       'old_sampled_conservation_C':conservation_moisture(pub['fvm'],pub['times'],pub['Y'],Ca),
       'old_sampled_conservation_T':conservation_heat(pub['fvm'],pub['times'],pub['Y'],Ta),
       'physical_bounds':bounds,'q2_overlap':overlap,'table_four_decimal_changes':table_changed,
       'events':{f'G{k}':c['event'] for k,c in cases.items()}|{'G8t':tight['event']},
       'delivery_gate':make_gate(gates),'table_hours':tables['table_hours'].tolist(),
       'excel_nrows':len(tables['excel_times']),'paper_table_C':tables['paper_C'],
       'max_location_cm':pub['event']['rmax_star_cm'],'center_is_max_at_event':pub['event']['center_is_max'],
       'n_radial_increases':pub['monitor']['n_radial_increases'],
       'elapsed_s':time.perf_counter()-start,'python':sys.version,
       'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
           ['code/problem3.py','code/q3_balance.py','code/q3_closeout.py','code/delivery.py',
            'tmp/q3_export/build.mjs','tmp/q3_export/gate.mjs',
            'code/radial_coupled.py','code/appendix3.py','data/附件/附件1.xlsx']}}
    print('CLOSEOUT',json.dumps({k:v[k] for k in ('t_star_h','t_rep_h','M_rep','dt_space_s','dt_time_s','conservation_C','conservation_T','delivery_gate')},ensure_ascii=False),flush=True)
    publish_results(pub, tables, v, Ta, no_xlsx=args.no_xlsx)
    print('Q3 CLOSEOUT NUMERICAL PASS',flush=True)


def publish_results(pub, tables, v, Ta, *, no_xlsx=False):
    from problem3 import write_result3_xlsx, write_table5_csv, plot_figures, setup_mpl
    require_q3_delivery(v,DIAG/'latest.json')
    t_rep, critical = v['t_rep_s'], v['t_star_s']
    # Commit production outputs only after every required numerical check passed.
    yend=pub['eval_y'](t_rep)
    np.savez_compressed(RESULTS_DIR/'q3_solution.npz',mesh_level=8,n_nodes=pub['n_nodes'],r=pub['fvm'].r,
        times=pub['times'],Y=pub['Y'],excel_times=tables['excel_times'],T_out=tables['T_excel'],C_out=tables['C_excel'],
        table_hours=tables['table_hours'],C_table=tables['C_table'],t_star=critical,t_rep=t_rep,
        y_star=pub['y_star'],y_end=yend,M_hist=pub['monitor']['M'],rmax_m=pub['monitor']['rmax_m'],
        C_center=pub['monitor']['C_center'],C_surface=pub['monitor']['C_surface'],
        T_center=pub['monitor']['T_center'],T_surface=pub['monitor']['T_surface'],
        rtol=v['rtol'],atol_T=v['atol_T'],atol_C=v['atol_C'],max_step_early=v['max_step_early'],max_step_late=v['max_step_late'],
        interpolation=np.array('pchip_then_constant'))
    (RESULTS_DIR/'q3_validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    write_table5_csv(RESULTS_DIR/'q3_table_moisture.csv',tables['table_hours'],tables['C_table'])
    if not no_xlsx:
        write_result3_xlsx(RESULTS_DIR/'result3.xlsx',tables['C_excel'],tables['excel_times'],validation=v)
    plot_figures(setup_mpl(),pub,tables,t_rep,Ta)


if __name__=='__main__':
    main()
