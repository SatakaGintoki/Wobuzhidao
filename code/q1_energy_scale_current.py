"""Read-only energy-scale screening of the current Q1 solution."""
from pathlib import Path
import hashlib
import json
import numpy as np
from utils import RESULTS_DIR, R, C0, T0

source = RESULTS_DIR / 'q1_solution.npz'
with np.load(source) as data:
    r = data['r']
    weights = np.diff(np.r_[0., (r[:-1]+r[1:])/2, R]**2)/R**2
    mean_C = float(weights @ data['C_full'][-1])
    mean_T = float(weights @ data['T_full'][-1])
    assert float(data['times'][-1]) == 1800
volume = np.pi*R**2*.25
dry_mass = 820*volume/(1+C0)
loss = dry_mass*(C0-mean_C)
latent = 2.4e6*loss
sensible = 820*volume*2600*(mean_T-T0)
record = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'nodes': len(r), 'time_s': 1800, 'mean_C': mean_C, 'mean_T_C': mean_T,
          'assumptions': ['820 kg/m3 interpreted as initial wet bulk density for screening only',
                          'free-water latent heat scale assumed 2.4 MJ/kg',
                          'all predicted moisture loss counted as evaporation'],
          'mass_lost_g': loss*1000, 'latent_kJ': latent/1000,
          'sensible_kJ': sensible/1000, 'ratio': latent/sensible,
          'scope': 'Energy scale only; not corrected temperature, time, or error bound'}
out = RESULTS_DIR / 'diagnostics' / 'q1_energy_scale_current.json'
out.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
