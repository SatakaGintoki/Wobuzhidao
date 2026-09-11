# 论文笔记与来源映射

> 最新写作偏好（2026-09-11）：用户要求“论文先不要写，我有我写的想法”。论文工作暂停，不续写、润色或合并正文。下方已生成稿件只保留参考；第三问模型记录与数值工作不等于论文写作授权。

- 第三问来源更新：q3-closeout-v1，模型仍为 q3-model-v1；表5、result3、图形和验收入口为 `reports/Q3_VERIFY_REPORT.md`。旧 G4 的57.473333 h及热收支失败记录属于历史版本，恢复写作时应从新版未舍入 NPZ/JSON取值。本轮只更新来源索引，没有修改论文正文。
- 第四问 q4-baseline-v1 从原初值独立求解，不读取第三问结果；第三、四问物性和几何同时变化，不能把两问时长差全部归因于收缩。

- 引擎沿用用户已选LaTeX/xelatex；入口`paper/main.tex`；编译器`D:/MikTex/miktex/bin/x64/xelatex.exe`。主论文正有并行编辑，本轮最终交付位于独立closeout目录，避免覆盖。
- 前两问收尾授权包含可审阅章节整理；章节为草稿，结果采纳状态仍PENDING。本轮不写摘要和后问结果。
- 第一问章节`paper/closeout/sections/5_problem1.tex`：对应q1-plan-v1/PCHIP和q1-closeout-v1；表1、2来自`results/q1_solution.npz`，验证来自`q1_validation.json`；径向温湿图来自`figures/q1_T_profiles.pdf`、`q1_C_profiles.pdf`。
- 第二问章节`paper/closeout/sections/6_problem2.tex`：对应q2-plan-v2和q2-closeout-v1；表3、4来自`results/q2_solution.npz`，验证来自`q2_validation.json`及已有独立G8审核；图来自`figures/q2_T_profiles.pdf`、`q2_C_profiles.pdf`。
- 章节构建脚本`code/build_q12_chapters.py`，表格直接从未舍入NPZ格式化四位小数，避免CSV二次舍入。参考文献hussain2003对应文献记录L02，只引方法旁证。
- 独立阅读入口`paper/q12_closeout.pdf`，源文件复用主模板前导及相同章节；整篇仍有未完成占位，不是提交版。
- 符号统一：T以摄氏度存储；Arrhenius项使用T+273.15；C为kg水/kg干物质；R=0.02m；B=rho*cp为有效体积热容量。
- 第一问温度/水分分别积分；第二问两场联合积分且物性全时段替换为附录3，均从原初值开始，不拼接两问结果。
- 结果中全部规定输出点通过2e-5相邻网格差目标，论文表四位稳定；不得写“全部Excel末位完全冻结”“真实物理预测精度达到四位”。
- 第一问湿收支旧2.10e-6来自1s梯形积分，本次改为连续解自适应积分；解析对照截断检查也已更新，旧验证描述须结合收尾报告阅读。
- `paper/drafts/`原始推导保留为历史写作材料；本轮最新章节与数值以本映射为准。历史笔记保存在`reports/archive/pre-closeout-20260911/PAPER_NOTES.md`。

## 其他写作任务记录（原文保留，数值版本以上方收尾映射为准）

# 论文笔记

- 引擎：LaTeX（xelatex）。工作区模板：`paper/main.tex`（由 `zh/cumcm-latex` 复制，Overleaf 用 `fontset=fandol`）。
- 2026-09-11 用户要求先把整体正文写满便于修改。已写入标题、摘要、重述至评价及参考文献。问题一、二表格数字来自当前基线（四位显示）；问题三、四只写模型与判据，时长和表5–6数值留空，未编造。无图文件，正文未插图。
- Overleaf 导入包：桌面文件夹 `药材烘干-Overleaf`，以及 zip `药材烘干-Overleaf.zip`（项目内另有 `overleaf-upload.zip`）。只含 `main.tex`、`sections/`、`references.tex`、`latexmkrc`。上传后编译器选 XeLaTeX。
- 问题一方法口径（求解前）：主求解为节点有限体积 + BDF；温度为 Bessel–Duhamel 精确核验；水分为变 \(D(C)\) 数值解，冻结 \(D\) 只核验离散，\(D\) 变幅事后决定能否佐证。
- 草稿：`paper/drafts/problem1_solving_outline.md`（写法与结构），`paper/drafts/problem1_solver.md`（有限体积与 BDF 细推导）。
- 解析温度推导与用户整理的分离变量链条一致；\(A_n\) 两种写法等价。
- 问题一结果：`q1-baseline-v1` 待审，见 `reports/RESULTS_REPORT.md`。方法草稿可迁入正文，表1–2数字须等结果批准。
- 对应模型记录：`reports/models/q1.md`，版本 `q1-plan-v1`。
