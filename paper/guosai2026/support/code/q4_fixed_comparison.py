"""Appendix-4 fixed-radius control. Existing production results are read-only.

Run --level 8, --level 16, --level 8 --tight, then --summarize.
The fixed control requires no extrapolation of the measured shrinking radius.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import time
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import solve_ivp
from problem4 import Inputs, ShrinkingFVM, properties, SWITCH, THRESHOLD
from radial_fvm import graded_radial_nodes, harmonic_mean
from utils import RESULTS_DIR, R, T0, C0, H, HM

OUT = RESULTS_DIR / 'q4_fixed_comparison'


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def run(level, tight):
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = Inputs()
    fvm = ShrinkingFVM(graded_radial_nodes(level)/R)
    n = fvm.n
    label = f'G{level}' + ('_tight' if tight else '')
    rtol = 1e-9 if tight else 1e-8
    atol = np.r_[np.full(n, 1e-9 if tight else 1e-8), np.full(n, 1e-11 if tight else 1e-10)]
    y = np.r_[np.full(n, T0), np.full(n, C0)]
    times, states = [np.array([0.])], [y[None, :]]
    event = lambda t, z: float(z[n:].max()-THRESHOLD)
    event.direction, event.terminal = -1., False
    breaks = np.unique(np.r_[0., SWITCH, np.arange(21600., 864000.+1., 21600.)])
    gx, gw = leggauss(4)
    loss, mass_error, heat_error = 0., 0., 0.
    bounds = [T0, T0, C0, C0]
    segments = []
    critical = None
    started = time.perf_counter()
    for a, b in zip(breaks[:-1], breaks[1:]):
        late = a >= SWITCH
        def rhs(t, z):
            ta, ca = inputs.environment(t, late=late)
            return fvm.rhs(z, R, ta, ca)
        step = (5. if tight else 10.) if not late else (30. if tight else 60.)
        sol = solve_ivp(rhs, (a, b), y, method='BDF', rtol=rtol, atol=atol,
                        max_step=step, jac_sparsity=fvm.sparsity(), dense_output=True, events=event)
        if not sol.success:
            raise RuntimeError(sol.message)
        ts = np.arange(a+60., b+.1, 60.)
        yy = sol.sol(ts).T
        times.append(ts); states.append(yy)
        for start in range(0, len(sol.t)-1, 128):
            aa, bb = sol.t[start:-1][:128], sol.t[start+1:][:128]
            qq = ((aa+bb)[:,None]/2 + (bb-aa)[:,None]/2*gx).ravel()
            surf = sol.sol(qq)[-1]
            ca = np.full_like(qq, .05) if late else inputs.Ca(qq)
            flux = 2*HM/R*(surf-ca)
            loss += float(np.sum(flux.reshape(-1,4)*gw*(bb-aa)[:,None]/2))
        y = sol.y[:,-1]
        mass_error = max(mass_error, abs(float(2*np.dot(fvm.w,y[n:])-C0+loss)))
        bounds = [min(bounds[0],float(sol.y[:n].min())), max(bounds[1],float(sol.y[:n].max())),
                  min(bounds[2],float(sol.y[n:].min())), max(bounds[3],float(sol.y[n:].max()))]
        for tq in (a,(a+b)/2,b):
            z = sol.sol(tq); dz = rhs(tq,z); B,_,_ = properties(z[n:],z[:n])
            ta,_ = inputs.environment(tq,late=late)
            heat_error = max(heat_error,abs(float(np.dot(fvm.w*B,dz[:n])+H/R*(z[n-1]-ta))))
        segments.append({'start_s':float(a),'end_s':float(b),'steps':len(sol.t)-1,'mass_abs':mass_error})
        print(f'{label}: {b/3600:.0f} h, maxC={y[n:].max():.8f}, wall={time.perf_counter()-started:.1f}s', flush=True)
        if len(sol.t_events[0]):
            critical = float(sol.t_events[0][0])
            event_state = sol.y_events[0][0]
            break
    if critical is None:
        raise RuntimeError('Fixed control has not crossed threshold by the 240 h numerical cap')
    tt, YY = np.concatenate(times), np.vstack(states)
    if not np.all(np.isfinite(YY)):
        raise RuntimeError('nonfinite state')
    # Independent physical-ring assembly verifies fixed-radius transformation.
    rp = R*fvm.xi; rf = (rp[:-1]+rp[1:])/2
    vol = np.diff(np.r_[0.,rf,R]**2)/2
    z = np.r_[35.+10*fvm.xi**2, 1.7-1.2*fvm.xi**2]
    B,k,D = properties(z[n:],z[:n])
    ft = np.r_[0.,-rf*harmonic_mean(k[:-1],k[1:])*np.diff(z[:n])/np.diff(rp),R*H*(z[n-1]-50.)]
    fc = np.r_[0.,-rf*harmonic_mean(D[:-1],D[1:])*np.diff(z[n:])/np.diff(rp),R*HM*(z[-1]-.05)]
    ref = np.r_[-np.diff(ft)/(vol*B),-np.diff(fc)/vol]
    operator_error = float(np.max(abs(ref-fvm.rhs(z,R,50.,.05))))
    meta = {'label':label,'nodes':n,'rtol':rtol,'atol_T':float(atol[0]),'atol_C':float(atol[n]),
            'critical_s':critical,'critical_h':critical/3600,'radius_m':R,'properties':'Appendix 4',
            'input_audit':inputs.audit,'mass_relative_error':mass_error/C0,'heat_equation_residual':heat_error,
            'physical_operator_error':operator_error,'bounds':bounds,'segments':segments,
            'max_center_gap':float(np.max(YY[:,n:].max(axis=1)-YY[:,n])),
            'wall_s':time.perf_counter()-started,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                             [Path(__file__),Path(__file__).with_name('problem4.py'),Path(__file__).with_name('radial_fvm.py')]}}
    np.savez_compressed(OUT/f'{label}.npz',times_s=tt,Y=YY,xi=fvm.xi,event_state=event_state)
    dump(OUT/f'{label}.json',meta)
    print(json.dumps(meta,ensure_ascii=False),flush=True)


def state_at(data, t):
    times = data['times_s']; i = int(np.searchsorted(times,t,side='right')-1)
    if i < 0 or t > times[-1]:
        raise ValueError('state query outside saved trajectory')
    if abs(times[i]-t)<1e-8:
        return data['Y'][i].copy()
    assert times[i]>=SWITCH
    fvm = ShrinkingFVM(data['xi']); n=fvm.n
    sol = solve_ivp(lambda tt,y:fvm.rhs(y,R,50.,.05),(times[i],t),data['Y'][i],
                    method='BDF',rtol=1e-10,atol=np.r_[np.full(n,1e-10),np.full(n,1e-12)],
                    max_step=1.,jac_sparsity=fvm.sparsity())
    if not sol.success: raise RuntimeError(sol.message)
    return sol.y[:,-1]


def summarize():
    labels = ['G8','G16','G8_tight']
    ds = {k:np.load(OUT/f'{k}.npz') for k in labels}
    ms = {k:json.loads((OUT/f'{k}.json').read_text(encoding='utf-8')) for k in labels}
    a,b,c = (ds[k] for k in labels); n,m = len(a['xi']),len(b['xi'])
    assert np.allclose(a['xi'],b['xi'][::2],rtol=0,atol=1e-14)
    count = min(len(d['times_s']) for d in ds.values())
    assert all(np.array_equal(a['times_s'][:count],d['times_s'][:count]) for d in ds.values())
    space = [float(np.max(abs(a['Y'][:count,:n]-b['Y'][:count,:m:2]))),
             float(np.max(abs(a['Y'][:count,n:]-b['Y'][:count,m::2])))]
    temporal = [float(np.max(abs(a['Y'][:count,:n]-c['Y'][:count,:n]))),
                float(np.max(abs(a['Y'][:count,n:]-c['Y'][:count,n:])))]
    critical = ms['G8']['critical_s']
    crit_max = {k:float(state_at(d,critical)[len(d['xi']):].max()) for k,d in ds.items()}
    margin = 2*max(abs(crit_max['G8']-crit_max[k]) for k in labels[1:])+1e-8
    report = math.ceil((max(v['critical_s'] for v in ms.values())+2.)/.36)*.36
    for _ in range(120):
        report_states = {k:state_at(d,report) for k,d in ds.items()}
        maxima = {k:float(report_states[k][len(ds[k]['xi']):].max()) for k in labels}
        if max(maxima.values())<THRESHOLD and maxima['G8']+margin<THRESHOLD: break
        report += .36
    spatial_event = abs(ms['G8']['critical_s']-ms['G16']['critical_s'])
    temporal_event = abs(ms['G8']['critical_s']-ms['G8_tight']['critical_s'])
    shrink = json.loads((RESULTS_DIR/'q4_validation.json').read_text(encoding='utf-8'))
    checks = {'spatial_T_2e-5':space[0]<2e-5,'spatial_C_2e-5':space[1]<2e-5,
              'temporal_T_2e-5':temporal[0]<2e-5,'temporal_C_2e-5':temporal[1]<2e-5,
              'spatial_event_1s':spatial_event<1.,'temporal_event_1s':temporal_event<1.,
              'mass_1e-6':all(v['mass_relative_error']<1e-6 for v in ms.values()),
              'heat_equation_1e-6':all(v['heat_equation_residual']<1e-6 for v in ms.values()),
              'fixed_operator_1e-8':all(v['physical_operator_error']<1e-8 for v in ms.values()),
              'physical_C_bounds':all(v['bounds'][2]>=0 and v['bounds'][3]<=C0+1e-8 for v in ms.values()),
              'center_is_maximum':all(v['max_center_gap']<1e-10 for v in ms.values()),
              'strict_report':max(maxima.values())<THRESHOLD and maxima['G8']+margin<THRESHOLD,
              'shrink_validated':shrink['pass'],
              'same_inputs':all(v['input_audit']['source_sha256']==shrink['runs']['G8']['input_audit']['source_sha256'] for v in ms.values())}
    result = {'version':'q4-fixed-comparison-v1','fixed_critical_h':critical/3600,
              'fixed_report_h':report/3600,'fixed_report_s':report,'fixed_report_maxima':maxima,
              'fixed_empirical_margin':margin,'fixed_spatial_T_C':space,'fixed_temporal_T_C':temporal,
              'fixed_event_space_s':spatial_event,'fixed_event_time_s':temporal_event,
              'shrink_critical_h':shrink['critical_h'],'shrink_report_h':shrink['report_h'],
              'saving_critical_h':(critical-shrink['critical_s'])/3600,
              'saving_report_h':report/3600-shrink['report_h'],
              'saving_percent':100*(report-shrink['report_s'])/report,
              'checks':checks,'pass':all(checks.values()),'runs':ms,
              'scope':'Controlled model comparison under the same Appendix-4 properties and environment; not experimental causal evidence.'}
    dump(OUT/'comparison.json',result)
    if not result['pass']: raise RuntimeError(checks)
    mask=a['times_s']<report
    tt=np.r_[a['times_s'][mask],report]
    yy=np.vstack([a['Y'][mask],report_states['G8']])
    np.savez_compressed(OUT/'fixed_solution.npz',times_s=tt,xi=a['xi'],Y=yy)
    sd=np.load(RESULTS_DIR/'q4_solution.npz'); sn=len(sd['xi'])
    for name, ts, cc in [('fixed',tt,yy[:,n]),('shrink',sd['times_s'],sd['Y'][:,sn])]:
        with (OUT/f'{name}_center.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(['time_s','center_C_kg_per_kg']);w.writerows(zip(ts,cc))
    print(json.dumps({k:v for k,v in result.items() if k!='runs'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--level',type=int,default=8)
    p.add_argument('--tight',action='store_true');p.add_argument('--summarize',action='store_true')
    args=p.parse_args()
    summarize() if args.summarize else run(args.level,args.tight)
