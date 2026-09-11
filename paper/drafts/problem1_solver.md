# 问题一求解方法（公式推导稿）

说明：本稿只写第1问已经采用的空间离散与时间积分，不含计算结果。数值须待求解完成后从结果报告写入，不得在本稿中填造。排版引擎未定时先以 Markdown 积累，正式论文再迁入问题一章节。

---

空间离散采用节点型有限体积法，把径向抛物方程化为常微分方程组；时间积分采用隐式反向差分公式（BDF）。温度场线性、水分场非线性，两套方程相互独立，分别积分。以下推导与实现使用同一套节点、通量和权重定义。

## 1. 从环层守恒到强形式

取药材中部横截面，径向坐标 $r\in[0,R]$，$R=0.02\,\mathrm{m}$。向外热流密度取 Fourier 定律
$$
q=-k\frac{\partial T}{\partial r}.
$$
半径 $[r,r+\mathrm{d}r]$ 的圆环体积为 $2\pi r L\,\mathrm{d}r$。该环层蓄热率等于进入的热量减去流出的热量：
$$
\rho c_p(2\pi r L\,\mathrm{d}r)\frac{\partial T}{\partial t}
=-\frac{\partial}{\partial r}(2\pi r L q)\,\mathrm{d}r.
$$
代入 $q$ 并约去公共因子，得到
$$
\rho c_p\frac{\partial T}{\partial t}
=\frac1r\frac{\partial}{\partial r}\left(rk\frac{\partial T}{\partial r}\right),\qquad 0<r<R.
$$
本问 $k$ 为常数，也可写成 $T_t=\alpha(T_{rr}+T_r/r)$，其中 $\alpha=k/(\rho c_p)$。

水分取固定、均匀的参考干物质密度 $\rho_d$，相对水质量通量 $j=-\rho_d D(C)\partial C/\partial r$。环层守恒后约去 $\rho_d$，得到
$$
\frac{\partial C}{\partial t}
=\frac1r\frac{\partial}{\partial r}\left(r D(C)\frac{\partial C}{\partial r}\right),
\qquad
D(C)=7\times10^{-9}\exp(-0.89/C).
$$
若把变扩散系数提出散度之外，会多出 $D'(C)(\partial_r C)^2$ 一项，$D'(C)=D(C)\cdot 0.89/C^2$。离散时始终保留通量形式，避免漏掉这一项。

初边值为
$$
T(r,0)=28,\quad C(r,0)=2.55,
$$
$$
\frac{\partial T}{\partial r}(0,t)=0,\quad
\frac{\partial C}{\partial r}(0,t)=0,
$$
$$
-k\frac{\partial T}{\partial r}(R,t)=h\bigl[T(R,t)-T_a(t)\bigr],
$$
$$
-D(C_s)\frac{\partial C}{\partial r}(R,t)=h_m\bigl[C_s-C_a(t)\bigr],\quad C_s=C(R,t).
$$
$T_a(t)$、$C_a(t)$ 由附件1观测点作保形三次 Hermite（PCHIP）插值，精确通过全部观测点。表面值由方程求出，不直接指定为烘房值。

## 2. 节点型有限体积网格

将 $[0,R]$ 分成 $N$ 个等距区间，步长 $\Delta r=R/N$，节点
$$
r_i=i\Delta r,\qquad i=0,1,\ldots,N.
$$
$r_0=0$ 为真实中心，$r_N=R$ 为真实表面。节点 $i$ 的控制体为 $[a_i,b_i]$：
$$
a_i=\max(0,r_i-\Delta r/2),\qquad
b_i=\min(R,r_i+\Delta r/2).
$$
径向体积权重定义为
$$
W_i=\frac{b_i^2-a_i^2}{2}.
$$
真实体积为 $2\pi L W_i$，且 $\sum_{i=0}^N W_i=R^2/2$。中心控制体 $W_0=\Delta r^2/8$，表面控制体
$$
W_N=\bigl[R^2-(R-\Delta r/2)^2\bigr]/2.
$$
内部节点有 $W_i=r_i\Delta r$。

生产计算在每个 $0.1\,\mathrm{cm}$ 输出区间内再细分，外侧更密，使规定输出半径仍落在节点上。一般非均匀网格把上式中的 $\Delta r$ 换成相邻节点间距 $r_{i+1}-r_i$，界面仍取算术中点；等距网格是其特例，中心系数 $4$ 的推导在等距情形下最直接。

## 3. 面通量与半离散方程

在内部面 $r_{i+1/2}=(r_i+r_{i+1})/2$ 上，定义已经乘过半径的向外通量
$$
F^T_{i+1/2}=-r_{i+1/2}\,k\,\frac{T_{i+1}-T_i}{\Delta r},
$$
$$
F^C_{i+1/2}=-r_{i+1/2}\,D_{i+1/2}\,\frac{C_{i+1}-C_i}{\Delta r}.
$$
界面扩散系数取调和平均，以保证正的面传输系数：
$$
D_{i+1/2}=\frac{2D(C_i)D(C_{i+1})}{D(C_i)+D(C_{i+1})}.
$$
若 $D(C_i)=D(C_{i+1})$，上式退化为该共同值。这是离散选择，不是题面给的材料混合定律。

中心面通量为 $0$。外表面用真实对流通量
$$
F^T_{\mathrm{surf}}=Rh\bigl(T_N-T_a(t)\bigr),\qquad
F^C_{\mathrm{surf}}=Rh_m\bigl(C_N-C_a(t)\bigr).
$$
对控制体 $i$ 积分后，蓄积等于左面流入减右面流出：
$$
\rho c_p W_i\dot T_i=F^T_{\mathrm{left},i}-F^T_{\mathrm{right},i},
$$
$$
W_i\dot C_i=F^C_{\mathrm{left},i}-F^C_{\mathrm{right},i}.
$$
同一内部面通量在相邻控制体中以相反符号出现，因此离散系统自动满足全局热、湿收支恒等式，可用于事后独立核验。

## 4. 中心与表面的专门格式

中心 $i=0$：$F_{\mathrm{left}}=0$，$r_{1/2}=\Delta r/2$，于是
$$
\rho c_p W_0\dot T_0=-F^T_{1/2}
=\frac{k}{2}(T_1-T_0).
$$
代入 $W_0=\Delta r^2/8$，得到
$$
\dot T_0=\frac{4\alpha}{\Delta r^2}(T_1-T_0).
$$
水分同理
$$
\dot C_0=\frac{4D_{1/2}}{\Delta r^2}(C_1-C_0).
$$
系数 $4$ 不能改成平板网格的 $2$。连续极限下，圆柱径向 Laplace 算子在中心满足 $\nabla^2 u|_{r=0}=2u''(0)$：由对称性 $u_r(0)=0$，L'Hôpital 法则给出 $u_r/r\to u_{rr}$，故
$$
u_{rr}+\frac1r u_r\Big|_{r=0}=2u_{rr}(0).
$$
二阶中心差分并用镜像点 $u_{-1}=u_1$，有 $u_{rr}(0)\approx 2(u_1-u_0)/\Delta r^2$，从而 $\nabla^2 u(0)\approx 4(u_1-u_0)/\Delta r^2$，与有限体积中心格式一致。

表面节点 $i=N$，$r_{N-1/2}=R-\Delta r/2$，
$$
\rho c_p W_N\dot T_N
=(R-\Delta r/2)k\frac{T_{N-1}-T_N}{\Delta r}
+Rh\bigl(T_a(t)-T_N\bigr),
$$
$$
W_N\dot C_N
=(R-\Delta r/2)D_{N-1/2}\frac{C_{N-1}-C_N}{\Delta r}
-Rh_m\bigl(C_N-C_a(t)\bigr).
$$
Robin 边界以通量形式进入最外层方程，不采用一阶单边差分去改写 $\partial_r T(R,t)$。控制体积分中以节点值代表控制体平均值；表面附近瞬态梯度较大，收敛阶由网格加密检验，不事先断言全域二阶。

内部节点 $i=1,\ldots,N-1$ 的温度方程可写成
$$
\rho c_p W_i\dot T_i
=\frac{k}{\Delta r}\Bigl[
r_{i+1/2}(T_{i+1}-T_i)-r_{i-1/2}(T_i-T_{i-1})
\Bigr].
$$

## 5. 线方法与刚性

上述空间离散把 PDE 化为 $N+1$ 维常微分方程
$$
\dot{\mathbf{y}}(t)=f\bigl(t,\mathbf{y}(t)\bigr),
$$
其中 $\mathbf{y}$ 为全部节点上的 $T$ 或 $C$。这就是线方法（method of lines）。温度问题中 $f$ 对 $\mathbf{y}$ 线性，且
$$
\dot{\mathbf{T}}=M\mathbf{T}+\mathbf{g}(t),
$$
$\mathbf{g}(t)$ 仅由表面节点的 $T_a(t)$ 贡献；水分问题中界面 $D_{i+1/2}$ 依赖 $\mathbf{C}$，$f$ 非线性。

扩散算子最负的特征值约为 $-\alpha/\Delta r^2$ 量级。对显式 Euler，中心格式的正系数要求给出步长限制
$$
\Delta t\le\frac{\Delta r^2}{4\alpha}.
$$
$N=160$ 时该限制约为 $0.023\,\mathrm{s}$，远小于输出间隔 $1\,\mathrm{s}$ 和观测间隔 $60\,\mathrm{s}$。因此不宜采用显式 Runge–Kutta（如 RK45）作为主积分器：限制来自稳定性而非局部截断误差。隐式方法每步求解关于 $\mathbf{y}_{n+1}$ 的代数方程，步长不再被 $\Delta r^2/\alpha$ 卡住。

## 6. 反向差分公式（BDF）

设时间步长为 $\Delta t$，反向差分算子为
$$
\nabla y_{n+1}=y_{n+1}-y_n,\qquad
\nabla^k y_{n+1}=\nabla^{k-1} y_{n+1}-\nabla^{k-1} y_n.
$$
$k$ 阶 BDF 把导数换成向后差分：
$$
\sum_{j=1}^{k}\frac1j\nabla^j y_{n+1}
=\Delta t\, f(t_{n+1},y_{n+1}).
$$
一阶即后向 Euler 公式
$$
y_{n+1}-y_n=\Delta t\, f(t_{n+1},y_{n+1}).
$$
二阶为
$$
\frac32 y_{n+1}-2y_n+\frac12 y_{n-1}
=\Delta t\, f(t_{n+1},y_{n+1}).
$$
一般定步长形式可写成
$$
\sum_{j=0}^{k}\alpha_{k,j} y_{n+1-j}
=\Delta t\,\beta_k f(t_{n+1},y_{n+1}),
$$
其中 $\beta_k\neq 0$，$\alpha_{k,0}\neq 0$。左端只用已经算出的旧值和未知的 $y_{n+1}$，右端只在新时刻取值，因此是隐式线性多步法。BDF 对刚性扩散问题 $A$-稳定阶不超过 $2$，但 $3$–$5$ 阶仍具有足够的刚性稳定性，适合本问的抛物方程。

水分方程在 $y_{n+1}$ 处非线性。将上式记为
$$
F(y_{n+1}):= y_{n+1}-\gamma\Delta t\, f(t_{n+1},y_{n+1})-\psi_n=0,
$$
其中 $\gamma$ 由当前阶数决定（BDF1 时 $\gamma=1$，BDF2 时 $\gamma=2/3$），$\psi_n$ 由历史值线性组合而成。Newton 迭代为
$$
\bigl(I-\gamma\Delta t\, J\bigr)\Delta y=-F(y^{(m)}),\qquad
y^{(m+1)}=y^{(m)}+\Delta y,
$$
$$
J=\frac{\partial f}{\partial y}\Big|_{t_{n+1},y^{(m)}}.
$$
$J$ 为三对角稀疏矩阵：温度的 $J$ 为常数；水分的 $J$ 随 $C$ 变化，但带宽不变。实际计算采用变阶变步长的 BDF（阶数在 $1$ 与 $5$ 之间），按局部误差容差自动选取 $\Delta t$。环境输入为 PCHIP，一阶导数连续，时间积分在 $[0,1800]\,\mathrm{s}$ 上连续推进，不必再按 $60\,\mathrm{s}$ 折点切断。

局部容差控制的是一步时间误差，不能单独保证 PDE 解的小数位数。空间误差由加密网格评估；时间误差另用收紧 `rtol`/`atol` 与减小最大步长来检查。

对非物理试探值 $C\le 0$，仅在求解器定义域内令 $D=0$，防止 $\exp(-0.89/C)$ 溢出。任何被接受的数值解若低于物理界限超过容差，则判定失败并缩小步长，不把该延拓解释为材料本构。

## 7. 离散守恒恒等式

温度：以 $T_0$ 为参考的离散热能（相对量）
$$
E_T(t)=2\pi L\rho c_p\sum_{i=0}^N W_i\bigl(T_i(t)-T_0\bigr)
$$
应等于累计表面对流输入
$$
Q(t)=2\pi R L\int_0^t h\bigl(T_a(s)-T_N(s)\bigr)\,\mathrm{d}s.
$$
水分：归一化存量 $M_C(t)=\sum_i W_i C_i(t)$ 满足
$$
M_C(t)-M_C(0)=-R\int_0^t h_m\bigl(C_N(s)-C_a(s)\bigr)\,\mathrm{d}s.
$$
半离散层上，对节点方程乘 $W_i$ 再求和，内部面通量两两抵消，只剩表面通量，故上述恒等式在空间离散后是代数恒等的；再用与主求解器独立的自适应求积检查时间积分误差。该检验只说明离散守恒被正确实现，不能证明忽略潜热或等效水分势在物理上成立。

## 8. 线性温度问题的解析核验

常物性热方程在环境温度连续可导、且 $T_a(0)=T_0$ 时可用分离变量加 Duhamel 叠加独立求解，用于核验有限体积解，不替代非线性水分计算。

令 $\mathrm{Bi}=hR/k$。径向特征问题
$$
\lambda J_1(\lambda)=\mathrm{Bi}\, J_0(\lambda)
$$
的正根记为 $\lambda_n$，对应
$$
A_n=\frac{2J_1(\lambda_n)}{\lambda_n\bigl[J_0(\lambda_n)^2+J_1(\lambda_n)^2\bigr]},
\qquad
\beta_n=\frac{\alpha\lambda_n^2}{R^2}.
$$
常环境阶跃满足
$$
\frac{T(r,t)-T_a}{T_0-T_a}
=\sum_{n=1}^\infty A_n J_0(\lambda_n r/R)\,e^{-\beta_n t}.
$$
对一般连续 $T_a(t)$，
$$
T(r,t)=T_a(t)-\sum_{n=1}^\infty A_n J_0\!\left(\frac{\lambda_n r}{R}\right) I_n(t),
$$
$$
I_n(t)=\bigl(T_a(0)-T_0\bigr)e^{-\beta_n t}
+\int_0^t e^{-\beta_n(t-\tau)}T_a'(\tau)\,\mathrm{d}\tau.
$$
本题 $T_a(0)=T_0$，第一项为零。对 PCHIP 输入，$T_a'(t)$ 连续但不是分段常数，因此将
$$
\dot I_n=-\beta_n I_n+T_a'(t),\qquad I_n(0)=0
$$
与热方程并行用 BDF 积分，得到与有限体积解独立的参考温度。级数项数加倍直至关键点变化小于预定阈值后，再与数值解比较。

水分没有本题非线性 $D(C)$ 下的闭式解。可将 $D$ 暂时固定为 $D(C_0)$，用 $\mathrm{Bi}_m=h_m R/D(C_0)$ 做同样的 Bessel 检验，只用于检查空间离散；该对照不得写入正式水分答卷。

## 9. 实现口径（不含数值）

- 温度与水分分开积分。
- 表面加密网格，使 $0,0.1,\ldots,2\,\mathrm{cm}$ 仍落在节点上，无需空间插值；比较加密等级后取四位小数稳定的网格发表。
- 局部容差：相对容差 $10^{-10}$，温度绝对容差 $10^{-10}\,{}^\circ\mathrm{C}$，水分绝对容差 $10^{-12}\,\mathrm{kg/kg}$，单步上限 $0.5\,\mathrm{s}$。
- 环境为 PCHIP，整段 $[0,1800]\,\mathrm{s}$ 连续积分，整秒输出。
- 主积分器为隐式 BDF；仅在出现异常时用 Radau 或后向 Euler 复核同一空间离散，不作为另一套物理模型。
