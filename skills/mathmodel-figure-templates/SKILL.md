---
name: mathmodel-figure-templates
description: Use this skill in the MathModel LaTeX sandbox when the user asks to reproduce built-in scientific visualization templates, especially prompts from the Improve tab mentioning $mathmodel-figure-templates, 科研绘图模板, SHAP蜂群柱状图, 配对云雨图, 交叉验证ROC, 泰勒图, 相关矩阵组合图, 预测真实值边缘分布图, TPE调参3D曲面, 下三角相关矩阵半边小提琴图, 分组环形热图, 城市公园降温组合图, or Nature和弦图. It provides ready-to-run Python scripts bundled inside the skill.
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

# MathModel Figure Templates

This skill contains the upstream Python/matplotlib reference templates. Resolve its directory and the current project from the actual environment instead of assuming a fixed sandbox path. For this personal competition workflow, read [figure style guidance](../_references/figure_style.md). Use templates for suitable implementation ideas; do not default to reproducing their complete layouts in every paper.

## Fast Path

1. Match the requested chart in `references/figure-catalog.md`.
2. For an explicit template preview, run the renderer from the actual project directory, replacing `SKILL_DIR` with this skill's location:

```bash
python3 "$SKILL_DIR/scripts/render_template.py" paired-raincloud
```

3. The renderer copies the bundled template script into `绘图复刻/scripts/`, runs it there, and writes outputs to `绘图复刻/outputs/`.
4. Return the generated PNG/PDF/SVG paths and the copied script path to the user.

Use `--list` to show supported ids:

```bash
python3 "$SKILL_DIR/scripts/render_template.py" --list
```

## Output Contract

- Work under the current workspace unless the user gives another path.
- Default project folder: `绘图复刻`.
- Script path: `绘图复刻/scripts/make_<template>.py`.
- Outputs: `绘图复刻/outputs/<template>_replica.png`, `.pdf`, `.svg`.
- For literal template reproduction use the bundled scripts; for actual competition figures adapt a workspace copy to the approved result data, argument and project style. Preserve upstream reference assets.
- The bundled scripts use deterministic simulated data. Do not claim simulated values reproduce a source study exactly.

## Template Ids

- `multiclass-shap-combo`
- `paired-raincloud`
- `cv-roc-ci`
- `taylor-diagram`
- `correlation-pairgrid`
- `prediction-marginal-grid`
- `rf-tpe-surface`
- `grouped-corr-split-violin`
- `grouped-circular-heatmap`
- `urban-park-cooling-combo`
- `nature-chord-diagram`

## When Customizing

If the user asks for changes, edit the workspace copy. A sample preview may use simulated data, but competition results must use the approved actual data and retain their provenance. Do not rerun the solver just to change visual style. Preserve:

- `MPLCONFIGDIR` before importing matplotlib.
- deterministic seeds for simulated data.
- PNG/PDF/SVG export.
- readable labels, legends, and high-DPI output.

Use `references/plot-recipes.md` for implementation patterns.
