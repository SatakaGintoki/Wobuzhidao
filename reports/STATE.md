# 状态索引

## 最新审核：第二问（2026-09-11）

- 用户要求使用skill审核第二问结果；已按本地6verity完成。报告：`reports/Q2_VERIFY_REPORT.md`。
- `q2-baseline-v1`数值核验PASS：完整3小时G4精确复现、时间加密及G8空间加密，论文60值四位不变。交付流程FAIL：导出门禁失败仍写正式路径；另有冻结D参考截断不足、温度剖面图例遮线与内部场归档问题。
- 新证据：`results/verification/q2/`；脚本`code/verify_q2_results.py`。原生产代码及Excel/NPZ/CSV/PDF未改；用户采纳状态仍为PENDING。
- 后续：处理报告列明的交付与验证问题；不由本次审核自动启动第三、四问，也不把第一问待审结果改记为通过。

## 当前状态：第二问结果待审（2026-09-11）

- 第二问基线 `q2-baseline-v1` **PENDING**。方案 `q2-plan-v2` 已按用户选择批准（PCHIP，一维）。
- 第一问 `q1-baseline-v2` 仍待审；第二问未使用其末态。
- 第三、四问仅为既有讨论，本轮未求解。
- 下一步：用户审核 `q2-baseline-v1` 是否作为第2问答卷。
- 复现：`D:/python/python.exe code/problem2.py`

## 当前讨论：第四问（2026-09-11）

- 用户要求查看文件夹、使用skill讨论第四问。已读取本地2analysis-modeling、前问模型、题面，并只读核查附件2及result4原模板。
- 新材料：`reports/models/q4.md`，`q4-discussion-v1`，PENDING讨论稿。方向为附件2给定R(t)、均匀比例径向收缩、材料坐标xi=r/R、附录4热湿有效模型、全域0.15阈值与动态表面输出。
- 明确限制：附录rho若同时解释为真实湿密度，与固定长度、均匀收缩和干物质守恒可能过约束；建议先讨论有效热容量解释。详见模型第4节，不将其说成严格多相守恒模型。
- 本轮未求解PDE或生成result4；不依赖第二、三问数值。第三问创新选型暂缓状态和前问决定均保留。下一步继续讨论第四问的收缩及密度闭合。

## 当前讨论：第三问（2026-09-11）

- 用户要求查看工作区并使用skill讨论第三问数学建模。已读本地2analysis-modeling及共享规范、题目和第二问当前决定。
- 当前材料：`reports/models/q3.md`，`q3-discussion-v1`，PENDING讨论建议；不是已采纳模型或求解结果。
- 建议沿用q2-model-v1，从原初值使用附录3；补充4小时后环境延续、全域最大含水率阈值、严格小于的报告口径及长时空间近似限制。
- 第二问尚无已验证数值，但本次模型讨论不依赖其数值末态。未编程、运行PDE、验证或生成结果图表；下方第二问决定与第一问历史状态保留。
- 下一步：按用户反馈继续讨论第三问；50°C/0.05后期边界与具体判据尚待采纳，不能默认启动实施。

## 当前状态（2026-09-11）

- 第一问结果已按用户要求改为 PCHIP 并加密重跑，版本 `q1-baseline-v2`，**待审**。旧版 `q1-baseline-v1` 为 `STALE`，归档于 `results/archive/q1-baseline-v1/`。
- 第二问模型方向仍为暂定 `q2-model-v1`（见 `reports/models/q2.md`）：第一问论文版框架＋附录3变物性，不考虑蒸发吸热。仅讨论/记录，**未授权编程或运行**。
- 第二问不使用第一问末态作初值。
- 已批准：选题A；`A-route-v1`；`q1-plan-v1`；插值修订 `q1-interp-pchip`。
- 下一步：用户审核 `q1-baseline-v2` 是否作为第1问答卷。通过前不把数字写入正式论文正文，不自动开始第2问求解。
- 审核记录：`reports/REVIEW_LOG.md`；结果报告：`reports/RESULTS_REPORT.md`
- 复现：`D:/python/python.exe code/problem1.py`

## 以下为第一问交接前的历史状态

- 新对话交接入口：`reports/HANDOFF_TO_Q2.md`。用户计划在新对话承接并处理第二问；本文以下部分保留第一问历史状态。第二问尚未启动，接续时先读交接记录和新对话用户指令。

- 当前问/阶段：第1问结果技术验收未通过，见`reports/VERIFY_REPORT.md`（2026-09-11）
- 待修正对象：`q1-baseline-v1`的水分空间精度与发布前收敛门禁；文件格式、数值来源、温度解析检验通过。原结果保留为候选，未验收为最终交付
- 已批准版本：选题A；整体路线 `A-route-v1`；第1问方案 `q1-plan-v1`
- 审核记录：`reports/REVIEW_LOG.md`
- 当前工作稿：`reports/RESULTS_REPORT.md`；模型 `reports/models/q1.md`；论文写法 `paper/drafts/problem1_solving_outline.md`
- 最新正文整理：`paper/drafts/problem1_model_consolidated.md`（已按用户最新权衡请求收敛：正文保留题给参数闭合的第一问模型，删除含未知水活度与β的扩展方程；潜热量级及局限保留在模型评价）；交付核查见`reports/Q1_PAPER_MODEL_DELIVERY.md`
- 依赖关系：附件1/附录2；不依赖前问数值
- 待定项：用户新提出参考da Silva2014改进模型；需评估表面潜热与界面水分基准后再决定正式采用何种温度结果。原基线仍保留为无潜热对照
- 探索授权：用户本轮要求评估是否升级主模型；已完成仅用于选型的限定温度诊断，未批准正式替换主模型或展开后问
- 下一步：按`reports/VERIFY_REPORT.md`改进既定模型的水分空间收敛，验证后更新结果；本轮未修改主模型或覆盖结果。若用户在新对话进入第二问，其独立建模不使用第一问末态
- 全局偏好：见 `plan.md`
- 文献记录：`reports/LITERATURE_REPORT.md`
- 绘图风格：`figures/STYLE.md`（初稿）

- 本问关键口径：不显式潜热；变 \(D(C)\) 为水分答卷；Bessel 核验温度；冻结 \(D\) 只核验离散
- 数值环境：`D:/python/python.exe`
- 复现：`D:/python/python.exe code/problem1.py`

- 2026-09-11新增证据：已读用户论文`C:/Users/chens/Desktop/国赛论文/1.pdf`，登记L13；其潜热删项实验与本题能量量级审查均支持认真考虑潜热。
- 同日用户提供 Hussain & Dincer (2003) 全文，L02 升为全文核实：同类圆柱热湿差分旁证；短粗样品上的二维不能推出本题第1问改二维；显式差分与文中 \(D(T)\) 不搬入主求解。
- 本轮新增产物：`reports/Q1_REFERENCE_AND_LATENT_REVIEW.md`、`reports/Q1_LATENT_ENERGY_AUDIT.json`；后处理脚本`code/assess_q1_latent.py`。只读取既有N=640结果，未运行含潜热PDE。
- 量级审查限制：假设820为初始湿密度，Lv≈2.4MJ/kg；30分钟隐含潜热约44.66kJ，原显热约4.80kJ，不能据此直接给出改进温度。原基线早期水分网格未达预拟精度的限制继续保留。

- 最新选型结论（2026-09-11）：见`reports/Q1_MAIN_MODEL_DECISION.md`。仅加潜热的M1在保留原失水规律下，1800秒Ts≈12.41°C；若Ca为常规空气含湿量、p=101325Pa，则露点≈33.28°C，持续蒸发方向不相容。暂不升为主模型，需先解决界面水分势与系数基准。
- 本次限定诊断：`code/probe_q1_latent_upgrade.py`及`results/diagnostics/q1_latent_upgrade/`，共5个温度试算，原水分场与正式result1未改。上述“未运行含潜热PDE”是上一轮历史记录；本轮已有温度诊断，但不是正式采纳结果。

### 2026-09-11增量：第三问求解创新候选

用户要求讨论第三问求解方法的创新空间。新增q3-innovation-candidate-v1（PENDING），见reports/models/q3.md第8节：达标时间误差估计、目标导向自适应及可选伴随加权残差；原物理模型不变。已查阅两篇首次阈值时间误差研究的作者摘要页，未读全文、未实验。不将候选或用户追问视为方案采纳/实施授权。

### 2026-09-11：候选方法汇总 q3-method-menu-v1

用户要求整理可能的建模方法。材料见reports/Q3_METHOD_COMPARISON.md：A全耦合基准、B达标时间目标自适应、C热湿时间尺度分离、D Kirchhoff扩散势改写、E轴对称二维、F边界情景敏感性。首选讨论组合A+B+F，其他按收益和适用性探索。全部为PENDING候选，未采纳、未编程运行。

### 2026-09-11：第三问改进选型暂缓

用户原话：“到时候再考虑吧，我们的skill是不是也是整体建立基础模型然后再进行看一下哪里可以优化改进”。决定：上述第三问创新候选暂缓选择和开展，保留讨论材料。此决定不表示基础模型已最终批准，也不授权编程或求解。当前继续以基础框架讨论为主，后续依据基线的具体不足再评估改进。已核对2analysis-modeling及review_workflow：先整体路线、再逐问稳健方案；候选可提前提出，实际探索在有效基线及对应授权基础上进行，不强求每问创新。
