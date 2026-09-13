# -*- coding: utf-8 -*-
"""问题4：独立求解并导出答案。运行 python Q4.py。
仅依赖numpy、scipy、openpyxl和同目录data附件。精简版未重新运行核验。
"""
from pathlib import Path
import csv
import json
import numpy as np
from openpyxl import load_workbook
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator
from scipy.sparse import diags, lil_matrix

ROOT = Path(__file__).resolve().parent
ATTACH = ROOT / "data" / "附件"
OUT = ROOT / "results"
R, H, HM, T0, C0 = 0.02, 25.0, 8e-7, 28.0, 2.55


def read_table(name):
    wb = load_workbook(ATTACH / name, read_only=True, data_only=True)
    rows = np.asarray(list(wb.active.values)[1:], dtype=float)
    wb.close()
    return rows


def environment(end):
    rows = read_table("附件1.xlsx")
    rows = rows[rows[:, 0] <= end]
    return (PchipInterpolator(rows[:, 0], rows[:, 1], extrapolate=False),
            PchipInterpolator(rows[:, 0], rows[:, 2], extrapolate=False))


def save_excel(question, times, fields):
    wb = load_workbook(ATTACH / "附件3" / f"result{question}.xlsx")
    for ws, field in zip(wb.worksheets, fields):
        header, surface = ws.cell(1, 1).value, ws.cell(1, ws.max_column).value
        ws.delete_rows(1, ws.max_row)
        ws.append([header] + [j / 10 for j in range(21)] + ([surface] if question == 4 else []))
        for t, row in zip(times, field):
            ws.append([float(t)] + [None if np.isnan(v) else float(v) for v in row])
        for row in ws.iter_rows(min_row=2, min_col=2):
            for cell in row:
                cell.number_format = "0.0000"
        ws.freeze_panes = "B2"
    OUT.mkdir(exist_ok=True)
    wb.properties.creator = wb.properties.lastModifiedBy = "Team"
    wb.save(OUT / f"result{question}.xlsx")
    wb.close()
    print(f"已生成 results/result{question}.xlsx", flush=True)


def save_csv(name, times, values, headers):
    with (OUT / name).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["时间"] + headers)
        for t, row in zip(times, values):
            writer.writerow([f"{t:.4f}"] + ["" if np.isnan(v) else f"{v:.4f}" for v in row])


def integrate(rhs, interval, initial, **options):
    solution = solve_ivp(rhs, interval, initial, method="BDF", **options)
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution


def geometry(nodes):
    faces = (nodes[:-1] + nodes[1:]) / 2
    return faces, np.diff(nodes), np.diff(np.r_[nodes[0], faces, nodes[-1]]**2) / 2


def graded_radial_nodes(level: int) -> np.ndarray:
    """Nodes denser near the surface; every 0.1 cm output radius remains a node.

    Interval subdivisions (before multiplying by ``level``):
    0–1.5 cm: 8; 1.5–1.8 cm: 16; 1.8–1.9 cm: 32; 1.9–2.0 cm: 64.
    Surface spacing at level L is 1e-3 / (64 L) metres.
    """
    level = int(level)
    if level < 1:
        raise ValueError("graded mesh level must be a positive integer")
    n_sub = np.full(20, 8 * level, dtype=int)
    n_sub[15:] = 16 * level
    n_sub[18] = 32 * level
    n_sub[19] = 64 * level
    pts = [0.0]
    for j in range(20):
        r0 = 0.001 * j
        r1 = 0.001 * (j + 1)
        m = int(n_sub[j])
        for k in range(1, m + 1):
            pts.append(r0 + (r1 - r0) * k / m)
    r = np.asarray(pts, dtype=float)
    r[0] = 0.0
    r[-1] = R
    return r

def harmonic_mean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = np.zeros_like(a, dtype=float)
    both = (a > 0.0) & (b > 0.0)
    out[both] = 2.0 * a[both] * b[both] / (a[both] + b[both])
    return out

def coupled_sparsity(n):
    matrix = lil_matrix((2*n, 2*n))
    for i in range(n):
        for j in range(max(0, i-1), min(n, i+2)):
            matrix[i, j] = matrix[i, n+j] = matrix[n+i, j] = matrix[n+i, n+j] = 1
    return matrix.tocsc()


def properties(C, T):
    C, T = np.asarray(C), np.asarray(T)
    # Only protect nonphysical implicit-iteration probes; stored states are audited.
    Cp = np.maximum(C, 1e-12)
    rho = 760.0 + 90.0 * Cp
    cp = 1850.0 + 2150.0 * Cp / (1.0 + Cp)
    k = 0.12 + 0.20 * Cp / (1.0 + Cp)
    D = 4.2e-4 * np.exp(-0.30 / Cp) * np.exp(-3850.0 / (T + 273.15))
    return rho * cp, k, D

def main():
    Ta, Ca = environment(14400.0)
    rows = read_table("附件2.xlsx")
    radius = PchipInterpolator(rows[:, 0], rows[:, 1]/100, extrapolate=False)
    xi = graded_radial_nodes(8)/R
    n = len(xi)
    faces, dx, weights = geometry(xi)
    def rhs(t, y, late):
        rr = float(radius(t))
        T, C = y[:n], y[n:]
        B, k, D = properties(C, T)
        ambient_T, ambient_C = (50.0, 0.05) if late else (float(Ta(t)), float(Ca(t)))
        FT = np.r_[0., -faces*harmonic_mean(k[:-1], k[1:])*np.diff(T)/dx, rr*H*(T[-1]-ambient_T)]
        FC = np.r_[0., -faces*harmonic_mean(D[:-1], D[1:])*np.diff(C)/dx, rr*HM*(C[-1]-ambient_C)]
        return np.r_[-np.diff(FT)/(rr**2*weights*B), -np.diff(FC)/(rr**2*weights)]
    event = lambda t, y: float(np.max(y[n:])-0.15)
    event.direction, event.terminal = -1.0, False
    options = dict(rtol=1e-8, atol=np.r_[np.full(n, 1e-8), np.full(n, 1e-10)], jac_sparsity=coupled_sparsity(n))
    initial = np.r_[np.full(n, T0), np.full(n, C0)]
    times, states = [], []
    breaks = np.unique(np.r_[0., 14400., np.arange(21600., min(259200., rows[-1, 0])+1, 21600.)])
    print("问题四：独立计算径向收缩模型...", flush=True)
    t_star = None
    for start, end in zip(breaks[:-1], breaks[1:]):
        late = start >= 14400
        solution = integrate(lambda t, y: rhs(t, y, late), (start, end), initial,
                             max_step=60.0 if late else 10.0, dense_output=True, events=event, **options)
        ts = np.arange(start+60, end+0.1, 60)
        times.extend(ts)
        states.extend(solution.sol(ts).T)
        initial = solution.y[:, -1]
        print(f"已计算至 {end/3600:.1f} h", flush=True)
        if len(solution.t_events[0]):
            t_star = float(solution.t_events[0][0])
            break
    if t_star is None:
        raise RuntimeError("No drying event within the measured radius interval")
    # Keep the two-second offset; this lean version does not compare other grids.
    report = np.ceil((t_star+2.0)/0.36)*0.36
    if report > rows[-1, 0]:
        raise RuntimeError("Reporting time exceeds measured radius coverage")
    times, states = np.asarray(times), np.asarray(states)
    keep = times < report
    times, states = times[keep], states[keep]
    final_solution = integrate(lambda t, y: rhs(t, y, True), (times[-1], report), states[-1],
                               rtol=1e-10, atol=np.r_[np.full(n, 1e-10), np.full(n, 1e-12)],
                               max_step=1.0, jac_sparsity=coupled_sparsity(n))
    final = final_solution.y[:, -1]
    if np.max(final[n:]) >= 0.15:
        raise RuntimeError("Final state is not strictly below the drying threshold")
    times = np.r_[times, report]
    states = np.vstack([states, final])
    fixed = np.arange(21)*.001
    radii = radius(times)
    C = np.full((len(times), 22), np.nan)
    for i, (state, rr) in enumerate(zip(states, radii)):
        good = fixed <= rr+1e-14
        C[i, :21][good] = PchipInterpolator(xi, state[n:], extrapolate=False)(np.minimum(fixed[good]/rr, 1.0))
        C[i, -1] = state[-1]
    save_excel(4, times, [C])
    tt = np.r_[np.arange(21600, report, 21600), report]
    ids = [int(np.argmin(abs(times-t))) for t in tt]
    table = np.column_stack([C[ids][:, [0, 5, 10, 15, 20, 21]], radii[ids]*100])
    save_csv("q4_table6.csv", tt/3600, table, ["0 cm", "0.5 cm", "1 cm", "1.5 cm", "2 cm", "药材表面", "半径/cm"])
    answer = dict(critical_h=t_star/3600, report_h=report/3600, max_moisture=float(np.max(final[n:])), radius_cm=float(radius(report)*100))
    (OUT / "q4_answer.json").write_text(json.dumps(answer, indent=2), encoding="utf-8")
    print(f"烘干报告时间：{report/3600:.4f} h", flush=True)


if __name__ == "__main__":
    main()
