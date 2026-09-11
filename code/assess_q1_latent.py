"""Post-process the existing no-latent baseline; does not solve a new model."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'results/q1_solution.npz'
z = np.load(source)
r = z['r']
assert np.allclose(np.diff(r), r[1]-r[0])
dr = r[1]-r[0]
R, L, rho, cp, C0, T0, Lv = .02, .25, 820., 2600., 2.55, 28., 2.4e6
faces_left = np.maximum(0., r-dr/2)
faces_right = np.minimum(R, r+dr/2)
weights = (faces_right**2-faces_left**2)/2
assert abs(weights.sum()-R**2/2)<1e-14
vol = np.pi*R**2*L
md = rho*vol/(1+C0)
mean_c = z['C_full'] @ weights / weights.sum()
mean_t = z['T_full'] @ weights / weights.sum()
mass_lost = md*(C0-mean_c)
latent = Lv*mass_lost
sensible = rho*cp*vol*(mean_t-T0)
from utils import load_oven_table
ot, ta, ca = load_oven_table()
times = z['times']
surface_j = rho/(1+C0)*8e-7*(z['C_full'][:, -1]-np.interp(times, ot, ca))
q_latent = Lv*surface_j
q_convection = 25*(np.interp(times, ot, ta)-z['T_full'][:, -1])
rows=[]
for t in [100,300,600,900,1200,1500,1800]:
    idx=int(np.flatnonzero(times==t)[0])
    rows.append(dict(time_s=t, mean_C_kg_kg=float(mean_c[idx]),
                     mean_T_C=float(mean_t[idx]), mass_lost_kg=float(mass_lost[idx]),
                     implied_latent_J=float(latent[idx]), baseline_sensible_gain_J=float(sensible[idx]),
                     latent_over_sensible=float(latent[idx]/sensible[idx]),
                     implied_latent_flux_W_m2=float(q_latent[idx]),
                     baseline_convective_flux_W_m2=float(q_convection[idx])))
report=dict(purpose='Energy scale audit of existing no-latent baseline, not a revised PDE solution',
            source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            source_N=int(z['N']), assumptions=dict(initial_wet_density_kg_m3=rho,
            constant_reference_dry_mass_kg=md, free_water_Lv_J_kg=Lv,
            Lv_reference='NISTIR 5078 Table 1; 40 C delta h 2406.0 kJ/kg; rounded 2.4 MJ/kg for screening',
            warning='Dry mass assumes 820 kg/m3 is initial wet bulk density. Existing effective moisture boundary is retained only for this consistency audit.'),
            rows=rows,
            conclusion='Under these assumptions, the implied latent load is not a small correction. These are not corrected temperatures or experimental validation.')
out=ROOT/'reports/Q1_LATENT_ENERGY_AUDIT.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
