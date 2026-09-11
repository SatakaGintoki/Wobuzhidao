"""Build reviewable Q1/Q2 LaTeX chapters from verified source arrays."""
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sci(x):
    a,b=f'{x:.2e}'.split('e')
    return rf'{a}\times10^{{{int(b)}}}'


def table(q, key, caption, label):
    z=np.load(ROOT/f'results/q{q}_solution.npz')
    ts=np.array([100,300,600,900,1200,1500,1800]) if q==1 else np.arange(1800,10801,1800)
    rows=[]
    for t,vals in zip(ts,z[key+'_out'][ts-1,::5]):
        time=str(t) if q==1 else f'{t/3600:.1f}'
        rows.append(time+' & '+' & '.join(f'{v:.4f}' for v in vals)+r' \\')
    return r'''
\begin{table}[H]
\centering
\caption{CAPTION}\label{LABEL}
\small
\begin{tabular}{rrrrrr}
\toprule
时间/UNIT & \multicolumn{5}{c}{到中心的距离/cm}\\
\cmidrule(lr){2-6}
 & 0 & 0.5 & 1.0 & 1.5 & 2.0\\
\midrule
ROWS
\bottomrule
\end{tabular}
\end{table}
'''.replace('CAPTION',caption).replace('LABEL',label).replace('UNIT','s' if q==1 else 'h').replace('ROWS','\n'.join(rows))


def figure(filename, caption, label, width='.70'):
    return rf'''
\begin{{figure}}[H]
\centering
\includegraphics[width={width}\textwidth]{{../figures/{filename}.pdf}}
\caption{{{caption}}}\label{{{label}}}
\end{{figure}}
'''


v1=json.loads((ROOT/'results/q1_validation.json').read_text(encoding='utf-8'))
v2=json.loads((ROOT/'results/q2_validation.json').read_text(encoding='utf-8'))
assert v1['delivery_gate']['meets_delivery_gate'] and v2['delivery_gate']['meets_delivery_gate']

q1=r'''\section{问题一的模型建立与求解}
\subsection{径向热湿传递模型}
将药材近似为半径 $R=0.02\,\mathrm m$、长度 $L=0.25\,\mathrm m$ 的圆柱体。
用 $T(r,t)$ 表示温度（$^\circ\mathrm C$），$C(r,t)$ 表示干基含水率（kg水/kg干物质）。
在预热阶段假设圆柱尺寸不变、周向均匀，忽略端面交换引起的轴向变化，仅求解径向传递。
已有圆柱干燥研究采用导热与水分扩散描述内部温湿场\cite{hussain2003}；本题的物性、初值及交换系数均取自题给附录2，不移用文献样品的经验参数。

依据径向导热与有效扩散关系，建立
\begin{align}
\rho c_p\frac{\partial T}{\partial t}
 &=\frac1r\frac{\partial}{\partial r}\left(rk\frac{\partial T}{\partial r}\right),\label{eq:q1_heat}\\
\frac{\partial C}{\partial t}
 &=\frac1r\frac{\partial}{\partial r}\left[rD(C)\frac{\partial C}{\partial r}\right],
 &D(C)&=7\times10^{-9}\exp\left(-\frac{0.89}{C}\right).\label{eq:q1_moisture}
\end{align}
其中 $\rho=820\,\mathrm{kg/m^3}$、$c_p=2600\,\mathrm{J/(kg\cdot K)}$、
$k=0.36\,\mathrm{W/(m\cdot K)}$，$D$ 的单位为 $\mathrm{m^2/s}$。
初始条件为 $T(r,0)=28$、$C(r,0)=2.55$；中心满足对称条件 $T_r(0,t)=C_r(0,t)=0$。
记烘房温度和水分浓度为 $T_a(t)$、$C_a(t)$，表面采用
\begin{equation}
-kT_r(R,t)=h[T(R,t)-T_a(t)],\qquad
-D(C_s)C_r(R,t)=h_m[C_s-C_a(t)],\label{eq:q1_robin}
\end{equation}
其中 $C_s=C(R,t)$，$h=25\,\mathrm{W/(m^2\cdot K)}$、$h_m=8\times10^{-7}\,\mathrm{m/s}$。
空气含湿量与药材干基含水率的基准不同，此处将题给浓度差及传质系数作为有效经验边界闭合，不将其解释为已测定的吸附平衡关系。
温度方程未显式计入蒸发潜热，其结果适用于所选等效模型。

对附件1中 $0$--$1800\,\mathrm s$ 的31个环境记录采用保形分段三次 Hermite 插值（PCHIP），
逐点保留观测值，不平滑数据。本问温度物性为常数且未引入潜热，温度方程与水分方程分别求解；水分方程始终保留 $D(C)$ 的非线性。

\subsection{有限体积离散与数值检验}
在 $0\le r\le R$ 上设置包含中心和表面的非均匀节点，将相邻节点中点作为控制体边界。
第 $i$ 个环形控制体的径向权重为
\begin{equation}
W_i=\int_{r_{i-1/2}}^{r_{i+1/2}}r\,\mathrm dr
=\frac{r_{i+1/2}^2-r_{i-1/2}^2}{2}.
\end{equation}
以 $F_{i+1/2}=-r_{i+1/2}D_{i+1/2}(C_{i+1}-C_i)/(r_{i+1}-r_i)$
表示向外的径向水分通量，则 $W_i\dot C_i=F_{i-1/2}-F_{i+1/2}$。
面扩散系数取相邻节点系数的调和平均；中心内侧通量为零，表面通量直接由式\eqref{eq:q1_robin}给出。
热传递按同一控制体积分，储热权重为 $\rho c_pW_i$。
该写法通过控制体积分处理中心，不在 $r=0$ 直接计算 $1/r$。

半离散系统采用隐式后向差分公式（BDF）积分。
在表面附近加密网格，同时使题目要求的每隔 $0.1\,\mathrm{cm}$ 输出位置均为计算节点。
比较529、1057和2113个节点，选用2113节点结果。
生产计算相对容差为 $10^{-10}$，温度和含水率绝对容差分别为 $10^{-10}$ 和 $10^{-12}$，最大时间步长为 $0.5\,\mathrm s$；另将容差缩小5倍、最大步长减半，检查时间敏感性。

温度的独立线性参考由分离变量与 Duhamel 叠加构造。
令 $\alpha=k/(\rho c_p)$、$\mathrm{Bi}=hR/k$，特征根满足
$\lambda_nJ_1(\lambda_n)=\mathrm{Bi}J_0(\lambda_n)$，则
\begin{align}
T(r,t)&=T_a(t)-\sum_{n=1}^{\infty}A_nJ_0(\lambda_nr/R)I_n(t),\\
A_n&=\frac{2J_1(\lambda_n)}{\lambda_n[J_0(\lambda_n)^2+J_1(\lambda_n)^2]},
\qquad \dot I_n=-\frac{\alpha\lambda_n^2}{R^2}I_n+\dot T_a(t).
\end{align}
其中 $J_0,J_1$ 为第一类 Bessel 函数，$I_n(0)=T_a(0)-28$。
将截断项数加倍并核对全部输出点变化后，才使用其作为参考。
水分的解析对照仅用于将 $D$ 冻结在初值后的辅助问题，不能代替式\eqref{eq:q1_moisture}的非线性答案。

相邻两层细网格的温度、含水率最大差分别为 $GRIDT$ 和 $GRIDC$，均小于预设的 $2\times10^{-5}$ 数值目标。
表1、表2在空间与时间加密后均保持四位小数不变；完整输出中仍有接近舍入分界的数值发生末位变化，不能据此声称所有单元格的第四位均已冻结。
温度与独立参考的最大差为 $BESSEL$。
对连续数值解的表面通量按 PCHIP 区间自适应积分，热、湿累计收支的相对残差分别为 $HEATBAL$ 和 $MOISTBAL$。
以上检验针对离散与积分误差，不代表经验参数及真实药材预测具有同样精度。

\subsection{预热阶段的温度与含水率分布}
'''
q1=q1.replace('GRIDT',sci(v1['grid_convergence']['T_G4_vs_G8']['max_abs'])).replace('GRIDC',sci(v1['grid_convergence']['C_G4_vs_G8']['max_abs'])).replace('BESSEL',sci(v1['bessel_temperature']['max_abs'])).replace('HEATBAL',sci(v1['conservation_T_1800s']['relative_residual'])).replace('MOISTBAL',sci(v1['conservation_C_1800s']['relative_residual']))
q1+=table(1,'T',r'30分钟内药材温度（$^\circ\mathrm C$）','tab:q1_T')+table(1,'C',r'30分钟内药材干基含水率（kg/kg）','tab:q1_C')
q1+=r'''在1800 s时，烘房温度为 $41.513\,^\circ\mathrm C$。
药材表面温度为 $36.7879\,^\circ\mathrm C$，中心温度为 $33.5758\,^\circ\mathrm C$。
表面先响应环境升温，热量向内传递形成径向梯度。
表面干基含水率降至 $1.5102$，中心仍为 $2.549992$（四位显示为 $2.5500$），说明短时失水主要集中在外层。
中心四位显示不变并不意味着中心完全没有失水。
'''
q1+=figure('q1_T_profiles','预热阶段不同时间的径向温度分布','fig:q1_T')
q1+=figure('q1_C_profiles','预热阶段不同时间的径向干基含水率分布','fig:q1_C')
q1+=r'''含水率下降使局部扩散系数减小，外层失水与内部补水形成动态耦合。
题目要求的逐秒温度和含水率按每隔 $0.1\,\mathrm{cm}$ 输出至 \texttt{result1.xlsx}，显示保留四位小数，计算及后续核查使用未舍入值。
忽略潜热和端面交换是本模型的主要局限；上述数值检验不消除这些物理近似。
'''

q2=r'''\section{问题二的模型建立与求解}
\subsection{变物性热湿耦合模型}
沿用第一问的固定圆柱径向结构、初值和有效交换边界，将全时段物性统一替换为附录3。
本问从 $T(r,0)=28$、$C(r,0)=2.55$ 重新积分，不以第一问的1800 s末态为初值，因而两问结果不能直接拼接为同一条时间轨迹。
令 $B(C)=\rho(C)c_p(C)$，方程为
\begin{align}
B(C)T_t&=\frac1r\partial_r[rk(C)T_r],\label{eq:q2_heat}\\
C_t&=\frac1r\partial_r[rD(C,T)C_r],\label{eq:q2_moisture}\\
\rho(C)&=650+128C,\qquad c_p(C)=1450+2736\frac{C}{1+C},\\
k(C)&=0.21+0.38\frac{C}{1+C},\\
D(C,T)&=2.4\times10^{-3}\exp\left(-\frac{0.45}{C}\right)
\exp\left(-\frac{3850}{T+273.15}\right).
\end{align}
温度状态量以摄氏度存储，经验扩散系数中的温度换算为开尔文；其余物性单位与第一问相同。
中心仍采用零梯度条件，表面为
\begin{equation}
-k(C_s)T_r(R,t)=h(T_s-T_a),\qquad
-D(C_s,T_s)C_r(R,t)=h_m(C_s-C_a).
\end{equation}
由于局部温度影响 $D$，含水率又影响 $B$ 与 $k$，两场必须联合推进。
变系数保留在散度算子内，不将水分方程简化为 $D(C,T)(C_{rr}+C_r/r)$，以免遗漏系数空间变化的影响。
附录中的密度用于有效热容量，不另以 $\rho/(1+C)$ 构造可变干物质密度。
本问继续采用无显式潜热和忽略端面的等效模型。

\subsection{联合求解与验证}
对附件1中前3小时的181个环境节点采用PCHIP插值，节点全部保留，计算时段内无需外推。
径向控制体与第一问一致，$k$、$D$ 的面系数按局部状态更新，储热项采用 $B(C_i)W_i\dot T_i$。
温度和含水率组成联合状态向量，采用隐式BDF积分。
比较529与1057个节点后选用1057节点；独立审核进一步以2113节点检查完整3小时结果。
生产相对容差为 $10^{-9}$，温度和含水率绝对容差为 $10^{-8}$、$10^{-10}$，最大时间步长为1 s；另进行容差缩小5倍和最大步长0.5 s的复算。

独立加密检查中，1057与2113节点的全部规定输出点温度、含水率最大差分别为
$6.24\times10^{-7}\,^\circ\mathrm C$、$3.73\times10^{-6}\,\mathrm{kg/kg}$。
论文两表共60个四位小数在时间与空间加密后均不变。
另以预先给定的光滑温湿场反推源项，进行变系数制造解检验，温度、含水率最大误差分别为 $MMST$、$MMSC$。
冻结 $D$ 的辅助水分问题采用Bessel参考，级数加倍后再比较，避免早期级数截断不足影响判断。

水分收支以径向权重加权存量与表面通量积分核对。
对热方程，定义有效储热量
\begin{equation}
E(t)=2\pi L\int_0^R B(C)(T-28)r\,\mathrm dr.
\end{equation}
由乘积求导可得
\begin{equation}
E(t)-E(0)-2\pi L\int_0^t\!\int_0^R
B'(C)(T-28)C_t r\,\mathrm dr\,\mathrm d\tau
=2\pi RL\int_0^t h(T_a-T_s)\,\mathrm d\tau.
\end{equation}
该组成修正项来自乘积求导，不能省略。
热、湿相对收支残差分别为 $HEATBAL$、$MOISTBAL$；全部内部节点满足所设温湿界限。
这一有效热收支不是包含潜热和组分焓输运的完整物理能量守恒。

\subsection{前三小时的干燥规律}
'''
q2=q2.replace('MMST',sci(v2['mms']['T_max_abs'])).replace('MMSC',sci(v2['mms']['C_max_abs'])).replace('HEATBAL',sci(v2['conservation_T_10800s']['relative_residual'])).replace('MOISTBAL',sci(v2['conservation_C_10800s']['relative_residual']))
q2+=table(2,'T',r'3小时内药材温度（$^\circ\mathrm C$）','tab:q2_T')+table(2,'C',r'3小时内药材干基含水率（kg/kg）','tab:q2_C')
q2+=r'''3 h时，中心与表面温度分别为 $49.8494\,^\circ\mathrm C$、$49.9645\,^\circ\mathrm C$，
温差约 $0.1151\,^\circ\mathrm C$，而两处干基含水率仍分别为 $1.7662$ 和 $1.0081$。
温度已接近烘房恒温水平，水分仍存在显著径向差异，说明热平衡与干燥完成不是同一条件。
该时刻尚未满足各处含水率低于 $0.15\,\mathrm{kg/kg}$ 的要求。
'''
q2+=figure('q2_T_profiles','前三小时不同时间的径向温度分布','fig:q2_T')
q2+=figure('q2_C_profiles','前三小时不同时间的径向干基含水率分布','fig:q2_C')
q2+=r'''经验式中，升温使扩散系数增大，含水率下降则使扩散系数减小。
这两种作用随时间与位置共同变化，因此不能用固定扩散系数或前三小时的失水斜率直接外推最终干燥时长。
本问将前3小时每隔1 s、径向每隔 $0.1\,\mathrm{cm}$ 的温度和含水率写入 \texttt{result2.xlsx}。
内部计算网格比输出网格更细，保存初值、论文表时刻和末态检查点以便复核。
后续长时预测仍需单独明确环境延续，并检验长期一维近似与达标时刻的数值稳定性。
'''

chapter_dir=ROOT/'paper/closeout/sections'
chapter_dir.mkdir(parents=True, exist_ok=True)
(chapter_dir/'5_problem1.tex').write_text(q1,encoding='utf-8')
(chapter_dir/'6_problem2.tex').write_text(q2,encoding='utf-8')
refs=r'''\begin{thebibliography}{9}
\bibitem{hussain2003} Hussain M M, Dincer I. Two-dimensional heat and moisture transfer analysis of a cylindrical moist object subjected to drying: A finite-difference approach[J]. International Journal of Heat and Mass Transfer, 2003, 46: 4033--4039.
\end{thebibliography}
'''
(ROOT/'paper/closeout/references.tex').write_text(refs,encoding='utf-8')
preamble=(ROOT/'paper/main.tex').read_text(encoding='utf-8').split(r'\begin{document}')[0]
preview=preamble+r'''\begin{document}
\begin{center}{\Large\heiti 药材烘干：前两问模型与结果}\end{center}
\setcounter{section}{4}
\input{closeout/sections/5_problem1}
\clearpage
\input{closeout/sections/6_problem2}
\input{closeout/references}
\end{document}
'''
(ROOT/'paper/q12_closeout.tex').write_text(preview,encoding='utf-8')
print('Built two chapters, reference entry and standalone preview source.')
