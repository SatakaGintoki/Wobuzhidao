# 正文图参考配色统一记录

版本：`paper-palette-reference-v1`。用户明确授权“所有结果图和三张示意图都换色”。实施与技术检查完成，用户最终视觉审核未代记。

## 范围与来源

参考用户提供的 `微信图片_20260913121806_72_219.png` 和 `微信图片_20260913121806_73_219.png`，位于 `C:/Users/chens/Desktop/组员的论文修改/图片/`。沿用现有图型，仅借鉴配色。

正文结果图共 10 份：`q1_oven_input`、`q4_R_history`、`q1_T_profiles`、`q1_C_profiles`、`q2_T_profiles`、`q2_C_profiles`、`q3_C_profiles`、`q4_C_profiles`、`q3_axisymmetric_check`、`q4_fixed_vs_shrink`。另含 `fig_q1_model`、`fig_flow_q3`、`fig_q4_coordinates` 三张示意图；合计 13 份图资产，正文组合为 11 个图号。未引用的诊断图不在本轮范围。

换色前图文件、Draw.io 与生成来源保存于 `ARCHIVE_all/figure_palette_before_reference_20260913/`。数值来源仍沿用原结果与图形生成记录，无新计算或数据调整。

## 配色规则

| 对象 | 配色 |
| --- | --- |
| 温度剖面 | `coolwarm` 有序蓝红色阶，细线避开近白色 |
| 含水率剖面 | `YlGnBu` 的 0.98 至 0.43，早期深蓝到后期青色 |
| 二维含水率云图及色条 | 完整 `YlGnBu`，浅黄至深蓝，原数值等级保持 |
| 对照曲线 | 红 `#D65244`、蓝 `#4358C5` |
| 环境输入 | 温度红 `#D65244`、含水率青 `#1D91C0` |
| 示意图 | 蓝轮廓、青绿 `#80CDBB` 圆柱、红色热量与事件、青色水分 |

示意图圆柱保持原透明度和完整水平轮廓，字体、公式单行、材料点与引线位置保持。几何填色不表示计算场。

## 复现

10 份结果图使用 `code/recolor_paper_figures.py` 解析 PDF 绘图指令与 Form XObject，替换颜色并保留矢量结构。原绘图生成器尚沿用历史色值，因此本步骤必须在原生成器之后执行，输入必须是原配色 PDF。工作目录为项目根目录：

```powershell
& 'D:/python/python.exe' 'code/recolor_paper_figures.py' --source-dir 'ARCHIVE_all/figure_palette_before_reference_20260913/figures' --output-dir '_tmp/reference_palette'
```

依赖 matplotlib、numpy、pypdf。输出后同步对应 PDF 和渲染预览到 `figures/` 及论文的现有图文件位置。三张示意图在 `figures/source/build_q1_model.py`、`build_q3_event.py`、`build_q4_coordinates.py` 中维护颜色，通过原流程生成 Draw.io、TeX 和 PDF。

## 验证与交付

- `FIGURE_PALETTE_20260913.json` 保存逐图输入输出 SHA256、颜色映射和非颜色指令校验。文字、页面尺寸与路径保持；PDF 数字序列化允许不超过 1e-6 的表示误差，不涉及模型数据变化。包含灰色第八条曲线的换色校验。
- 三张 Draw.io 解码 stencil 后比较非颜色内容，文字、几何及连接关系保持。13 图预览和正文 11 张图所在页均已目视检查。
- `FIGURE_PALETTE_PAPER_CHECK_20260913.json` 保存正文页数、图号与页码；阅读版 35 页，完整版 117 页，前 35 页文本一致。无 Overfull/Underfull、未定义或重复引用。
- 当前图 1 至 11 页码依次为 5、6、8、10、15、17、19、21、22、26、27。三张示意图为图 3/6/9。
- 正式入口仅为 `paper/guosai2026/reading.pdf` 和 `main.pdf`，已由暂存编译产物同步并校验哈希；现有 `support/figures/q3_axisymmetric_check.pdf/.png` 副本同步更新。
- 本次无论文文字、图型、模型或数值改动；编译沿用当时工作区最新正文。原结果审核状态不变。
