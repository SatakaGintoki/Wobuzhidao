"""Bounded Q3 mesh diagnosis; never overwrite production results."""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from scipy.integrate import solve_ivp, quad
import problem3 as p
from radial_coupled import CoupledRadialFVM
from radial_fvm import graded_radial_nodes, harmonic_mean
from utils import R, HM

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/diagnostics/q3_time_discrepancy'
OUT.mkdir(parents=True,exist_ok=True)
Ta,Ca,_=p.load_q3_inputs()
sources=['code/problem3.py','code/radial_coupled.py','code/appendix3.py','results/q3_validation.json','results/q3_solution.npz']
hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
report={'purpose':'isolate mesh effects at identical time tolerances; no model or production output edits','source_sha256':hashes,'runs':[]}

for name,r in [('uniform41',np.linspace(0,R,41)),('uniform81',np.linspace(0,R,81)),('uniform161',np.linspace(0,R,161)),('gradedG4',graded_radial_nodes(4))]:
    f=CoupledRadialFVM(r);n=f.n_nodes;start=time.perf_counter()
    kwargs={'method':'BDF','rtol':1e-9,'atol':p.atol_vector(n,1e-8,1e-10),'jac_sparsity':f.jac_sparsity()}
    rhs=lambda t,y:f.rhs(t,y,float(Ta(t)),float(Ca(t)))
    initial=f.pack(np.full(n,p.T0),np.full(n,p.C0))
    early=solve_ivp(rhs,(0,p.T_SWITCH),initial,max_step=2.,t_eval=[p.T_SWITCH],**kwargs)
    assert early.success,early.message
    late=solve_ivp(rhs,(p.T_SWITCH,12*86400.),early.y[:,-1],max_step=60.,events=p.max_moisture_event(n),**kwargs)
    assert late.success and len(late.t_events[0]),late.message
    event=float(late.t_events[0][0]);y=late.y_events[0][0]
    result={'mesh':name,'nodes':n,'surface_dr_m':float(r[-1]-r[-2]),'rtol':1e-9,'max_step_early_s':2.,'max_step_late_s':60.,'t_h':event/3600.,'t_days':event/86400.,'C_surface':float(y[-1]),'C_center':float(y[n]),'elapsed_s':time.perf_counter()-start}
    report['runs'].append(result)
    print(json.dumps(result),flush=True)
    (OUT/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

z=np.load(ROOT/'results/q3_solution.npz');r=z['r'];n=int(z['n_nodes']);C=z['y_star'][n:];T=z['y_star'][:n]
diagnostics=[]
for dr in (.0005,.00025,.000125,float(r[-1]-r[-2])):
    ci=float(np.interp(R-dr,r,C));cs=float(C[-1]);tc=float(T[-1]);ds=float(p.moisture_diffusivity_q2(cs,tc));di=float(p.moisture_diffusivity_q2(ci,tc))
    dh=float(harmonic_mean(np.array([di]),np.array([ds]))[0])
    # At constant temperature, integral D(C)dC / deltaC is the planar
    # Kirchhoff effective coefficient for an interval. Used only to diagnose
    # nonlinear face interpolation, not as an alternative physical model.
    dk=float(quad(lambda c:p.moisture_diffusivity_q2(c,tc),cs,ci,epsabs=1e-20,epsrel=1e-10)[0]/(ci-cs))
    diagnostics.append({'dr_m':dr,'C_inner_from_fine_solution':ci,'C_surface':cs,'D_inner':di,'D_surface':ds,'D_harmonic':dh,'D_integral_mean':dk,'harmonic_over_integral':dh/dk})
report['face_diagnostics_on_fine_event_profile']=diagnostics
report['surface_D_over_hm_m']=float(p.moisture_diffusivity_q2(C[-1],T[-1])/HM)
report['production_files_unchanged']=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in hashes.items())
assert report['production_files_unchanged']
(OUT/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'face_diagnostics':diagnostics,'surface_D_over_hm_m':report['surface_D_over_hm_m'],'production_files_unchanged':True}),flush=True)
