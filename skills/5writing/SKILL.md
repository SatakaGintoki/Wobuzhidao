---
name: 5writing
description: "数学建模论文逐问积累与全文整合。每问最终结果审核通过后撰写对应方法和结果，全部完成后统一摘要、引言、结论和排版；支持 Typst 与 LaTeX。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 竞赛论文撰写（Typst / LaTeX）

本 skill 承接 `3coding-visual` 和 `4drawio`。前序阶段只提供真实数据、图表 PDF 和记录文件；本阶段负责选择比赛模板和排版引擎、组织论文结构，并决定每张图表放入哪个章节。

先读取 [审核与逐问推进规则](../_references/review_workflow.md)。进入本阶段前核对当前问最终结果已获批准且未失效；原始结果存在或基线已批准但探索尚未结束，都不代表本问可以正式定稿。

## 两种写作范围

- **逐问积累**：本问最终结果通过后，及时写出本问假设、符号、模型、求解、结果、图表说明和局限。引擎未定时写 `paper/drafts/problemN.md`；引擎已定时增量更新对应章节，或在模板跨问题章节中补充本问小节。不提前填造后问内容，不重建已有论文。
- **全文整合**：所有必需问题的最终结果均有效且审核通过后，把逐问材料组织进模板，统一引言、摘要、结论、章节衔接、符号与图表引用。必要时保留已有单问草稿作为来源，不把内部审核信息写入正式正文。

在 `reports/PAPER_NOTES.md` 增量记录共享符号/术语、各问段落位置、对应方案和最终结果版本、数值来源及待更新项。阶段间用这份映射识别受影响段落，不能在前问改动后保留失效结论。

按 [跨问记录与上下文恢复](../_references/context_memory.md) 读取本问有效模型记录及其引用的原报告/结果，不凭聊天摘要重建模型；写作保留假设和结论的适用限制，不把候选或被否决方法写成采用方法。段落完成后更新模型记录中的段落链接及状态索引，数值和符号仍引用原有记录，避免多份独立副本。

本问草稿供用户随时查看，不新增强制写作审核关卡；发现科学含义不清、文献未核实或证据缺口时说明具体问题，不自行补造论证。本问积累后回交总控进入下一问。

**Typst 引擎**下可调用 typst-author skill 学习 typst 写法；**LaTeX 引擎**参考本文件末尾的"LaTeX 写作要点"小节。

## 数学建模规范参考

如需领域判断，读取 `../_references/math_modeling_norms.md` 中的“论文写作”“图表与可视化”和“非数据图工具选择”小节。该文件只作为规范知识库，论文结构仍按比赛模板和当前赛题内容决定。

## 模板族

本技能内捆绑的模板位于：

```text
templates/zh/<竞赛>/main.typ         # Typst 模板
templates/zh/<竞赛>-latex/main.tex   # LaTeX 模板
templates/en/<竞赛>/main.typ         # Typst 模板
templates/en/<竞赛>-latex/main.tex   # LaTeX 模板
```

**LaTeX 模板覆盖范围**：所有中文模板和英文模板均已提供 LaTeX 版本（`-latex` 后缀），使用 xelatex 编译。

支持的中文模板（Typst + LaTeX 双版本）：

```text
apmcm, changsanjiao, cumcm, default, diangongbei, dongsansheng,
huashubei, huaweibei, huazhongbei, mathorcup, mcm, shuweibei, stats, wuyibei
```

华为杯、华中杯、五一杯统一使用 `huaweibei`、`huazhongbei`、`wuyibei` 作为模板。

支持的英文模板（Typst + LaTeX 双版本）：

```text
apmcm, default, mcm
```

论文中的数值与图表必须来自已审核的当前结果版本，并能对应 `reports/RESULTS_REPORT.md` 的关键指标记录及源文件。按规定单位、尺度和显示精度表达；不得编造、从图片估读精确数值或引用失效结果。


## 工作流

### 步骤 0：确定排版引擎

**正式模板排版前确定引擎；逐问 Markdown 积累不依赖引擎。** 引擎决定模板路径、章节扩展名、图片语法和编译命令。

复用会话、已有论文或 `plan.md` 中已确定的引擎。仅在开始正式排版且选择仍缺失时，使用宿主可用方式询问："撰写论文使用哪种排版引擎？"

- 选项 1：LaTeX（xelatex 编译，数学建模竞赛主流，模板已全部就绪）— 推荐选项放第一位
- 选项 2：Typst（typst 编译，调用 typst-author skill 辅助写作）

已明确选择时直接沿用，不重复确认。尚未回复时继续可做的 Markdown 积累，不自定引擎；用户明确委托选择时，可结合现有环境与模板推荐并记录实际决定。

根据确定的引擎选择对应模板族：

- **Typst 引擎**：使用 `templates/<lang>/<竞赛>/main.typ`，调用 typst-author skill。编译命令 `typst compile main.typ`。
- **LaTeX 引擎**：使用 `templates/<lang>/<竞赛>-latex/main.tex`，xelatex 编译（中文和英文均需跑两遍解决交叉引用）。编译命令 `xelatex -interaction=nonstopmode main.tex`（执行两次）。

**后续步骤中的所有代码示例、文件扩展名、图片插入语法都必须按所选引擎选择对应版本，不要混用。**

### 步骤 1：选择语言和模板


本个人版默认全国大学生数学建模竞赛、中文，模板为 `zh/cumcm` 或 `zh/cumcm-latex`。其他赛事按用户要求；MCM/ICM/COMAP 通常使用英文。正式提交前核对本次赛事官方要求，不能把捆绑模板或知识库年份当作当前规则。

模板键示例（Typst 引擎）：

```text
长三角 -> zh/changsanjiao
APMCM 英文版 -> en/apmcm
全国赛/国赛/CUMCM -> zh/cumcm
统计建模 -> zh/stats
MCM/ICM/COMAP -> en/mcm
```

模板键示例（LaTeX 引擎）：

```text
全国赛/国赛/CUMCM -> zh/cumcm-latex
MCM/ICM/COMAP -> en/mcm-latex
```

### 步骤 2：准备模板

先按 [运行环境与路径](../_references/runtime_environment.md) 核对所选编译器和字体。在工作区副本调整不匹配的字体配置：例如 Windows 不直接沿用 `fontset=mac`；确认字体存在后改为合适 fontset 或显式字体。无需修改上游模板资产。先做最小编译检查，再排版全文。

用以下命令检查捆绑模板是否可访问（`SKILL_DIR` 为本 skill 所在目录）：

**Typst 模板**：

```bash
ls "$SKILL_DIR/templates/zh/<竞赛>/main.typ" 2>/dev/null && echo "OK" || echo "MISSING"
```

- **文件存在（OK）**：首次排版时将匹配模板整目录复制到 `paper/`，保留已有草稿；已有入口和章节时只增量编辑，不能重复复制覆盖。沿用模板内部依赖。
- **文件不存在（MISSING）**：说明 skill 未完整安装或在沙箱中，此时依照本 SKILL.md 步骤 3 列出的对应节文件结构，从零重建最小可编译 Typst 框架，并在 `paper/` 内注明"重建自 default 结构"。

存在匹配模板时，绝不从零开始写论文。

**LaTeX 模板**：

```bash
ls "$SKILL_DIR/templates/zh/<竞赛>-latex/main.tex" 2>/dev/null && echo "OK" || echo "MISSING"
```

- **文件存在（OK）**：首次排版时将匹配模板整目录复制到 `paper/`，保留已有草稿；已有入口和章节时增量编辑，不覆盖累计成果。
- **文件不存在（MISSING）**：说明 skill 未完整安装或在沙箱中，此时依照本 SKILL.md 步骤 3 列出的对应节文件结构，从零重建最小可编译 LaTeX 框架，并在 `paper/` 内注明"重建自 default-latex 结构"。


### 步骤 3：构建图表规划

在写正文各节之前，根据 `figures/*.pdf`、`reports/RESULTS_REPORT.md`，以及 `reports/DRAWIO_REPORT.md`（如果存在）构建图表规划：

```text
图表规划
fig_roadmap.pdf -> 引言/问题重述
fig_flow_q1.pdf -> 问题一模型构建
fig_flow_q2.pdf -> 问题二模型构建
fig_pipeline.pdf -> 数据预处理/方法节
结果图 -> 对应的结果节
```

Typst 图片路径按所在源文件及项目根解析：`paper/main.typ` 常用 `../figures/xxx.pdf`，`paper/sections/*.typ` 常用 `../../figures/xxx.pdf`，跨目录时需设置允许访问的项目根。LaTeX 固定从 `paper/` 编译，图片路径按该编译工作目录解析，通常为 `../figures/xxx.pdf`，不随章节文件目录额外增加一级 `..`。

**Typst 引擎**图片插入：

```typst
#figure(
  image("../../figures/fig_q1_error_dist.pdf", width: 85%),
  caption: [问题一预测误差分布],
)
```

**LaTeX 引擎**图片插入：

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{../figures/fig_q1_error_dist.pdf}
  \caption{问题一预测误差分布}
  \label{fig:q1_error}
\end{figure}
```

英文论文使用英文图注。

沿用 `figures/STYLE.md` 中认可的风格，不在写作阶段重置为模板配色。嵌入后检查实际字号、图例、裁切及跨图语义一致；仅调整尺寸等展示问题不改变数值含义。

### 步骤 4：撰写各节

**以下章节文件名按所选引擎使用 `.typ`（Typst）或 `.tex`（LaTeX）扩展名。** 例如 Typst 引擎用 `1_restatement.typ`，LaTeX 引擎用 `1_restatement.tex`。文件名主体保持一致。

按当前问及实际模板组织方法、结果和局限；建议题以有依据的建议组织，不硬填公式。需要具体文件名时，只读取 [各赛事模板章节参考](references/template-sections.md) 中所选赛事/引擎部分。

**正文写作应使用连贯的学术段落。避免在最终论文中出现工作流内部名称，如 `reports/`、`figures/` 或 `CLAUDE.md`。**

### 步骤 5：参考文献

按 [文献参与建模规则](../_references/literature_support.md) 读取 `reports/LITERATURE_REPORT.md` 及当前问建模依据表。逐问积累时就把已核实的模型、假设、公式或参数依据放在相应段落，不到最后才补引用。复用稳定来源标识维护引用映射，不重复搜索已验证且仍适用的来源。

清楚说明文献方法与本题的差异和改造；自行提出的假设、推导或改进不得归给文献。仅摘要可访问时，不把未读全文细节写成已证实事实。确需补充论点时先核实来源，不能先写结论再找题目相似的文章作依据。

只使用真实存在且已核对与相应论点关系的参考文献；未核实项记入 `PAPER_NOTES.md`，不编造作者、题名或标识。文件名通常按引擎选择：Typst 用 `paper/references.typ`，LaTeX 用 `paper/references.tex`；已有模板采用 BibTeX/Biber 等机制时沿用。

**Typst 引擎**：

```typst
#set enum(numbering: "[1]")
#enum[
  作者. 题名[J]. 期刊名, 年份, 卷(期): 页码.
  Author. "Title." Journal or Conference, year.
]
```

正文上标引用：`相关研究已用于物流网络优化#super("[1]")。`

**LaTeX 引擎**：

```latex
\begin{thebibliography}{99}
  \bibitem{ref1} 作者. 题名[J]. 期刊名, 年份, 卷(期): 页码.
  \bibitem{ref2} Author. "Title." Journal, year.
\end{thebibliography}
```

正文引用用 `\cite{ref1}` 或 `\cite{ref1,ref2}`。

### 步骤 6：最后撰写摘要或总结

全部问题最终结果审核通过、各问段落完成后，统一引言、摘要或 Summary Sheet、结论与章节衔接。摘要概括主要方法及有依据的关键结果，按指标规定精度表达，不为每问硬凑数值。检查符号、单位、图表编号及结论与最新结果的对应关系。

## LaTeX 写作要点

以下要点供 **LaTeX 引擎**使用。Typst 引擎请调用 typst-author skill 获取语法帮助。

### 编译命令

以下为无外部文献处理步骤时的基础示例，从 `paper/` 运行。使用 BibTeX、Biber 或其他模板步骤时完成实际编译链，不假设两次 xelatex 总能解决全部引用。环境命令按实际平台调整。

```bash
# 中文模板（xelatex，跑两遍解决交叉引用）
xelatex main.tex && xelatex main.tex

# 英文模板（xelatex，同样跑两遍）
xelatex main.tex && xelatex main.tex
```

### 文档结构

```latex
\documentclass[a4paper,12pt]{article}   % 英文
\documentclass[a4paper,12pt]{ctexart}   % 中文

\usepackage{...}   % 宏包加载
\usepackage{graphicx}   % 图片支持
\usepackage{booktabs}   % 三线表
\usepackage{amsmath,amssymb}   % 数学公式
\usepackage{hyperref}   % 交叉引用（需两遍编译）
```

### 图表插入

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{../figures/fig_q1.pdf}
  \caption{图注}
  \label{fig:q1}
\end{figure}

% 三线表
\begin{table}[htbp]
  \centering
  \caption{表注}
  \begin{tabular}{ccc}
    \toprule
    \textbf{列1} & \textbf{列2} & \textbf{列3} \\
    \midrule
    数据 & 数据 & 数据 \\
    \bottomrule
  \end{tabular}
\end{table}
```

### 交叉引用

```latex
如图~\ref{fig:q1}所示，...   % 图片引用
式~(\ref{eq:objective}) 给出...   % 公式引用
见第~\pageref{fig:q1} 页   % 页码引用
```

### 数学公式

```latex
行内公式：$f(x) = \sum_{i=1}^n \theta_i \phi_i(x)$

行间公式：
\begin{equation}
  \mathcal{L}(\theta) = \frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2
  \label{eq:objective}
\end{equation}
```

### 章节和强调

```latex
\section{问题重述}
\subsection{问题背景}
\textbf{问题一：} xxx   % 对应 Typst 的 #strong
```
