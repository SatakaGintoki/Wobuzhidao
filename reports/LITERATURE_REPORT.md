# 文献报告

检索日期：2026-09-10。本报告仅服务A题《药材的烘干问题》的整体路线与后续逐问建模。尚未把公式迁入数值求解。核实口径：能打开的摘要/官方页面/可下载全文按实际读到的内容记录；搜索摘要里未核到的数值不引用。

检索词（中英交叉）：
- Luikov heat mass transfer drying cylinder；food drying shrinkage moving boundary；Kaya Aydin Dincer cylindrical moist objects；Hussain Dincer 2003 finite difference

## 来源登记

### L01
- 身份：A. V. Luikov. Systems of differential equations of heat and mass transfer in capillary-porous bodies. *International Journal of Heat and Mass Transfer*, 1975. DOI: 10.1016/0017-9310(75)90002-2
- 核实范围：检索到的综述定位与后续引用链；未通读 1975 全文公式编号。
- 支持内容：毛细多孔体干燥可用温度–湿度耦合传递方程描述，是 A 题热风烘干的经典机理框架。
- 适用与差异：Luikov 含热扩散引起的湿迁移等交叉项；A 题附录已直接给出 ρ、cp、k、D 及对流换热/传质系数，应优先用题面给定物性，而不是把文献交叉项全部搬进来。
- 状态：书目已核对；主张“耦合热质传递适用于干燥”为部分核实。
- 采用决定：若选 A，作为机理背景候选，不作为本题系数来源。

### L02
- 身份：M.M. Hussain, I. Dincer. Two-dimensional heat and moisture transfer analysis of a cylindrical moist object subjected to drying: A finite-difference approach. *International Journal of Heat and Mass Transfer*, 46 (2003) 4033–4039. DOI: 10.1016/S0017-9310(03)00229-1。
- 核实范围：用户提供全文 PDF（7 页），含式(1)–(9)、假设(i)–(vi)、西兰花/苹果算例与中心温湿对照。2026-09-11 由摘要级升级为全文。
- 支持内容：轴对称圆柱 Fourier 导热 + Fick 扩散、侧表面与两端第三类边界、温度依赖的 Arrhenius 型 \(D\)、显式差分。与本题“圆柱内部热湿场 + 对流边界”同属一类。
- 适用与差异：样品短粗（西兰花直径 7 mm、长 20 mm），二维 \((r,z)\) 对其必要；本题 \(L/(2R)=6.25\)，第1问短时更支持径向一维。该文忽略收缩与体积热源、烘房温度恒定、热物性按初值取常；\(D=D_0\exp(-1119/T)\) 且文中未给出 \(D_0\)，不能替换附录 2–4。式(6)中 \(A\) 含 \(\Delta z\) 却作用于 \(i\)、径向几何因子写成 \(0.5j\)（\(j\) 为轴向指标），离散式不宜照抄。显式稳定性 (8)–(9) 不适合本题细网格主求解。
- 状态：全文已读；机理同类已核实；具体差分公式与物性数值不采用。
- 采用决定：作圆柱热湿差分的方法旁证和第3问端面效应的提醒；不改第1问主模型，不搬西兰花/苹果参数，不用它为忽略潜热背书。

### L03
- 身份：A. Adrover, A. Brasiello, G. Ponso. A moving boundary model for food isothermal drying and shrinkage: General setting. *Journal of Food Engineering*, 2019. https://www.sciencedirect.com/science/article/abs/pii/S0260877418304060
- 核实范围：已读出版商摘要：收缩速度与水分扩散通量成比例，半径随含水量变化，适用于圆柱等几何。
- 支持内容：A 题问题 4“水分流失导致尺寸变化、附件 2 给出半径–时间”可用移动边界/变半径网格处理，而不是继续固定 r=2 cm。
- 适用与差异：文献常由湿含量反推收缩；本题半径轨迹已由附件 2 给出，收缩律可降为已知 R(t)，比一般移动边界更简单。
- 状态：摘要级已核实。
- 采用决定：若选 A，问题 4 采用“已知 R(t) 的变域扩散”而非自建完整力学收缩模型。

### L08
- 身份：A. Kaya, O. Aydın, I. Dincer. Numerical modeling of forced-convection drying of cylindrical moist objects. *Numerical Heat Transfer, Part A*, 2007, 51:843–854. DOI: 10.1080/10407780601112753
- 核实范围：已读摘要。隐式差分求解圆柱体内瞬态温度与湿度；对流换热系数约 4.65–59.33 W/(m²·K)，对流传质系数约 3.59×10⁻⁷–4.58×10⁻⁶ m/s。
- 支持内容：A 题附录 2 的 h=25、hm=8×10⁻⁷ 落在该文计算范围内；问题 1–3 的表面第三类边界与该文同类。
- 适用与差异：该文 h、hm 随表面位置变化且用 CFD 求外部流场；本题只给常数，不应再上 Fluent。
- 状态：摘要级已核实。
- 采用决定：若做 A，作边界条件与系数数量级对照，不搬变系数场。

### L09
- 身份：N. Wang, J. G. Brennan. A mathematical model of simultaneous heat and moisture transfer during drying of potato. *Journal of Food Engineering*, 1995, 24:47–60. DOI: 10.1016/0260-8774(94)P1607-Y（由热湿耦合文献引用链定位）
- 核实范围：未读全文；仅作为“内部导热+湿扩散、表面对流、蒸发吸热”这一类模型的代表。
- 支持内容：问题 2–3 物性随含水率变化、温度进入 D 时，热质通过系数耦合；表面是否加汽化潜热是该类模型的分岔。
- 适用与差异：本题附录未给汽化潜热。加不加必须作为假设并做温度敏感性检验，不能把马铃薯实验系数当成本题参数。
- 状态：书目待打开全文后升级。
- 采用决定：候选；潜热项从问题 1 起就要定，不能到问题 3 才突然加入。

## A 题四问与文献对应（讨论用）

| 问 | 核心机制 | 优先阅读 |
| --- | --- | --- |
| 1 预热 1800 s | 圆柱径向热传导 + 湿扩散，烘房 T、C 随时间变，物性常值、D=D(C) | Hussain & Dincer 2003；Kaya et al. 2007；Luikov 1975 作背景 |
| 2 全过程前 3 h | 同上，但 ρ,cp,k=f(C)，D=D(C,T)；预热结束后烘房约 50°C | 仍用上两篇；Arrhenius 型 D(T) 只对照形式，系数用附录 3 |
| 3 烘至各处 C<0.15 | 问 2 模型积分到终止条件；瓶颈在中心 | 无新模型，检验网格/时间步与“各处”定义 |
| 4 收缩 | 已知 R(t) 的变半径网格，附录 4 换一套物性 | Adrover 2019；da Silva 等圆柱收缩干燥作离散参考 |

## 2026-09-10：A-route-v1 整体路线增量核查

以下对应本轮实际访问，历史“已核实”状态不自动代表本轮已阅读全文。检索词：Numerical modeling of forced-convection drying of cylindrical moist objects；A moving boundary model for food isothermal drying and shrinkage；Non-isothermal Moving-boundary Model for Food Drying。

### L08 本轮复核

- 来源：Kaya A., Aydin O., Dincer I. (2007)，*Numerical Heat Transfer, Part A*, 51(9):843–854，DOI 10.1080/10407780601112753。
- 实际读取：[作者机构研究信息页](https://avesis.ktu.edu.tr/yayin/835ff2e9-e0b5-4c67-babf-78bb8903a78e/numerical-modeling-of-forced-convection-drying-of-cylindrical-moist-objects) 的书目和Abstract，未读全文。
- 核实：圆柱湿物体的同时热质传递、隐式差分、局部对流系数范围。支持分布式数值路线，不支持直接采用其未读取的边界公式。
- 本题差异：题面已给h、hm，无需反演外部流场。原文有CFD部分，但不据此要求本题使用CFD。一维忽略端面、潜热处理、水分基准仍须本题自行论证。
- 决定：采用为整体方法依据，摘要级支持；不作题面数值结果来源。

### L10

- 身份：Brasiello A., Venditti C., Adrover A. (2021). *Non-isothermal Moving-boundary Model for Food Drying*. Chemical Engineering Transactions, 87:193–198. DOI 10.3303/CET2187033。
- 实际读取：[期刊官方页面](https://www.cetjournal.it/index.php/cet/article/view/CET2187033) 的作者、年份、引用信息与Abstract。书目信息已核实，论点为摘要级核实；未声称核对全文公式。
- 支持内容：收缩导致的体积变化会影响传递模型；即使烘房恒温，材料仍可能非等温；模型同时考虑热惯性、边界蒸发、热湿输运及收缩。
- 对应：支持第4问变域建模，也为第1–3问“忽略显式潜热”的候选简化提供反向提醒。
- 本题差异：文献对象为番石榴片等，使用的扩散率关系不同。本题R(t)已知，各问D由附录规定，不移植文献的材料参数，也不宣称其验证覆盖本题。
- 决定：采用为机制依据和局限说明；不直接照搬方程参数。

### 本轮访问限制与纠正

- L03出版商页面本轮直接打开返回403；另一篇shortcut文章的搜索结果提供出版商摘要/引言片段，但直接访问亦403。未据此升级L03为全文已核实。
- PMC相关文章本轮打开为验证码页，未读取全文，不以检索摘要补称全文结论。
- 旧记录中A题“长径比12.5”应为“长度/半径=12.5，长度/直径=6.25”。以原题L=25 cm、R=2 cm为准。
- 原PDF已视觉确认D指数：附录2为-0.89/C，附录3为-0.45/C与-3850/T_K，附录4为-0.30/C与-3850/T_K。所有这些系数依据题面，不依据外文材料。
- 当前证据缺口：空气水分与固体干基含水率的界面平衡映射、显式潜热闭合、收缩内部速度与干物质守恒、有限长度端面影响。整体方案把它们作为待论证假设，不把文献存在当作假设已获验证。

## 2026-09-10：q1-plan-v1 定向补查

范围：第一问的蒸发热边界、界面湿度解释、BDF与误差控制。检索词：Non-isothermal Moving-boundary Model for Food Drying PDF；SciPy solve_ivp BDF jac_sparsity rtol atol。未开展其他题的检索，也未移植外部食品参数。

### L10 核实范围更新

本轮可访问[期刊原始PDF](https://www.cetjournal.it/cet/21/87/033.pdf)，读取前3节相关内容，尤其出版页194–195的数学模型说明、式(4)–(5)附近边界解释及吸附等温段落。原文水分变量使用单位体积水分，界面传质通过蒸汽压/相对湿度描述，热边界包含蒸发吸热，并另用吸附等温关系联系固体含水量与表面相对湿度。

这支持“空气与固体的kg/kg不能仅因同单位而直接等同”的提醒，也支持潜热作为独立物理机制。原文对象和经验物性与本题不同，不采用番石榴的等温关系或参数。q1-plan-v1将简单hm(Cs-Ca)明确标为等效经验闭合；不显式潜热为候选基线简化，未声称经该论文验证。本轮仅核实所读章节，不宣称全文所有推导及实验均已独立复核。

### L11

- 来源身份：SciPy community，*solve_ivp — SciPy v1.18.0 Manual*，[官方文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)，访问2026-09-10。
- 实际读取：method中BDF/Radau定义；t_eval、max_step、rtol/atol、jac、jac_sparsity及success/status说明。
- 支持：BDF是隐式变阶方法；容差控制局部误差；输出时间与内部步长分离；可以利用稀疏雅可比结构。
- 本题差异：先将PDE做径向有限体积离散，才得到solve_ivp所求的ODE。工具成功退出不能证明空间收敛、物理真实性或四位有效精度。
- 核实：官方文档已读，现有数值解释器的SciPy1.18.0与文档版本一致，BDF与稀疏模块导入成功。尚未运行真实PDE。
- 决定：用于q1-plan-v1算法实现依据；网格数、容差、误差目标由本题设计并待验证，不说成文档给定的本题推荐参数。

### 自推导关系及边界

q1-plan-v1的环层守恒、中心系数4、有限体积面通量、常系数圆柱Bessel展开及分段线性温度输入的Duhamel表达均给出推导链，作为待数值核验的数学关系。没有引用未读取文献为公式背书；这些表达不使非线性水分问题变成解析可解，也不适用于后问变物性热方程。

## 建模依据追问的补充（2026-09-10）

用户要求解释为何选此模型及论文支撑。逐项说明见`reports/Q1_MODEL_RATIONALE.md`。本次不构成q1方案批准，也未开展数值求解。

### L12

- 身份：Hui Yang, Noboru Sakai, Manabu Watanabe (2001). Drying model with non-isotropic shrinkage deformation undergoing simultaneous heat and mass transfer. Drying Technology, 19(7), 1441–1460. DOI:10.1081/DRT-100105299。
- 来源：[出版商条目](https://www.tandfonline.com/doi/abs/10.1081/DRT-100105299)。期刊卷期年份2001，网页另有后期上线日期，不能混作出版年份。
- 实际读取：搜索返回的出版商摘要和书目；直接打开403，未读取全文。摘要称其联合圆柱热湿传递、非恒定物性与二维非各向同性收缩，采用有限元并与圆柱马铃薯实验比较。
- 支持范围：第4问热湿/收缩机制路线，也提示轴向与径向收缩不能未经说明等同。不能支持本题采用具体有限体积边界、忽略潜热或移植马铃薯参数。
- 采用：机制方向与限制说明，摘要级支持；不作为第1问公式细节来源。

### L02 全文升级（2026-09-11）

用户提供本地 PDF：`c:\Users\chens\Documents\xwechat_files\wxid_rsibjnswkr4q12_d929\msg\file\2026-09\Two-dimensional heat and moisture transfer analysis of  a cylindrical moist object subjected to drying  A finite-difference approach.pdf`。书目与 DOI 10.1016/S0017-9310(03)00229-1 一致，此前摘要级限制作废。详见上方 L02 条；不与同作者矩形物体干燥文混用。

本轮继续复用L08此前实际读取的机构摘要；本轮再访问该页超时，不升级其全文状态。L10期刊PDF可读，前3节支持此前的机制判断。用户可直接查看上方原文链接与建模依据说明。

## 2026-09-11：用户提供的主参考论文与潜热必要性

### L13（优先方法参考）

- 身份：Wilton Pereira da Silva, Cleide M.D.P.S. e Silva, Fernando J.A. Gama (2014). Estimation of thermo-physical properties of products with cylindrical shape during drying: The coupling between mass and heat. Journal of Food Engineering, 141:65–73. DOI:10.1016/j.jfoodeng.2014.05.010。
- 原始材料：`C:/Users/chens/Desktop/国赛论文/1.pdf`，9页；[出版商页面](https://www.sciencedirect.com/science/article/pii/S0260877414002118)书目与用户PDF相符。
- 核实范围：全文文本读完；PDF第3、4、7页已渲染检查公式/数值。式(1)圆柱守恒、式(8)–(9)平衡含水率边界、式(10)潜热耦合、式(14)调和平均、式(17)–(18)干物质量换算、3.3节删项对照均已定位。
- 支持：径向扩散、全隐式有限体积、表面潜热、变量物性与收缩方向；直接支持通过已知干物质量将平均干基含水率变化换算成失水kg/s。
- 反面证据：58.6°C实验固定已拟合参数，去掉潜热使R²从0.98843降至0.75502，χ²从28.9增至4146.1。支持潜热可能关键，不能外推相同误差到本题；不是竞争模型分别重拟合后的比较。
- 差异：论文M_eq是产品平衡含水率，不是空气含湿量；物性与香蕉收缩经验式不能迁移；水分等温假设与本题后问D(C,T)不同；其单元中心网格和全隐式TDMA不等同节点FVM+BDF；文中hT与本题h单位不同，见专项评估。
- 采用决定：作为核心方法参考，建议重新评估无潜热温度方案。没有直接替换既有批准模型。完整说明见`reports/Q1_REFERENCE_AND_LATENT_REVIEW.md`。

### L14（潜热量级物性来源）

- 身份：NISTIR 5078，Table 1, Saturation (Temperature)，[NIST官方饱和水表](https://www.nist.gov/document/nistir5078-tab1pdf)，[报告说明](https://www.nist.gov/srd/nistir-5078)。
- 核实：本轮官方检索返回表格40°C行汽化焓差2406.0 kJ/kg。取2.4×10^6 J/kg仅用于量级筛查，不冒称药材结合水的专用潜热。
- 适用差异：用自由水近似；正式模型若选择温度相关值应读取相应温区数据/关联式，且必须检验材料结合水效应。
- 本题使用：将既有q1无潜热场中的失水量转成隐含蒸发热。初始湿密度解释下30分钟失水18.6092 g，潜热44.6621 kJ，原显热4.8010 kJ。来源为实际后处理，不是论文实验数据或新PDE结果。详见`reports/Q1_LATENT_ENERGY_AUDIT.json`。

- 后续主模型评估补充：已读取同一官方表第1页0.01–50°C饱和蒸汽压，用对数线性插值反算露点。若附件Ca解释为kg水/kg干空气、取总压101325Pa，则0秒和1800秒露点约24.63、33.28°C。空气湿度解释与压力是明确诊断假设；露点由本题数据计算，不是NIST提供的本题结果。详见`Q1_MAIN_MODEL_DECISION.md`。

## 2026-09-10：用户提供全文对照（da Silva 2014）

用户指定本地文件 `c:\Users\chens\Desktop\国赛论文\1.pdf`，要求与当前第1问方案比较方法。本轮按全文9页读取，不据此改写 q1-plan-v1 方程，也不移植香蕉物性。

### L13

- 身份：Wilton Pereira da Silva, Cleide M.D.P.S. e Silva, Fernando J.A. Gama (2014). Estimation of thermo-physical properties of products with cylindrical shape during drying: The coupling between mass and heat. *Journal of Food Engineering*, 141, 65–73. DOI: 10.1016/j.jfoodeng.2014.05.010。
- 核实范围：用户提供的全文PDF（第65–73页），含摘要、假设、式(1)–(22)、香蕉实验、简化敏感性及结论。书目与DOI与原文页眉一致。
- 支持内容：圆柱一维径向液态扩散、第三类边界、有限体积全隐式离散、界面扩散系数调和平均；水分先按等温场求解，热量在表面通过蒸发潜热与失水速率耦合；含收缩与变量物性；用实验反演 D、α、hm、hT。第3.3节：忽略潜热使中心温度拟合完全不可接受（58.6°C 时 χ² 由 28.9 升至 4146.1）；忽略蒸汽升温影响很小；把 ρcp 当常数也会明显变差。
- 适用与差异：对象为整根香蕉、恒温热风、有称重与中心热电偶。本题第1问是药材、变温预热 1800 s、物性由附录给定、无内部观测，不能做同样反演。水分驱动力该文用 M−Meq，本题基线用 Cs−Ca。该文从一开始就收缩并重划网格；本题第1–3问固定几何，第4问用附件2的 R(t)。离散上该文是单元中心控制体+后向欧拉+TDMA；本题拟用节点型有限体积+BDF。D 形式该文为 bm exp(am M)，本题附录2为 7×10⁻⁹ exp(−0.89/C)。
- 状态：全文已读，主张已按所读章节核实。香蕉实验数值不作为本题结果。
- 采用决定：作为同类方法对照和“忽略潜热可能严重影响温度场”的外部证据；不替代题面参数，不自动把第1问基线改成含潜热模型。该文结论受香蕉长时干燥与可拟合实验约束，不能直接证明本题 30 min 预热也必须含潜热。

## 2026-09-11：第三问讨论的依据与定向补查

对应q3-discussion-v1。复用第二问当前方程及L02/L13既有方法记录，本轮未重新读取其论文全文，不升级核实状态。题面附录3图像再次核对，指数为-0.45/C、-3850/T_K；0.15与输出规格来源于题面。后4小时环境50°C、0.05来自既有附件审计与恒温阶段解释，明确为延续假设；不是文献参数或未来观测。

L11补查：实际打开SciPy官方solve_ivp文档 https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html ，读取BDF、events、direction、terminal、t_eval及max_step。支持连续事件根定位、负方向穿越、输出时刻与内部步长分离；文档同时提醒一步内多个越零可能漏检。仅为数值工具支持，不能证明空间最大值、全域达标或时长收敛。全域阈值、严格不等式下的inf定义与简单根误差传播为本题自行定义/推导，不强配外部论文。

## 2026-09-11：第三问求解创新候选的文献初查

L-Q3-01：Jehanzeb H. Chaudhry, Donald Estep, Zachary Stevens, Simon J. Tavener，Error estimation and uncertainty quantification for first time to a threshold value，arXiv:2001.11139，2020。https://arxiv.org/abs/2001.11139 。实际读取作者原始预印本摘要页，核对题名作者年份；摘要明确研究首次阈值时间、Taylor/求根误差表达及伴随后验估计。未读全文，不声称已核实定理条件和全部公式。

L-Q3-02：Jehanzeb Chaudhry, Don Estep, Trevor Giannini, Zachary Stevens, Simon Tavener，Error estimation for the time to a threshold value in evolutionary partial differential equations，arXiv:2111.09834，2021提交、v3于2022修订。https://arxiv.org/abs/2111.09834 。实际读取作者预印本摘要页；支持PDE首次阈值时间的Taylor及伴随后验估计路线，摘要给出半线性抛物/双曲方程、一维热方程和线性浅水验证范围。未读全文；不能将其结论直接套用于本题拟线性热湿耦合及全域max事件。

对应q3-innovation-candidate-v1；采用决定为待讨论方法候选，未验证本题效果。事件灵敏度和半离散伴随式在模型记录中明确为自行线性化推导。创新定位是既有目标导向方法在本题事件及耦合结构上的针对性改造，不宣称首次提出目标导向误差控制。

### L-Q3-03：Kirchhoff候选方法线索（2026-09-11）

本轮检索Kirchhoff transformation moisture dependent diffusivity drying nonlinear diffusion equation，读取出版商搜索结果摘要：A transient technique for determining diffusion coefficients in hygroscopic materials，https://www.sciencedirect.com/science/article/abs/pii/S0360132399000189 。摘要明确提及Kirchhoff势用于含水率依赖扩散的改写。未打开全文、作者年份尚未完整核对，不作为已就绪参考文献或本题效果证明。q3-method-menu-v1的D=A(T)f(C)、U积分、变换后PDE与边界由本题题给式直接推导，见Q3_METHOD_COMPARISON.md；不声称引自未读全文。


## 2026-09-11：第四问收缩模型定向补查

对应q4-discussion-v1。检索词：drying shrinkage solid velocity dry basis moisture moving coordinate conservation cylindrical model。复用L10既有第1–3节核实记录，本轮不冒称重读其全文。题给经验式由本地q2_source_page4.png复核，附件2/result4原工作簿只读核查。

### L-Q4-01

Alessandra Adrover, Claudia Venditti, Antonio Brasiello (2020). A Non-Isothermal Moving-Boundary Model for Continuous and Intermittent Drying of Pears. Foods, 9(11), 1577. DOI 10.3390/foods9111577。原期刊：https://www.mdpi.com/2304-8158/9/11/1577 。

本轮核实范围：搜索工具返回原期刊的书目、摘要及第3.2节片段；其中以cw为水分体积浓度，包含固体速度vs的水分对流扩散方程。原页面open返回429，PMC返回验证页，未通读全文或核对所有公式。书目和上述有限主张部分核实。

支持：收缩传递应区分材料运动与扩散，温度和水分可在移动域联合求解。差异：该文由局部水流预测收缩，研究梨、包含表面蒸发，采用体积浓度及自身物性；本题R已给定、C为干基量、物性由附录4给定。不能直接搬入其体积浓度压缩项，不移植其收缩因子或潜热参数。本题s与sC守恒消元、比例收缩映射与密度兼容性检查属于自行推导，文献不证明这些本题假设成立。

其他线索：2018年A moving boundary model for food isothermal drying and shrinkage: General setting的作者库返回403；2019年The Role of Shrinkage on Food Isothermal Drying: a Moving Boundary Model期刊页超时。只作检索线索，不计全文核实，不据其填写模型公式。

## 2026-09-11：第四问讨论恢复时的来源核对

对应q4-discussion-v2。本轮重新打开L10原期刊PDF https://www.cetjournal.it/cet/21/87/033.pdf ，实际读取第1–3节的文本（出版页193–196），核对作者、年份、DOI及材料速度、体积水浓度、界面蒸发和吸附等温关系的文字说明。网页提取未显示完整数学公式，不宣称本轮重新视觉核验各式。支持收缩热湿传递应明确材料运动；不证明本题比例收缩、无潜热或经验密度解释。题给R而文献由局部水流建立收缩，两者不直接互换。

L-Q4-01原期刊再次访问返回429，核实状态不升级。q4-discussion-v2的干基守恒和密度全局上界仍是依据题给关系自行推导，不来自外部文献。原题依据本輪重读A_text.txt，附件数值依据重读A_INPUT_AUDIT.json与v1原表读取记录；本轮未重开原Excel。
