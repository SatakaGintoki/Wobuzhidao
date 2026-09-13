"""Reproduce the approved contour layouts from saved solutions, without solving."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.colors import BoundaryNorm
import numpy as np
from scipy.interpolate import PchipInterpolator


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
RED, BLUE = "#B83F3B", "#4358C5"
MOISTURE = "干基含水率 $C$ (kg/kg)"
BREAKS = np.array([.05, .1, .15, .2, .3, .6, 1, 1.5, 2, 2.55])
LEVELS = np.concatenate([np.linspace(a, b, 5)[:-1]
                         for a, b in zip(BREAKS[:-1], BREAKS[1:])] + [BREAKS[-1:]])
plt.rcParams.update({
    "font.family": "SimSun", "mathtext.fontset": "stix",
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.unicode_minus": False,
    "pdf.fonttype": 42, "axes.linewidth": .65,
    "text.color": "#333333", "axes.labelcolor": "#333333",
})
AUDIT = {"version": "paper-spacetime-v1", "solver_rerun": False, "sources": {},
         "figures": {}, "interpolation": "PCHIP only for Q2 radial display; saved states otherwise"}


def load(relative):
    path = ROOT / relative
    AUDIT["sources"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return np.load(path)


def sampled(n, maximum=950):
    return np.unique(np.r_[np.arange(0, n, max(1, n // maximum)), n - 1])


def save(fig, name, description):
    for suffix in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{suffix}", dpi=240, facecolor="white")
    AUDIT["figures"][name] = {"description": description,
        "pdf_sha256": hashlib.sha256((OUT / f"{name}.pdf").read_bytes()).hexdigest()}
    plt.close(fig)


def axes_labels(ax, hours=True):
    ax.set_xlabel("时间 $t$ (h)" if hours else "时间 $t$ (s)")
    ax.set_ylabel("径向位置 $r$ (cm)")
    ax.tick_params(length=3, width=.6)


def contour_labels(ax, x, y, z, levels, manual=None, red=False):
    contour = ax.contour(x, y, z, levels=levels,
                         colors=RED if red else "#62696F",
                         linewidths=1.25 if red else .55,
                         linestyles="--" if red else "-")
    if manual is None:
        manual = []
        scale = np.array([np.ptp(x), np.ptp(y)])
        for segments in contour.allsegs:
            paths = [s for s in segments if len(s) > 1]
            if not paths:
                continue
            segment = max(paths, key=lambda s: np.linalg.norm(np.diff(s / scale, axis=0), axis=1).sum())
            distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(segment / scale, axis=0), axis=1))]
            manual.append(segment[np.searchsorted(distance, distance[-1] / 2)])
    labels = ax.clabel(contour, inline=True, inline_spacing=3, fontsize=8,
                       fmt=lambda v: f"{v:g}", manual=manual)
    for label in labels:
        label.set_path_effects([path_effects.withStroke(linewidth=1.1, foreground="white")])
    return contour


def short_fields(q):
    with load(f"results/q{q}_solution.npz") as d:
        ti = sampled(len(d["times"]))
        times = np.r_[0., d["times"][ti]]
        if q == 1:
            ri = sampled(len(d["r"]), 320)
            radius = d["r"][ri] * 100
            temp, water = d["T_full"][ti][:, ri], d["C_full"][ti][:, ri]
        else:
            radius = np.linspace(0, 2, 161)
            temp = PchipInterpolator(d["output_radii_m"] * 100, d["T_out"][ti], axis=1)(radius)
            water = PchipInterpolator(d["output_radii_m"] * 100, d["C_out"][ti], axis=1)(radius)
        temp = np.vstack([np.full(len(radius), 28.), temp])
        water = np.vstack([np.full(len(radius), 2.55), water])
    time = times if q == 1 else times / 3600
    fig = plt.figure(figsize=(6.3, 3.12))
    axs = [fig.add_axes([.08, .19, .29, .71]), fig.add_axes([.585, .19, .29, .71])]
    for k, (ax, field, cmap, limits, lines, title, label) in enumerate(zip(
        axs, [temp, water], ["coolwarm", "YlGnBu"],
        [(28, 37 if q == 1 else 50), (1, 2.55)],
        [np.arange(29, 37) if q == 1 else [30, 34, 38, 42, 46, 48, 49],
         [1.8, 2, 2.2, 2.4, 2.5] if q == 1 else [1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.4, 2.5]],
        ["(a) 温度场", "(b) 含水率场"], ["温度 $T$ (℃)", MOISTURE])):
        # Round-off can put the uniform initial field infinitesimally above 2.55.
        field = np.clip(field, *limits)
        cf = ax.contourf(time, radius, field.T, levels=np.linspace(*limits, 33), cmap=cmap)
        cf.set_edgecolor("face")
        cf.set_linewidth(.1)
        contour_labels(ax, time, radius, field.T, lines)
        cb = fig.colorbar(cf, cax=fig.add_axes([.386 if k == 0 else .891, .20, .014, .69]))
        cb.set_label(label, fontsize=8)
        cb.set_ticks([28, 31, 34, 37] if q == 1 and k == 0 else
                     [28, 34, 40, 46, 50] if k == 0 else [1, 1.5, 2, 2.55])
        cb.ax.tick_params(labelsize=8, length=2)
        axes_labels(ax, hours=q == 2)
        ax.set_title(title, loc="left", pad=8)
        ax.set_ylim(0, 2)
        ax.set_yticks([0, .5, 1, 1.5, 2])
        ax.set_xticks([0, 600, 1200, 1800] if q == 1 else [0, 1, 2, 3])
    save(fig, f"q{q}_spacetime", f"Q{q}: temperature and moisture over time and radius")


def long_fields(name):
    path = {"q3": "results/q3_solution.npz", "fixed": "results/q4_fixed_comparison/fixed_solution.npz",
            "shrink": "results/q4_solution.npz"}[name]
    with load(path) as d:
        y = d["Y"]
        n = y.shape[1] // 2
        ti, ri = sampled(len(y)), sampled(n, 340)
        times = d["times"] if name == "q3" else d["times_s"]
        t = times[ti] / 3600
        c = y[ti, n:][:, ri]
        xi = d["r"][ri] / .02 if name == "q3" else d["xi"][ri]
        radius = d["radius_m"][ti] * 100 if name == "shrink" else np.full(len(t), 2.)
        if name == "q3":
            t = np.r_[t, float(d["t_star"]) / 3600, float(d["t_rep"]) / 3600]
            c = np.vstack([c, d["y_star"][n:][ri], d["y_end"][n:][ri]])
            radius = np.r_[radius, 2., 2.]
    assert c[-1].max() < .15
    return t, xi, radius, c


def long_contour(ax, fields, compact=False):
    t, xi, radius, c = fields
    x, r = np.broadcast_arrays(t[None, :], xi[:, None] * radius[None, :])
    cf = ax.contourf(x, r, np.clip(c.T, .05, 2.55), levels=LEVELS,
                     norm=BoundaryNorm(LEVELS, 256), cmap="YlGnBu")
    cf.set_edgecolor("face")
    cf.set_linewidth(.1)
    contour_labels(ax, x, r, c.T, [.1, .2, .4, 1, 2] if compact else [.1, .2, .3, .4, .6, 1, 1.5, 2])
    contour_labels(ax, x, r, c.T, [.15], red=True,
                   manual=[(.70 * t[-1], .63 * radius[-1])])
    ax.plot(t, radius, color="#333333", lw=1.1)
    axes_labels(ax)
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, 2.2 if compact else 2)
    ax.set_yticks([0, .5, 1, 1.5, 2])
    return cf


def moisture_bar(fig, cf, ax=None, cax=None, compact=False):
    cb = fig.colorbar(cf, ax=ax, cax=cax, spacing="uniform", ticks=BREAKS,
                      fraction=.035, pad=.03)
    cb.set_label(MOISTURE + ("" if compact else "（非等距分级）"), fontsize=8)
    cb.ax.set_yticklabels([f"{v:g}" for v in BREAKS])
    cb.ax.tick_params(labelsize=8, length=2)


def main():
    OUT.mkdir(exist_ok=True)
    short_fields(1)
    short_fields(2)
    fig, ax = plt.subplots(figsize=(6.3, 3.55))
    fig.subplots_adjust(left=.09, right=.88, bottom=.15, top=.965)
    cf = long_contour(ax, long_fields("q3"))
    ax.set_xticks(np.arange(0, 55, 6))
    moisture_bar(fig, cf, ax=ax)
    save(fig, "q3_spacetime", "Q3: nonuniform contour bins, exact critical and report states included")

    fixed, shrink = long_fields("fixed"), long_fields("shrink")
    fig = plt.figure(figsize=(6.3, 5.0))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.1, 1], width_ratios=[1, 1, .045],
                          left=.09, right=.92, bottom=.11, top=.935, hspace=.53, wspace=.33)
    left, right = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    for ax, data, title in [(left, fixed, "(a) 固定半径"), (right, shrink, "(b) 实测半径驱动收缩")]:
        cf = long_contour(ax, data, compact=True)
        ax.set_title(title, loc="left", pad=8)
        ax.text(.98, .98, f"报告时刻 {data[0][-1]:.4f} h", transform=ax.transAxes,
                va="top", ha="right", fontsize=8, bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
        ax.set_xticks([0, 40, 80, 120] if ax is left else [0, 20, 40])
    right.set_ylabel("")
    right.text(28, 1.7, "药材外部", color="#777777", fontsize=8, ha="center")
    right.annotate("边界 $R(t)$", xy=(29, 1.202), xytext=(25, 1.43), fontsize=8,
                   arrowprops={"arrowstyle": "->", "lw": .7, "color": "#555555"})
    moisture_bar(fig, cf, cax=fig.add_subplot(gs[0, 2]), compact=True)
    ax = fig.add_subplot(gs[1, :2])
    for data, color, ls, label in [(fixed, BLUE, "--", "固定半径"), (shrink, RED, "-", "实测半径驱动收缩")]:
        t, _, _, c = data
        ax.plot(t, c[:, 0], color=color, ls=ls, lw=1.2, label=label)
        ax.plot(t[-1], c[-1, 0], "o", color=color, ms=3)
    ax.axhline(.15, color="#777777", ls=":", lw=.8)
    ax.text(133, .17, "0.15", fontsize=8, ha="right", va="bottom")
    ax.set(xlim=(0, 135), ylim=(0, 2.65), xlabel="时间 $t$ (h)", ylabel="$C(0,t)$ (kg/kg)")
    ax.set_title("(c) 同一时间轴上的中心含水率", loc="left", pad=6)
    ax.set_yticks([0, 1, 2])
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "q4_spacetime_comparison", "Appendix-4 fixed/shrink fields with shared-time center comparison")
    (ROOT / "reports/SPACETIME_FIGURE_PROVENANCE_20260913.json").write_text(
        json.dumps(AUDIT, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Four vector figures generated from saved solutions.")


if __name__ == "__main__":
    main()
