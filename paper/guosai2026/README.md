# 当前论文基准

2026-09-13评阅补充落实后的最新交付：`reading.pdf`为32页，`main.pdf`为117页。新增第四问条件性温度敏感性分析及附录B.6潜热量级核算，收紧端面与收敛结论；保留同期图注精简和原图。两版共有页面一致，正式答案、六张题定表与四个Excel保持。记录见 `../../reports/REVIEWER_FIXES_20260913.md`。下段页数对应前一轮交付。

2026-09-13结果分析与图注精简后的正文阅读版为32页，含完整程序附录版为116页。10张正文图采用简短图名，图表解释放入正文；补充第三问末期耗时和第四问同时间对照，保留当前温度敏感性与端面讨论。四问正式数值及题定表保持。`reading.pdf`与`main.pdf`均已同步新版，可直接打开；本轮修改与核验见 `../../reports/RESULT_ANALYSIS_CAPTIONS_20260913.md`。`review/`中的旧审阅快照仅供追溯。

当前图4、5、7、10采用用户提供的四张原始 PNG，版本 `paper-spacetime-original-v1`，论文内文件名均以 `_original.png` 结尾。原图10径向剖面已按用户要求从正文删除，原时空对照图11自动改为图10；旧图文件仅供追溯。保留原始像素、字体、配色和布局；`code/plot_paper_spacetime.py` 的重绘版已被替换，后续生成不得覆盖这些原图。核对及采用记录见 `../../reports/ORIGINAL_FIGURES_20260913.md`。

本目录是唯一正式论文工作区。正式论文只保留两个版本：

- `main.tex` / `main.pdf`：完整论文，含程序附录
- `reading.tex` / `reading.pdf`：正文阅读版

编译所需的章节、表格、图片和支撑材料均位于本目录内。问题三、四正文分别为 `sections/05_q3.tex`、`sections/06_q4.tex`；二维校核正文为 `sections/07_axisymmetric.tex`。

编译器必须选择 **XeLaTeX**。在本目录运行 `latexmk -xelatex main.tex` 或 `latexmk -xelatex reading.tex`，自动重复编译直至交叉引用稳定。Overleaf 同样选择 XeLaTeX；VS Code 的项目配置已设为 `latexmk (XeLaTeX)`。两个入口均已声明编译器，公共导言区会阻止错误引擎继续生成乱码 PDF。

旧版 PDF、编译日志、临时目录、日期交付包和历史源码统一存放在项目根目录的 `ARCHIVE_all/`，不作为当前论文入口。

论文目录中的图只保留正文实际引用的版本；`q3_C_max_history.pdf` 和 `q4_C_history.pdf` 属于生成器输出的诊断图，保留作追溯但不作为正文图，也不在后续正式打包序列中复制。

当前正文图采用 `paper-palette-reference-v1` 配色。结果图原生成器输出后，需在项目根目录使用 `code/recolor_paper_figures.py` 对原配色 PDF 执行换色，再同步到本目录；三张示意图的生成来源已内置新色值。复现命令和校验见 `../../reports/FIGURE_PALETTE_20260913.md`，避免后续生成覆盖当前配色。
