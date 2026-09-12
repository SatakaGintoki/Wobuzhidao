# 基线论文证据映射

| ID | 来源 | 级别 | 可支持内容 | 不可支持内容 | 计划用途 | 风险 |
|---|---|---|---|---|---|---|
| E1 | `data/A_text.txt` | L1 | 题面、四问任务、初值、几何、附录物性公式、输出要求 | 附件中未给出的物理机制 | 问题重述、模型参数 | OCR 公式以现有模型报告复核 |
| E2 | `reports/STATE.md` | L1 | 四问当前版本、技术状态、第三问和第四问严格报告时刻 | 用户已正式采纳、真实实验精度 | 摘要、结论、结果状态 | 当前结果仍为 PENDING |
| E3 | `reports/RESULTS_REPORT.md`、`results/q1_table_temperature.csv`、`results/q1_table_moisture.csv` | L1 | 第一问表格、1800 s 结果、网格和时间核验 | 真实药材实验误差 | 问题一、数值检验 | 仅为选定模型的数值预测 |
| E4 | `reports/RESULTS_REPORT.md`、`results/q2_table_temperature.csv`、`results/q2_table_moisture.csv` | L1 | 第二问表格、3 h 结果、耦合模型核验 | 二维端面影响大小 | 问题二、数值检验 | 一维径向近似未做二维对照 |
| E5 | `reports/Q3_VERIFY_REPORT.md`、`results/q3_validation.json`、`results/q3_table_moisture.csv` | L1 | 第三问 57.4731 h、表5、收支与加密结果 | 严格 PDE 误差界、实测准确度 | 问题三、敏感性 | 经验裕量不是严格误差界 |
| E6 | `reports/Q4_VERIFY_REPORT.md`、`reports/Q4_TABLE6.md`、`results/q4_validation.json` | L1 | 第四问 51.0877 h、表6、收缩域模型核验 | 收缩的独立实验验证、物性与几何效应的因果拆分 | 问题四、敏感性 | 半径轨迹是模型输入而非验证数据 |
| E7 | `paper/sections/5_problem1.tex`、`paper/sections/6_problem2.tex`、`reports/models/q3.md`、`reports/models/q4-model-v1.md` | L1 | 控制方程、初边值条件、材料坐标、离散方法 | 未实施的潜热或二维扩展 | 方法章节 | 主论文旧稿的第三、四问结果占位不可沿用 |
| E8 | Luikov (1975), DOI 10.1016/0017-9310(75)90002-2 | L2 | 多孔介质热湿传递方程的研究背景 | 本题参数与计算结果 | 引言、模型依据 | 摘要级证据 |
| E9 | Hussain and Dincer (2003), DOI 10.1016/S0017-9310(03)00229-1 | L2 | 圆柱湿物料二维热湿数值分析属于既有研究路线 | 本文一维模型精度、具体参数可迁移性 | 引言、模型评价 | 摘要级证据 |
| E10 | Kaya, Aydin, and Dincer (2007), DOI 10.1080/10407780601112753 | L2 | 圆柱湿物料强制对流干燥的隐式数值建模 | 本题边界系数与真实药材适用性 | 引言、方法背景 | 摘要级证据 |
| E11 | da Silva, e Silva, and Gama (2014), DOI 10.1016/j.jfoodeng.2014.05.010 | L2 | 变物性、收缩、第三类边界与有限体积用于圆柱干燥建模 | 本题药材物性与实验吻合 | 引言、方法背景 | 摘要级证据 |
| E12 | Adrover, Brasiello, and Ponso (2019), DOI 10.1016/j.jfoodeng.2018.09.018 | L2 | 干燥收缩可用移动边界模型描述 | 本文均匀比例收缩已由内部变形实验证实 | 问题四、模型评价 | 摘要级证据 |

