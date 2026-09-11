# 当前状态索引

## 2026-09-11：前两问技术收尾完成

- 用户授权：“你帮我收尾一下并告诉我做了什么”，执行范围为前两问修复、复算、核验、章节草稿及状态整理。
- 当前交付：`q1-closeout-v1`、`q2-closeout-v1`；技术核验PASS（已选等效模型与明确数值阈值下），结果采纳PENDING，不自动登记用户已批准新版本。
- 前两问所有答卷数值与收尾前一致。修复发布门禁、参考级数收敛、第一问通量积分、第二问图例和内部场归档。
- 入口：`reports/Q12_CLOSEOUT_REPORT.md`；证据`results/verification/closeout/`；Excel位于`results/result1.xlsx`与`result2.xlsx`。
- 论文采用已选LaTeX/xelatex；前两问已积累到`paper/closeout/sections/5_problem1.tex`、`6_problem2.tex`，单独预览`paper/q12_closeout.pdf`。全文仍未完成。
- 第一问旧v1、v2及第二问旧v1为历史版本；数值未失效，当前代码及验证以closeout版本为准。原快照及SHA256见`results/archive/pre-closeout-20260911/`。
- 第三问：`q3-discussion-v1`，后期环境和实施方案未定，创新选型暂缓；无求解结果。
- 第四问：`q4-discussion-v1`，收缩运动与经验密度解释未闭合；无求解结果。
- 下一步：审阅前两问交付，随后明确第三问实施方案。本轮没有开启第三、四问求解。

## 偏好、模型与历史入口

- 只做A题《药材的烘干问题》，四问，中文国赛论文；整体路线`A-route-v1`已批准。
- 已批准第一问方案`q1-plan-v1`及PCHIP修订；第二问`q2-plan-v2`，PCHIP、一维、不做二维或潜热探索。
- 第二问从原初值独立计算，不使用第一问末态；第三问不能从已舍入Excel恢复内部状态。
- 方案详情：`reports/models/q1.md`至`q4.md`；决定原文：`reports/REVIEW_LOG.md`。
- 文献：`reports/LITERATURE_REPORT.md`；论文来源：`reports/PAPER_NOTES.md`；图形风格：`figures/STYLE.md`。
- 完整旧状态记录保存在`reports/archive/pre-closeout-20260911/STATE.md`，其中旧“当前”标签均为历史时点。

- 并行写作记录补充：工作区另有整体正文及Overleaf包，详见`reports/PAPER_NOTES.md`保留的其他任务记录。本轮验收只覆盖独立closeout章节与前两问结果，不覆盖该并行全文。
