"""Plot the Attachment-2 radius trajectory used by Problem 4."""
from __future__ import annotations

import json
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import numpy as np

from problem2 import setup_mpl
from problem4 import CAP, Inputs
from utils import FIGURES_DIR, ROOT


def main():
    inputs = Inputs()
    t_s = np.linspace(0.0, CAP, 2001)
    plt = setup_mpl()
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(t_s / 3600.0, inputs.radius(t_s) * 100.0, color="C0", lw=1.2, label="PCHIP插值")
    ax.scatter(inputs.rt / 3600.0, inputs.rv * 100.0, s=12, color="C0", zorder=3, label="附件2观测")
    ax.set_xlabel("时间 $t$ (h)")
    ax.set_ylabel("药材半径 $R(t)$ (cm)")
    ax.set_xlim(0, 72)
    ax.set_ylim(1.12, 2.08)
    ax.legend(frameon=False)
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    paper_fig = ROOT / "paper" / "guosai2026" / "figures"
    paper_fig.mkdir(parents=True, exist_ok=True)
    for folder in (FIGURES_DIR, paper_fig):
        fig.savefig(folder / "q4_R_history.pdf")
        fig.savefig(folder / "q4_R_history.png", dpi=160)
    plt.close(fig)
    summary = {
        "n_obs": int(inputs.rt.size),
        "R0_cm": float(inputs.rv[0] * 100.0),
        "R6_cm": float(inputs.radius(6 * 3600.0) * 100.0),
        "R12_cm": float(inputs.radius(12 * 3600.0) * 100.0),
        "R24_cm": float(inputs.radius(24 * 3600.0) * 100.0),
        "R48_cm": float(inputs.radius(48 * 3600.0) * 100.0),
        "R72_cm": float(inputs.rv[-1] * 100.0),
        "node_error_m": inputs.audit["radius_node_error_m"],
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
