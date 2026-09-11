# 论文笔记

- 引擎：未定；逐问先写 `paper/drafts/`。
- 问题一方法口径（求解前）：主求解为节点有限体积 + BDF；温度为 Bessel–Duhamel 精确核验；水分为变 \(D(C)\) 数值解，冻结 \(D\) 只核验离散，\(D\) 变幅事后决定能否佐证。
- 草稿：`paper/drafts/problem1_solving_outline.md`（写法与结构），`paper/drafts/problem1_solver.md`（有限体积与 BDF 细推导）。
- 解析温度推导与用户整理的分离变量链条一致；\(A_n\) 两种写法等价。
- 问题一结果：`q1-baseline-v1` 待审，见 `reports/RESULTS_REPORT.md`。方法草稿可迁入正文，表1–2数字须等结果批准。
- 对应模型记录：`reports/models/q1.md`，版本 `q1-plan-v1`。
