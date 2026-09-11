---
name: 1start-mathmodel
description: "全国大学生数学建模竞赛个人工作流入口。先审核整体路线，再逐问审核方案、实现求解、审核结果并积累论文，最后整合验收；用于启动或继续建模任务。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 数学建模工作流

本 skill 是数学建模竞赛项目的总控入口，负责记录偏好与决策、生成计划并按审核状态调用各阶段。开始或恢复任务时先读取 [审核与逐问推进规则](../_references/review_workflow.md)，以其中的批准范围、暂停和变更规则控制下游执行。

## 数学建模规范参考

如需领域判断，读取 `../_references/math_modeling_norms.md`。该文件只提供数学建模基本规范和防错知识，不改变本 skill 的阶段顺序和产出约定。

## 必须产出

在当前工作目录中创建或更新以下文件：

- `plan.md`：整体流程方案、建模方向、阶段顺序、预期产物和风险控制。
- `todo.md`：具体待办事项列表，记录每个阶段的任务和状态。
- `reports/REVIEW_LOG.md`：整体路线、逐问方案和结果的版本、用户决定与影响范围。
- `reports/LITERATURE_REPORT.md`：整体与逐问检索的来源、支持关系、适用差异和核实状态，由建模阶段增量维护。
- `reports/STATE.md`：当前阶段、批准/待审版本、依赖、恢复入口及下一步；按 [跨问记录与上下文恢复](../_references/context_memory.md) 维护，并在恢复时先读取。
- `reports/models/qN.md`：仅为已经展开的问题建立模型记录，保存建立依据、关键语义、源文件和跨问交接；详细格式见上述恢复规则。

## 工作流

### 1. 读取偏好与本次范围

复用会话和现有计划，不重复确认用户已经给出的偏好。默认赛事为全国大学生数学建模竞赛、论文中文；其他赛事按用户要求。单阶段请求只完成请求范围及必要准备。

优先询问（按重要性排序）：

1. **题面和附件是否充分**：子问题数量由题面识别，缺失的必要输入才询问。
2. **已有进度与时间约束**：从已审核成果继续；需要探索时明确投入范围。
3. **排版引擎**：沿用现有选择；未确定可先积累 Markdown 段落，不阻塞建模，正式排版前再选择 Typst 或 LaTeX。
4. **绘图偏好**：暂不指定固定配色，先生成初稿，再随结果反馈逐步确定。

将用户的选择记录到 `plan.md` 的"方案"小节中。

需要代码或排版时按 [实际运行环境与路径](../_references/runtime_environment.md) 复用项目解释器与工具路径，阶段依赖按需检查；纯讨论不因缺少后期编译器而阻塞。


### 2. 制定方案

按以下结构编写 `plan.md`：

```markdown
# 方案

先整体审核，再按当前问调用这些 skill。没有对应批准不得越过审核点。

用户偏好：
- 排版引擎：<已有选择 / 待正式排版前确定>
- 竞赛类型：全国大学生数学建模竞赛（用户另有指定则替换）
- 论文语言：中文（用户另有指定则替换）
- 子问题数量：<已知 N 个 / 待分析确定>

workflow:
   step      skills
1. 整体路线分析与领域文献检索 - `2analysis-modeling` → 用户审核
2. 当前问详细方案与文献依据 - `2analysis-modeling` → 用户审核
3. 稳健方案求解及图表 - `3coding-visual`、按需 `4drawio` → 用户审核基线结果
4. 已批准的探索 - `3coding-visual` → 用户审核最终结果（不探索则复用基线结果批准）
5. 当前问章节积累 - `5writing` → 更新依赖后回到步骤 2
6. 全部完成后全文整合 - `5writing` → 最终验收 `6verity`
```

## 项目目录结构

各阶段按此骨架创建和填充文件：

```text
.
├── plan.md                      # 1: 本文件
├── todo.md                      # 1: 待办事项
├── reports/                     # 各阶段文档报告
│   ├── ANALYSIS_MODELING_REPORT.md  # 1: 赛题分析-建模报告（2analysis-modeling）
│   ├── RESULTS_REPORT.md            # 2: 结果报告（3coding-visual）
│   ├── DRAWIO_REPORT.md             # 3: 非数据图说明（4drawio）
│   ├── VERIFY_REPORT.md             # 5: 验收报告（6verity）
│   ├── REVIEW_LOG.md                # 用户审核与版本记录
│   ├── LITERATURE_REPORT.md          # 文献与建模主张的支持关系
│   ├── STATE.md                      # 当前状态、版本与恢复索引
│   ├── models/                       # 按问保存模型记录 qN.md
│   └── PAPER_NOTES.md               # 符号、术语、章节与结果版本映射
├── code/                        # 2: 代码（3coding-visual）
│   ├── problem1.py
│   ├── problem2.py
│   ├── problem3.py               # 问题的数量应该更具题目动态调整
│   ├── ... 
│   └── utils.py
├── results/                     # 2: 结果记录（3coding-visual）
├── figures/                     # 2+3: 所有图表（3coding-visual + 4drawio）
│   ├── STYLE.md                 # 生成初稿后按反馈积累风格
│   ├── *.pdf                    #     数据图 + 非数据图 PDF
│   ├── *.drawio                 #     非数据图源文件
├── paper/                       # 4: 论文（5writing）
│   ├── main.typ / main.tex      #     论文主文件（按用户选择的引擎）
│   ├── drafts/                  #     引擎未确定时逐问积累 Markdown
│   └── sections/                #     各节文件（.typ 或 .tex）
```

方案必须明确每个阶段由哪个下游 skill 负责，以及该阶段应产出什么文件。

### 3. 生成待办

将 `todo.md` 写成阶段性 checklist，格式如下：

```markdown
# 待办事项

- [ ] 整体路线已审核
- [ ] 当前问方案已审核（逐问展开）
- [ ] 当前问稳健方案已运行、验证，基线结果已审核
- [ ] 当前问探索已按授权完成或不开展，最终结果已审核
- [ ] 当前问段落已积累、后问依赖已更新
- [ ] 全文已整合
- [ ] 最终验收完成
```

按实际问题数展开逐问条目，记录当前状态及待审对象。生成了文件不等于审核完成；状态必须能对应审核记录。

### 4. 按审核状态调用阶段

以下是职责表，不是一次执行完所有问题的流水线。整体分析后暂停审核；每次只进入当前问的方案、实现、结果审核和章节积累。当前问最终结果通过后才能进入下一问；全部问题通过后才做全文整合与最终验收。

| 阶段 | Skill | 作用 | 主要产物 |
| --- | --- | --- | --- |
| 赛题分析与建模设计 | `2analysis-modeling` | 先生成整体路线供审核，再逐问形成稳健与探索方案供审核。 | `ANALYSIS_MODELING_REPORT.md` |
| 编程实现和图表生成 | `3coding-visual` | 实现可复现代码，运行实验，生成结果表和多种多样的图表。 | `code/`, `results/` ,  `RESULTS_REPORT.md`, `figures/图表` |
| 流程与架构图绘制 | `4drawio` | 在论文确实需要时，绘制方法流程图、架构图和非数据型概念图。 | `figures/*.drawio`, `figures/*.pdf`, `DRAWIO_REPORT.md` |
| 竞赛论文撰写 | `5writing` | 每问最终结果通过后积累段落，最后统一全文与图表。 | `paper/`, `PAPER_NOTES.md` |
| 验证和验收 | `6verity` | 检查可复现性、一致性、产物完整性、格式规范和提交就绪状态。 | `VERIFY_REPORT.md` |

## 阶段边界

- `3coding-visual` 负责生成所有依赖计算结果或实验输出的数据图表。
- `4drawio` 只负责概念图、算法流程图、架构图、路线图等非数据型图示。
- 不要让 `4drawio` 重复绘制 `3coding-visual` 已经生成的统计图或数据图。
- `5writing` 负责决定图表在论文中的位置，并按所选引擎写入图表代码：
  - Typst：`#figure(image("../../figures/xxx.pdf", width: 85%), caption: [...])`
  - LaTeX（从 `paper/` 编译）：`\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{../figures/xxx.pdf}\caption{...}\label{fig:xxx}\end{figure}`
- 不要让 `5writing` 编造数值结论。论文中的数值必须来自 `RESULTS_REPORT.md`、结果表或已生成图表的数据。
