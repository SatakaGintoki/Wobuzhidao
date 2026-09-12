# 论文独立引文核查

核查日期：2026-09-12。核查者以独立上下文仅接收拟用原句及参考文献，按 paper-writer 的 verification-ladder 执行实际联网检索。每条均执行完整题名、作者/责任者＋关键词＋年份、核心关键词三类查询。仅采用出版商、作者机构和 SciPy 官方文档作为判定依据。未修改论文。

## 结论

五条引文均真实，未发现题名、作者顺序、出版年、期刊卷期页码或 DOI 的实质错误。前三条可支持所给背景表述。第 4、5 条的算法性质已核实；“本文实际采用什么设置”仍应由论文作者对照代码确认，本报告不以文献代替实现核查。没有 NOT_FOUND 或 METADATA_MISMATCH 条目。原句涉及本题半径输入及参数选择的部分属于作者自身方法陈述，不是所引论文的结论。

## 1. Hussain 与 Dincer（2003）

**状态：VERIFIED（书目信息及限定范围内的背景表述）。**

准确条目：Hussain M M, Dincer I. Two-dimensional heat and moisture transfer analysis of a cylindrical moist object subjected to drying: A finite-difference approach[J]. International Journal of Heat and Mass Transfer, 2003, 46(21): 4033–4039. DOI: 10.1016/S0017-9310(03)00229-1.

依据：[Elsevier 原论文页面](https://www.sciencedirect.com/science/article/pii/S0017931003002291)的实际检索返回提供题名、卷期、年月、页码、DOI 和摘要，摘要明确研究圆柱湿物体二维热湿传递、采用显式有限差分并计算时空温湿分布；[Elsevier 元数据接口](https://api.elsevier.com/content/article/pii/S0017931003002291)实际请求返回匹配题名、DOI、期刊及 2003 年 10 月。出版商页面直接打开遇到 403，因此没有据此声称全文核实。作者名与顺序另由 Dincer 本人参与撰写、Wiley 出版的[书章参考文献](https://onlinelibrary.wiley.com/doi/10.1002/9781118534892.ch6)核对，其参考文献明确列出 Hussain M.M., Dincer I. 2003b 及本题名、卷号和页码。

原句可以保留。“为本题保留空间分布提供方法背景”属于本研究对既有工作的定位，不能扩展成该文证明本题所用材料参数或模型假设适用。

建议原句：Hussain 和 Dincer 研究了圆柱湿物体干燥中的二维热湿传递问题，为本文描述内部温度与含水率的空间分布提供了方法背景。

三类查询：

- `"Two-dimensional heat and moisture transfer analysis of a cylindrical moist object subjected to drying"`
- `Hussain Dincer 2003 cylindrical moist drying finite difference`
- `cylindrical moist object heat moisture drying finite difference 4033 4039`

## 2. Kaya 等（2007）

**状态：VERIFIED。**

准确条目：Kaya A, Aydin O, Dincer I. Numerical modeling of forced-convection drying of cylindrical moist objects[J]. Numerical Heat Transfer, Part A: Applications, 2007, 51(9): 843–854. DOI: 10.1080/10407780601112753.

依据：作者机构 Karadeniz Technical University 的[成果记录](https://avesis.ktu.edu.tr/yayin/835ff2e9-e0b5-4c67-babf-78bb8903a78e/numerical-modeling-of-forced-convection-drying-of-cylindrical-moist-objects)列明全部书目字段，并提供摘要；Dincer 的 [Wiley 书章参考文献](https://onlinelibrary.wiley.com/doi/10.1002/9781118534892.ch6)亦列明匹配条目。已读机构元数据与摘要，未声称读取全文。

原句在引用层面成立，可以保留：Kaya 等讨论了圆柱湿物体强制对流干燥的数值建模。

三类查询：

- `"Numerical modeling of forced-convection drying of cylindrical moist objects"`
- `Kaya Aydin Dincer 2007 cylindrical moist numerical drying`
- `cylindrical forced convection drying 843 854 10407780601112753`

## 3. Brasiello 等（2021）

**状态：VERIFIED（文献部分由摘要支持；本文输入与参数选择须由作者材料支持）。**

准确条目：Brasiello A, Venditti C, Adrover A. Non-isothermal Moving-boundary Model for Food Drying[J]. Chemical Engineering Transactions, 2021, 87: 193–198. DOI: 10.3303/CET2187033.

完整作者：Antonio Brasiello, Claudia Venditti, Alessandra Adrover。依据：[出版商第 87 卷目录](https://www.cetjournal.it/index.php/cet/issue/view/vol87)、[出版商 PDF 的检索结果](https://www.cetjournal.it/cet/21/87/033.pdf)及作者机构 Sapienza 的[成果记录与摘要](https://iris.uniroma1.it/handle/11573/1571237)。机构摘要明确指出在水分输运方程之外加入考虑热传递、表面蒸发和收缩的热输运方程，足以支持“收缩与传热传质在统一框架内讨论”的温和概括。出版商 PDF 直接打开失败，故这里按“元数据＋摘要核实”记录，未声称全文审阅。

建议拆开归属：Brasiello 等研究了食品干燥的非等温移动边界模型，将收缩及热湿传递纳入同一建模框架。本文采用题目给定的半径轨迹描述收缩，材料参数按本题条件设定。

三类查询：

- `"Non-isothermal Moving-boundary Model for Food Drying"`
- `Brasiello Venditti Adrover 2021 food drying moving boundary`
- `non isothermal moving boundary food drying 193 198`

## 4. SciPy solve_ivp

**状态：VERIFIED（官方 API 算法说明）；本文实现事实不在本次引文核查范围内。**

建议书目：The SciPy community. scipy.integrate.solve_ivp[EB/OL]. SciPy documentation. [2026-09-12]. https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html.

依据：[官方 solve_ivp 文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)。已读 method、rtol/atol、jac 和 jac_sparsity 说明：BDF 是隐式多步变阶方法，阶数 1–5；可接受稀疏雅可比矩阵；jac_sparsity 用于有限差分雅可比估计，给出每行较少非零元的结构可加速计算，且在 jac 非 None 时该参数被忽略；容差控制局部误差估计。网页版权责任者显示 The SciPy community，不应把版权起始年当作发布年；访问日期可明确列出。当前页面版本不等同于项目实际运行版本。

“控制计算规模”较含混，建议改为“降低计算开销”。“局部容差不能替代空间收敛检查”是对时间误差与空间离散误差区别的方法论解释，并非文档原句，可写成本文验证安排。仅在代码确有对应设置和收敛检查时采用以下版本：

半离散系统采用隐式变阶 BDF 方法积分，并向求解器提供雅可比稀疏结构以降低计算开销。时间积分的局部误差由相对、绝对容差控制，空间离散误差则通过网格加密单独检查。

三类查询：

- `"scipy.integrate.solve_ivp" site:docs.scipy.org`
- `SciPy community solve_ivp BDF 2026 site:docs.scipy.org`
- `BDF jac_sparsity rtol atol site:docs.scipy.org`

## 5. SciPy PchipInterpolator

**状态：VERIFIED（官方 API 性质）；本文数据处理事实不在本次引文核查范围内。**

建议书目：The SciPy community. scipy.interpolate.PchipInterpolator[EB/OL]. SciPy documentation. [2026-09-12]. https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html.

依据：[官方 PchipInterpolator 文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html)。已读正文和 Notes：PCHIP 是保形分段三次 Hermite 插值，保持数据单调性、避免不光滑数据产生过冲，一阶导连续，二阶导可在节点跳跃；横坐标须严格递增且不能重复。插值通过给定数据节点，“精确”宜理解为插值条件，而非计算机浮点运算零误差。保形性质限定于数据插值区间，不能据此外推区间也保形。

建议原句：在观测时间范围内，环境与半径数据采用保形分段三次 Hermite 插值，使插值曲线经过观测节点，并保持数据的局部单调性。

三类查询：

- `"scipy.interpolate.PchipInterpolator" site:docs.scipy.org`
- `SciPy community PchipInterpolator 2026 site:docs.scipy.org`
- `PCHIP shape preserving monotonicity interpolation site:docs.scipy.org`

## 交付边界

本报告确认引文真实性、书目信息及文献支持强度，不替代本题数据、代码、参数、模型正确性和数值结果的审查。以上建议措辞均无需加入占位符；按文中要求对照已有代码与本题材料后即可使用。搜索中返回的非官方转载站、商业聚合站和个人上传站未作为判定依据。
