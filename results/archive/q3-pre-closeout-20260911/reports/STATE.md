# 当前状态索引

## 最新：第四问基线已求解并核验（2026-09-11）

- 用户在已选模型基础上询问是否可开始求解，本轮继续q4-model-v1并完成q4-baseline-v1；数值及导出技术PASS，结果采纳PENDING。
- 生产G8：临界51.08712298h；严格报告51.0877h，最大含水率0.1499989333，事件最大值在中心，表面半径1.2cm；无半径外推。
- G8/G16时差0.113486s，时间收紧差0.002883s，表6四位一致；质量收支、同时间全场/输出比较及Excel全量核对通过。热验证仅指有效方程残差及收敛，不是完整多相能量守恒。
- 入口reports/Q4_VERIFY_REPORT.md；模型reports/models/q4-model-v1.md；表6 reports/Q4_TABLE6.md；Excel results/result4.xlsx；源解及检查results/q4_solution.npz、q4_validation.json、q4_delivery_validation.json。
- 本轮未变更第三问结果及其验收状态，论文写作仍暂停，可选改进未开展。

## 补充：第三问9天差异已独立定位（2026-09-11）

- 同模型、同时间容差，仅改变空间网格：均匀41/81/161节点分别9.28064/3.63450/2.51758天，表面加密G4为2.39472天；主要差异来自表面强非线性扩散区域的空间离散。
- 证据入口：`reports/Q3_TIME_DISCREPANCY.md`、`results/diagnostics/q3_time_discrepancy/audit.json`。原生产代码和Q3源解未改，论文仍暂停。
- 此诊断不等于完整验收：热收支门禁仍失败；后续需复核守恒积分、统一失败阻断、修正事件误差阈值命名及同一时刻的含水率误差/严格阈值裕量。

## 最新：第三问基线 q3-baseline-v1 已算出，待审（2026-09-11）

- 用户授权实现并求解第三问基线；论文仍暂停，创新方法仍暂缓。
- 正式网格 G4：\(t_*=57.473174\,\mathrm{h}\)，严格报告 \(t_{\mathrm{rep}}=57.473333\,\mathrm{h}\)，最大值在中心。约 2.39 天。G2 相差 9.65 s，时间收紧几乎为 0。
- 均匀 41 点探针的 222.7 h 是粗网格把干壳通量掐死，不作答。
- 材料：`reports/Q3_VERIFY_REPORT.md`、`results/result3.xlsx`、`results/q3_validation.json`、`figures/q3_*.pdf`。状态 PENDING。
- 热收支相对残差 \(1.06\times10^{-4}\)，略超预拟 \(10^{-4}\)；硬条件已通过。

## 已有决定：第四问基础模型已接受并整理（2026-09-11）

- 用户回复“行就这样把，整理一下第四问的建模”；当前采用q4-model-v1，完整材料reports/models/q4-model-v1.md，索引reports/models/q4.md。
- 采用比例径向收缩、固定材料坐标、附录4等效热湿模型及全域事件判据，继承q2-closeout-v1框架和q3-model-v1环境口径。
- 密度按本次解释作为有效热容量系数使用，保留严格湿密度与给定几何的兼容性限制；不再作为当前模型采纳的待决项。
- 本轮只整理模型与后续工作，无求解、时长或result4；生产数值配置待落实，若超过72h仍未达标需补充半径延续假设。第三问方向保留，论文写作仍暂停。

## 已有决定：第三问基础模型已确定，论文写作暂停（2026-09-11）

- 当前模型q3-model-v1及后续工作已按用户“行记住这个模型建立的以及后续工作”保存至reports/models/q3.md顶部。
- 第三问采用附录3固定径向热湿耦合模型；前4小时附件1/PCHIP，之后50°C、0.05 kg/kg；原初值独立积分。
- 判据为全部内部节点最大含水率低于0.15；有限体积+BDF联合推进，连续插值与带括号求根定位事件，另处理严格不等式和时空收敛。
- 后续：落实基线数值配置→求解全过程→验证达标时间与输出场→表5/result3.xlsx及证据归档；创新选型暂缓。该条为当时“只记录、未运行”的快照；求解结果见顶部 q3-baseline-v1。
- 用户要求“论文先不要写，我有我写的想法”：写作暂停，不续写或合并已有稿件；保留已有代码、结果及草稿。

第三问求解现状已改由顶部「q3-baseline-v1」条目记录，不再停留在“尚无时长”。

## 2026-09-11：前两问技术收尾完成

- 用户授权：“你帮我收尾一下并告诉我做了什么”，执行范围为前两问修复、复算、核验、章节草稿及状态整理。
- 当前交付：`q1-closeout-v1`、`q2-closeout-v1`；技术核验PASS（已选等效模型与明确数值阈值下），结果采纳PENDING，不自动登记用户已批准新版本。
- 前两问所有答卷数值与收尾前一致。修复发布门禁、参考级数收敛、第一问通量积分、第二问图例和内部场归档。
- 入口：`reports/Q12_CLOSEOUT_REPORT.md`；证据`results/verification/closeout/`；Excel位于`results/result1.xlsx`与`result2.xlsx`。
- 论文采用已选LaTeX/xelatex；前两问已积累到`paper/closeout/sections/5_problem1.tex`、`6_problem2.tex`，单独预览`paper/q12_closeout.pdf`。全文仍未完成。
- 第一问旧v1、v2及第二问旧v1为历史版本；数值未失效，当前代码及验证以closeout版本为准。原快照及SHA256见`results/archive/pre-closeout-20260911/`。
- 第三问：`q3-model-v1` 已实施 `q3-baseline-v1`，见顶部最新条目；结果待审。
- 第四问：当前已实施`q4-baseline-v1`，见顶部最新结果；早期“未求解”描述为历史时点。
- 下一步：审阅第三、四问各自基线及其验证范围；论文写作仍暂停。前问采纳记录不因第四问通过技术检查自动改写。

## 偏好、模型与历史入口

- 只做A题《药材的烘干问题》，四问，中文国赛论文；整体路线`A-route-v1`已批准。
- 已批准第一问方案`q1-plan-v1`及PCHIP修订；第二问`q2-plan-v2`，PCHIP、一维、不做二维或潜热探索。
- 第二问从原初值独立计算，不使用第一问末态；第三问不能从已舍入Excel恢复内部状态。
- 方案详情：`reports/models/q1.md`至`q4.md`；决定原文：`reports/REVIEW_LOG.md`。
- 文献：`reports/LITERATURE_REPORT.md`；论文来源：`reports/PAPER_NOTES.md`；图形风格：`figures/STYLE.md`。
- 完整旧状态记录保存在`reports/archive/pre-closeout-20260911/STATE.md`，其中旧“当前”标签均为历史时点。

- 并行写作记录补充：工作区另有整体正文及Overleaf包，详见`reports/PAPER_NOTES.md`保留的其他任务记录。本轮验收只覆盖独立closeout章节与前两问结果，不覆盖该并行全文。
