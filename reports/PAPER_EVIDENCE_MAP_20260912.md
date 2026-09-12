# 论文证据映射（2026-09-12）

写作授权：用户要求整体查看当前工作并根据已建立模型与公式推导写成国赛论文，故恢复全文写作。本文不自动将历史结果采纳状态改成 APPROVED。

| ID | 来源（相对项目根） | 层级 | 支持内容 | 不能支持的内容 | 正文章节 |
|---|---|---|---|---|---|
| E1 | data/A_text.txt；data/A.pdf；data/附件 | L1 原题 | 四问任务、物性系数、输出规格 | 后4小时真实环境；真实三维预测误差 | 1至6 |
| E2 | reports/models/q1.md；paper/drafts/problem1_solver.md；code/radial_fvm.py；code/q1_analytic.py | L1 用户模型及代码 | 环层推导、Robin、中心系数4、Bessel与Duhamel | 真实非线性水分的解析解 | 3 |
| E3 | reports/models/q2.md；code/appendix3.py；code/radial_coupled.py | L1 | 有效热容量、散度、局部物性双向耦合 | 完整多相能量守恒；历史线性插值与旧网格不可作为现行描述 | 4 |
| E4 | reports/models/q3.md；code/q3_closeout.py；code/q3_balance.py | L1 | 全域最大值事件、严格裕量、变热容量收支 | 最大值的连续时空严格误差界 | 5、7 |
| E5 | reports/models/q4-model-v1.md；code/problem4.py；code/verify_q4_results.py | L1 | 比例收缩、干基守恒、材料坐标、动态表面 | 半径数据唯一确定内部速度；收缩单因素因果效应 | 6、8 |
| E6 | results/q1_solution.npz、q2_solution.npz、q3_solution.npz、q4_solution.npz | L1 数组 | 六张题定表与正文数值 | 尚未进行的参数/环境敏感性实验 | 3至6 |
| E7 | results/q1_validation.json、q2_validation.json、q3_validation.json、q4_validation.json；reports/Q12_CLOSEOUT_REPORT.md、Q3_VERIFY_REPORT.md、Q4_VERIFY_REPORT.md | L1 既有运行记录 | 空间/时间加密、独立对照、收支、文件核验 | 本轮已重跑所有PDE；实物实验验证 | 7 |
| E8 | figures/q1_*.pdf、q2_*.pdf、q3_*.pdf、q4_*.pdf | L1 已生成图 | 对应源结果的剖面与历程 | 未完成的对照图与新实验 | 1、3至6 |
| E9 | reports/PAPER_CITATION_AUDIT.md所列出版社、机构与官方文档 | L2/L3及官方算法说明 | 圆柱/移动边界研究方向、PCHIP和BDF性质 | 文献为本题参数或预测精度背书 | 方法背景与数值方法 |
| E10 | 官网2026论文格式、2026 AI规定 | L1 官网文本 | 摘要一页、无目录、正文30页、完整源程序附录、匿名、AI说明 | 地方赛区未提供的附加要求 | 排版与交付说明 |

主文本排除内容：把粗41节点222.7 h作为当前答案；未实施的扩散势算法、自适应网格、参数扰动、二维端面和潜热改进；将收缩导致时间缩短11.11%作为单因素结论；将技术检查通过直接表述为实测验证。

表格由 code/build_guosai_paper.py 从未舍入NPZ自动生成，来源哈希见 paper/guosai2026/qa/table_sources.json。物性敏感性只作既有公式求导与条件性代入，不声称开展了新的参数扰动实验。
