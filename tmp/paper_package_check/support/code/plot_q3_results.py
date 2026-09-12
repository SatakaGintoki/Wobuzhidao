"""Redraw Q3 profiles and the event window using validated saved states only."""
import hashlib
import json
from pathlib import Path

import numpy as np

from problem3 import setup_mpl
from q3_closeout import require_q3_delivery
from utils import ROOT, RESULTS_DIR, FIGURES_DIR


def main():
    out = RESULTS_DIR / 'diagnostics/q3_delivery'
    out.mkdir(parents=True, exist_ok=True)
    validation = json.loads((RESULTS_DIR / 'q3_validation.json').read_text(encoding='utf-8'))
    require_q3_delivery(validation, out / 'pre_plot.json')
    z = np.load(RESULTS_DIR / 'q3_solution.npz')
    n = int(z['n_nodes'])
    plt = setup_mpl()
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    for hour in z['table_hours']:
        if abs(hour * 3600 - float(z['t_rep'])) < 1e-7:
            state = z['y_end']
        else:
            indices = np.flatnonzero(abs(z['times'] - hour * 3600) < 1e-7)
            if len(indices) != 1:
                raise RuntimeError('profile time missing from saved states')
            state = z['Y'][indices[0]]
        ax.plot(z['r'] * 100, state[n:], lw=1.2, label=fr'$t={hour:g}\,\mathrm{{h}}$')
    ax.set_xlabel('\u534a\u5f84 $r$ (cm)')
    ax.set_ylabel('\u5e72\u57fa\u542b\u6c34\u7387 $C$ (kg/kg)')
    ax.set_xlim(0, 2)
    ax.legend(frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(.5, 1.01))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'q3_C_profiles.pdf')
    plt.close(fig)

    critical, report = float(z['t_star']), float(z['t_rep'])
    mask = z['times'] >= critical - 90
    times = np.r_[z['times'][mask], critical, report]
    maxima = np.r_[z['M_hist'][mask], np.max(z['y_star'][n:]), np.max(z['y_end'][n:])]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.axhline(0, color='.4', lw=1, ls='--', label='$C=0.15$')
    ax.plot(times - critical, (maxima - .15) * 1e6, marker='o', ms=3, lw=1.2,
            label=r'$\max_i C_i-0.15$')
    ax.axvline(0, color='.2', lw=.9, ls=':', label=fr'$t_*={critical/3600:.6f}\,\mathrm{{h}}$')
    ax.axvline(report - critical, color='#c44242', lw=.9, ls='-.',
               label=fr'$t_{{\mathrm{{rep}}}}={report/3600:.6f}\,\mathrm{{h}}$')
    ax.set_xlabel('\u76f8\u5bf9\u4e34\u754c\u65f6\u523b $t-t_*$ (s)')
    ax.set_ylabel(r'$(\max_i C_i-0.15)\, /\, 10^{-6}$ (kg/kg)')
    ax.set_xlim(-90, 7)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / 'q3_event_zoom.pdf')
    plt.close(fig)
    artifacts = ['code/plot_q3_results.py', 'results/q3_solution.npz',
                 'results/q3_validation.json', 'figures/q3_C_profiles.pdf', 'figures/q3_event_zoom.pdf']
    provenance = {'result_version': validation['result_version'],
                  'event_times_s': times.tolist(), 'event_maxima': maxima.tolist(),
                  'event_lines': 'linear guides connecting saved states; no new PDE solve',
                  'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in artifacts}}
    (out / 'figure_provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print('Q3 profiles and event window redrawn from saved states')


if __name__ == '__main__':
    main()
