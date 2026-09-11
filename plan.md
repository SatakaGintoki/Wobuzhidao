# 方案

先整体审核，再按当前问调用这些 skill。没有对应批准不得越过审核点。

用户偏好：
- 排版引擎：待正式排版前确定（引擎未定时先积累 Markdown 段落）
- 竞赛类型：全国大学生数学建模竞赛
- 论文语言：中文
- 子问题数量：A题共4问
- 绘图偏好：暂不指定固定配色，先生成初稿，再随结果反馈逐步确定

workflow:
   step      skills
1. 整体路线分析与领域文献检索 - `2analysis-modeling` → 用户审核
2. 当前问详细方案与文献依据 - `2analysis-modeling` → 用户审核
3. 稳健方案求解及图表 - `3coding-visual`、按需 `4drawio` → 用户审核基线结果
4. 已批准的探索 - `3coding-visual` → 用户审核最终结果（不探索则复用基线结果批准）
5. 当前问章节积累 - `5writing` → 更新依赖后回到步骤 2
6. 全部完成后全文整合 - `5writing` → 最终验收 `6verity`

## 阶段职责与产物

| 阶段 | Skill | 作用 | 主要产物 |
| --- | --- | --- | --- |
| 赛题分析与建模设计 | `2analysis-modeling` | 先生成整体路线供审核，再逐问形成稳健与探索方案供审核。 | `reports/ANALYSIS_MODELING_REPORT.md` |
| 编程实现和图表生成 | `3coding-visual` | 实现可复现代码，运行实验，生成结果表和数据图表。 | `code/`、`results/`、`reports/RESULTS_REPORT.md`、`figures/` |
| 流程与架构图绘制 | `4drawio` | 仅在论文确实需要时绘制非数据型概念图。 | `figures/*.drawio`、`figures/*.pdf`、`reports/DRAWIO_REPORT.md` |
| 竞赛论文撰写 | `5writing` | 每问最终结果通过后积累段落，最后统一全文与图表。 | `paper/`、`reports/PAPER_NOTES.md` |
| 验证和验收 | `6verity` | 检查可复现性、一致性、产物完整性、格式规范和提交就绪状态。 | `reports/VERIFY_REPORT.md` |

## 环境

本轮只读附件审计使用宿主Python：`C:/Users/chens/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`，已实际运行openpyxl、numpy、pypdfium2读取与渲染。未安装新依赖。数值求解环境在逐问实施时按需检查。

## 风险控制

- A题题面与附件均已存在并核查；当前只做数据审计和整体路线，尚未实施PDE求解。
- 生成文件不等于审核完成；状态以 `reports/REVIEW_LOG.md` 与 `reports/STATE.md` 为准。
- 论文数值只能来自已审核结果，不得编造。

## 当前整体路线 A-route-v1（2026-09-10，已通过）

本项目只处理工作区A题《药材的烘干问题》。 

建模方向：第1问固定圆柱径向热湿传递；第2问统一采用附录3从t=0重算；第3问沿用第2问模型定位全域含水率阈值事件；第4问采用附件2的R(t)和附录4重新构建变域模型。候选求解方法是有限体积与隐式时间推进。

整体材料：`reports/ANALYSIS_MODELING_REPORT.md`；文献及限制：`reports/LITERATURE_REPORT.md`；数据证据：`reports/A_INPUT_AUDIT.json`。

主要风险：扩散系数指数误读、4 h后环境外推、端面近似、空气与固体水分量的不同干基、潜热简化、收缩中的材料运动与守恒。详细说明与验证办法均随路线提交。

用户已明确“就做A题了”，随后针对整体路线确认回复“来吧”。第1问方案 `q1-plan-v1` 已于2026-09-11由用户确认：主求解为节点有限体积+BDF，温度用Bessel–Duhamel核验，水分保留D(C)。正在用 `D:/python/python.exe` 实施基线及必要验证。后续仍逐问求解、验证、积累论文。

补充数值环境：宿主Python缺少SciPy，已验证现有 `D:/python/python.exe` 可用Python3.14.6、NumPy2.5.1、SciPy1.18.0及稀疏BDF工具。无需安装；数值计算使用该解释器。
