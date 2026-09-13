# 2026-09-13 正文短板修补（不含总模型结构图）

用户原话：“用结构图替换问题分析中的部分文字 这个不用做，剩下的你可以完成，记得做了这么按照skill的要求留档”。

本轮只改论文表述、第三问已有校核的写入，以及后期水分量敏感性补算。不改四问正式答卷、Excel 和生产 NPZ。结果采纳仍为 PENDING，不代记人工验收。

## 明确不做

- 不用结构图替换问题分析文字。
- 不把潜热写入主模型，不改写成焓方程 \(\partial_t(BT)\)，不把 \(\rho(C)\) 当作真实湿密度。
- 不把四问主模型改为二维；第四问不扩展二维。
- 不改正式报告时长：问题三 57.4731 h，问题四 51.0877 h。

## 已写入正文

| 项目 | 位置 | 口径 |
|---|---|---|
| 假设（6）后期环境 | `paper/guosai2026/sections/02_assumptions.tex` | 4 h 后 \(T_a=50^\circ\mathrm C\)，\(C_a=0.05\) kg/kg，非实测 |
| Kaya 经验 Robin | 假设（4）、问题一 | 已有 `kaya2007` |
| 问题一回调假设（1）（3） | `sections/03_q1.tex` | 轴对称与不显式潜热 |
| 问题二守恒到本构过渡 | `sections/04_q2.tex` | 同环层守恒；\(B(C)\) 为有效热容量 |
| 问题四物质导数 | `sections/06_q4.tex` | \(\mathrm DT/\mathrm Dt=T_t+vT_r\)，不重做能量守恒 |
| \(C_a\pm10\%\) 敏感性 | `sections/05_q3.tex` 表 `tab_q3_sensitivity` | 仅后期改变 \(C_a\)；\(h_m\) 仍为全程缩放 |
| 轴对称端面校核 | `sections/07_validation.tex` 式 `eq_q3_2d`、图 `fig_q3_2d` | 已有计算写入检验章 |

## 新补数值（非正式答卷）

程序 `code/q3_sensitivity.py --only Ca_minus10pct Ca_plus10pct`。

| 情景 | 未舍入 \(t_*\) / h | 四位显示 | 相对基准 |
|---|---:|---:|---:|
| \(C_a=0.045\) | 57.38152630439856 | 57.3815 | −0.16% |
| \(C_a=0.055\) | 57.58258569937401 | 57.5826 | +0.19% |

窗口记录：`Ca_window=after_4h`，`hm_window=full_horizon`。证据 `results/diagnostics/q3_sensitivity/`。二维校核仍用既有 `results/q3_axisymmetric/comparison.json`：配对网格提前 7.633550 s（约 0.004%），端面排湿约占 5.3%，最湿点仍为中截面中心。

## 编译与核验

- 阅读版 31 页（`reading.pdf` / `reading_comparison.pdf`，与本次 `reading_20260913.pdf` 相同）。`qa_guosai_paper.py` 的页数门禁为阅读版页数减 1 不超过 30，本版通过。
- 完整程序附录版 113 页（`main.pdf`）。
- AI 说明 2 页（`ai_details.pdf`）。
- `code/qa_guosai_paper.py` 退出码 0；六表 216 格与源 NPZ 一致，源哈希未变；阅读版与完整版日志无 Overfull、无未定义引用。
- `reading_updated.pdf` 当时被占用，未覆盖，不能当作本轮阅读版。

## 待用户审阅

新写入的假设（6）表述、\(C_a\) 两行、二维校核段落与图 9，以及问题二/四过渡句。正式四问时长未改，亦不将上述补算记为已采纳。
