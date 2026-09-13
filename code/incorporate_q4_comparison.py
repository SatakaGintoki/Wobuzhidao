"""Integrate the verified fixed-radius control into the existing manuscript."""
from pathlib import Path
import json
import shutil
import hashlib

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper/guosai2026'
O=ROOT/'results/q4_fixed_comparison'


def replace(path, old, new):
    s=path.read_text(encoding='utf-8')
    if old not in s:
        if new in s: return
        raise RuntimeError(f'Missing expected text in {path}: {old[:80]}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')


def main():
    v=json.loads((O/'comparison.json').read_text(encoding='utf-8'))
    assert v['pass']
    fixed,shrink,delta,pct=(v[k] for k in ['fixed_report_h','shrink_report_h','saving_report_h','saving_percent'])
    q=P/'sections/06_q4.tex'
    # The new control plot replaces the redundant center/surface history panel;
    # the existing radial profiles and all prescribed tables are retained.
    replace(q,'中心与表面历程见图\\ref{fig_q4history}，规定时刻的径向剖面见图\\ref{fig_q4profiles}',
            '规定时刻的径向剖面见图\\ref{fig_q4profiles}')
    old=r'''\begin{figure}[H]
\centering\includegraphics[width=.72\linewidth]{q4_C_history.pdf}
\caption{收缩模型中心与表面含水率历程。中心与全域最大值重合，虚线为0.15 kg/kg阈值。}
\label{fig_q4history}
\end{figure}'''
    s=q.read_text(encoding='utf-8')
    if old in s: q.write_text(s.replace(old,'',1),encoding='utf-8')
    old=r'''\subsection{几何与物性变化的影响讨论}
本问同时把物性换成附录4、把计算域换成给定$R(t)$。两者都会进入时长预测，不能把51.0877 h解释成收缩的单独效应。若要分离几何贡献，应在附录4物性和相同环境下比较$R\equiv R_0$与$R=R(t)$；该对照未做，故不与固定半径、附录3条件下的结果比较时长。'''
    new=r'''\subsection{同物性对照与收缩贡献}
第三问与第四问同时改变物性和几何，二者的时长差不能单独归因于收缩。为分离模型中的几何作用，增加附录4物性下的固定半径对照：两组均采用本问的初值、有效热湿方程、表面交换系数、前4 h环境插值及其后的50 $^\circ$C、0.05 kg/kg恒定环境，仅将半径分别设为$R\equiv R_0=0.02$ m和附件2给定的$R(t)$。固定组由式\eqref{eq_shrink}取常半径得到，仍联合求解温湿场，并以全部节点的最大含水率严格低于0.15为终止要求。

表\ref{tab_q4_control}列出两组结果。固定组采用与收缩组一致的$G_8$生产网格及BDF容差，再用$G_{16}$和时间收紧复核；两组均按最晚临界根后留出2 s并向上取四位小时，检验同一报告时刻的未舍入最大值和经验裕量。
\begin{table}[htbp]\centering\small
\caption{附录4物性下固定半径与实测收缩的对照}\label{tab_q4_control}
\begin{tabular}{lrrr}\toprule
半径方案 & 临界时间/h & 严格报告时间/h & 报告时最大含水率\\
 & & & (kg/kg)\\\midrule
固定$R=R_0$ & @FC@ & @F@ & @MC@\\
实测$R(t)$ & @SC@ & @S@ & 0.1499989333\\\bottomrule
\end{tabular}
\end{table}

以固定组报告时长为分母，收缩使本模型的预测烘干时间减少
\begin{equation}\label{eq_q4_saving}
\begin{gathered}
\Delta t_{\rm shrink}=t_{\rm fixed,4}-t_{\rm shrink,4}
=@F@-@S@=@D@\ \mathrm h,\\
\eta_t=\frac{\Delta t_{\rm shrink}}{t_{\rm fixed,4}}\times100\%
\approx@P@\%.
\end{gathered}
\end{equation}
两组临界根之差为@DC@ h，与报告时长差在四位小数下一致，说明该差异不由严格达标的时间裕量造成。图\ref{fig_q4_control}展示中心含水率全过程及后期放大；保存轨迹中两组中心均与径向最大值重合，收缩组更早穿越阈值。
\begin{figure}[htbp]\centering
\includegraphics[width=.94\linewidth]{q4_fixed_vs_shrink.pdf}
\caption{同一附录4物性下，收缩组比固定半径组更早达标。左图为中心含水率全过程，右图放大后期；曲线止于各自报告时刻，点线为0.15 kg/kg阈值。}
\label{fig_q4_control}
\end{figure}

固定组约129.84 h超过附件2的72 h覆盖，但其半径为指定常数，不使用或外推72 h后的实测半径；收缩组仍在观测范围内达标。固定组后期沿用既定恒温恒湿假设。这一反事实数值对照量化的是所选有效模型中的收缩总效应，包括扩散距离、表面交换和温湿物性的反馈，不是独立实测的节时比例，也不能由第三、四问的直接相减替代。'''
    for token,value in {'@FC@':f"{v['fixed_critical_h']:.7f}",'@SC@':f"{v['shrink_critical_h']:.7f}",
                        '@F@':f'{fixed:.4f}','@S@':f'{shrink:.4f}','@D@':f'{delta:.4f}',
                        '@P@':f'{pct:.2f}','@DC@':f"{v['saving_critical_h']:.7f}",
                        '@MC@':f"{v['fixed_report_maxima']['G8']:.10f}"}.items(): new=new.replace(token,value)
    replace(q,old,new)
    p=P/'sections/abstract.tex'
    replace(p,'计算未超出半径观测范围。',f'计算未超出半径观测范围。同用附录4物性时，固定半径对照需{fixed:.4f} h，收缩使预测时长减少{delta:.4f} h（约{pct:.2f}\\%）。')
    p=P/'sections/08_evaluation.tex'
    replace(p,'未来可在补充测量范围后开展环境敏感性、相同物性下收缩与固定域对照；现有资料不支持给出这些扩展的实验结论。',
            '同物性下的固定域与收缩域对照已完成，但环境敏感性和实测预测验证仍待开展；数值对照不能代替真实药材试验。')
    replace(p,'全域阈值计算给出固定半径模型的报告时长57.4731 h、给定收缩模型的报告时长51.0877 h。',
            '全域阈值计算给出附录3固定半径模型的报告时长57.4731 h、附录4给定收缩模型的报告时长51.0877 h。')
    replace(p,'且移动边界计算未超出半径观测范围。',f'且移动边界计算未超出半径观测范围。补充的附录4固定半径对照报告时长为{fixed:.4f} h，在相同物性与环境条件下，收缩使模型预测时长缩短{delta:.4f} h，约占固定组的{pct:.2f}\\%。')
    p=P/'sections/07_validation.tex'
    s=p.read_text(encoding='utf-8')
    addition=r'''\subsection{同物性固定半径对照的检验}
新增对照沿用附录4及第四问的积分配置，独立以物理环层组装检查常半径算子。$G_8/G_{16}$和$G_8$时间收紧的临界时间差分别为0.498231 s、0.013113 s；至132 h共同保存时刻的空间温度、含水率最大差分别为$1.3522\times10^{-5}$ $^\circ$C、$1.9052\times10^{-6}$ kg/kg，时间加密差分别为$1.4730\times10^{-5}$ $^\circ$C、$6.4161\times10^{-8}$ kg/kg。三组累计水分相对残差均低于$10^{-6}$。固定组在129.8448 h的三个未舍入最大值均低于0.15，生产最大值加经验裕量$1.9437\times10^{-7}$后也仍达标。该检验支持表\ref{tab_q4_control}的数值可比性；第四问原收缩结果和六张题定表均保持不变。

'''
    if addition not in s: p.write_text(s.replace(r'\subsection{局部敏感性与适用边界}',addition+r'\subsection{局部敏感性与适用边界}'),encoding='utf-8')
    p=P/'sections/09_declaration.tex'
    replace(p,'中文正文起草、公式与结果的一致性检查以及LaTeX排版。','中文正文起草、公式与结果的一致性检查、同物性固定半径对照的程序编写与数值验证、比较图绘制以及LaTeX排版。')
    p=P/'ai_details.tex'
    replace(p,r'\section*{四、历史使用记录的边界}',r'''\section*{补充：同物性收缩对照}
在后续明确要求评估并补算、修改论文的交互中，AI编写附录4固定半径对照程序，复用既有物性与有限体积算子，实际完成$G_8$、$G_{16}$及$G_8$时间收紧计算，检查全域阈值、水分收支、状态范围和同时间网格差。新增固定组报告时长129.8448 h，与既有收缩组51.0877 h相比减少78.7571 h，约60.65\%。AI生成比较曲线，更新第四问、摘要、检验与结论并重新编译检查。原四问主模型、原Excel和生产结果未被覆盖；新增结论限定于相同物性及既定环境假设下的模型对照。上述自动核验仍不代表参赛队已完成最终人工审阅。

\section*{四、历史使用记录的边界}''')
    shutil.copy2(ROOT/'figures/q4_fixed_vs_shrink.pdf',P/'figures/q4_fixed_vs_shrink.pdf')
    sup=P/'support'; (sup/'results/q4_fixed_comparison').mkdir(parents=True,exist_ok=True)
    for name in ['q4_fixed_comparison.py','plot_q4_fixed_comparison.py']:
        shutil.copy2(ROOT/'code'/name,sup/'code'/name)
    for f in O.iterdir():
        if f.suffix in ['.json','.csv']: shutil.copy2(f,sup/'results/q4_fixed_comparison'/f.name)
    p=P/'sections/appendix.tex'
    s=p.read_text(encoding='utf-8')
    appendix=r'''
\subsection*{补充对照程序与复现}
附录4固定半径对照的完整程序如下。复算依次运行：
\begin{Verbatim}[fontsize=\small,breaklines=true]
python code/q4_fixed_comparison.py --level 8
python code/q4_fixed_comparison.py --level 16
python code/q4_fixed_comparison.py --level 8 --tight
python code/q4_fixed_comparison.py --summarize
python code/plot_q4_fixed_comparison.py
\end{Verbatim}
汇总需先按前述步骤生成第四问原收缩结果。若仅复核图形，可直接使用支撑材料所附的对照JSON与两组中心曲线CSV；较大的固定组内部数组可重算。
\VerbatimInput[fontsize=\fontsize{7.5}{9}\selectfont,breaklines=true,breakanywhere=true,numbers=left,numbersep=5pt,xleftmargin=12pt]{support/code/q4_fixed_comparison.py}
\VerbatimInput[fontsize=\fontsize{7.5}{9}\selectfont,breaklines=true,breakanywhere=true,numbers=left,numbersep=5pt,xleftmargin=12pt]{support/code/plot_q4_fixed_comparison.py}
'''
    if appendix not in s: p.write_text(s+appendix,encoding='utf-8')
    p=sup/'README.md';s=p.read_text(encoding='utf-8')
    add='\n## 2026-09-12 同物性收缩对照补充\n\n新增code/q4_fixed_comparison.py和plot_q4_fixed_comparison.py。依次运行前者 --level 8、--level 16、--level 8 --tight、--summarize，最后运行绘图脚本。汇总前需已生成原q4_solution.npz和q4_validation.json；仅重绘可直接读取附带的results/q4_fixed_comparison/两份CSV及comparison.json，不必重算PDE。新增固定组不读取实测半径作为演化输入，不外推半径；后4小时沿用50°C、0.05kg/kg环境。详见reports/Q4_FIXED_COMPARISON_REPORT.md。\n'
    if add not in s:p.write_text(s+add,encoding='utf-8')
    report=f'''# 第四问同物性固定半径与收缩对照

版本：q4-fixed-comparison-v1。用户本轮明确要求评估此项对照，必要时开始计算并修改论文；据此完成本项补算与论文整合，不另记用户已人工验收新数值。

## 设计及沿用内容

复用q4-model-v1的附录4经验物性、28°C和2.55kg/kg初值、h=25、hm=8e-7、有效热湿方程与全域最大值阈值0.15。前4小时使用同一附件PCHIP，后期50°C、0.05kg/kg。唯一干预为将实测R(t)替换为恒定R0=0.02m；不改原主模型。固定组用相同材料坐标有限体积实现取R常数，并通过独立物理环层算子核对。它是模型反事实对照，不是药材实测因果效应。

## 结果

| 指标 | 数值 |
|---|---:|
| 固定半径临界时间/h | {v['fixed_critical_h']:.10f} |
| 固定半径严格报告时间/h | {fixed:.4f} |
| 收缩严格报告时间/h | {shrink:.4f} |
| 节省时间/h | {delta:.4f} |
| 相对固定组节时百分比 | {pct:.8f}% |
| 两组临界根之差/h | {v['saving_critical_h']:.10f} |
| 固定组报告最大含水率/kg/kg | {v['fixed_report_maxima']['G8']:.12f} |
| 固定组空间加密事件差/s | {v['fixed_event_space_s']:.9f} |
| 固定组时间加密事件差/s | {v['fixed_event_time_s']:.9f} |

固定组G8/G16空间温度与含水率最大差分别为{v['fixed_spatial_T_C'][0]:.8e}°C、{v['fixed_spatial_T_C'][1]:.8e}kg/kg；时间收紧差分别为{v['fixed_temporal_T_C'][0]:.8e}°C、{v['fixed_temporal_T_C'][1]:.8e}kg/kg。比较覆盖0–132h的共同60s保存轨迹。原生BDF接受状态另检查范围；所有保存状态有限。

三组全部质量相对残差低于1e-6，热方程加权残差低于1e-6；后者不代表完整多相能量守恒。原收缩组引用q4_validation.json的既有验证，未重跑。两组输入附件哈希一致。固定组报告时刻在三配置上均低于阈值，生产值加经验裕量后仍低于阈值。全部{len(v['checks'])}项检查通过，详见comparison.json，不把该裕量称严格连续方程误差界。

## 图表、论文与来源

- results/q4_fixed_comparison/comparison.json：未舍入指标与全部门禁。
- 同目录G8/G16/G8_tight.npz及JSON：场、配置、逐段运行记录、源码/附件哈希。
- 同目录fixed_center.csv、shrink_center.csv：图中全精度数据。两条曲线止于各自报告时刻，不将收缩曲线延续到固定组終时。
- code/q4_fixed_comparison.py：可复算程序；code/plot_q4_fixed_comparison.py：独立重绘。
- figures/q4_fixed_vs_shrink.pdf与PNG：左图全过程、右图后期放大；中心在保存轨迹与全域最大值浮点一致。
- paper/guosai2026/sections/06_q4.tex：新增同物性对照表、节时公式和图。替换原重复的中心/表面历程图，径向剖面和全部六张题定表保留。摘要、检验、结论及AI说明同步更新。

## 解释边界

固定组约129.84h超过72h半径记录，但其半径指定恒定，不需要半径外推。其长期环境是假定延续；结果不证明真实固定尺寸药材需要相同时长。差值包含几何变化引起的内部扩散、边界面积体积比、温湿物性反馈总效应。第三问附录3与第四问附录4的直接差值仍不能归因于收缩。现有有效热容量、等效水分边界、径向近似的物理限制保持。

## 复现

Python D:/python/python.exe（既有NumPy2.5.1、SciPy1.18.0）。依次运行 code/q4_fixed_comparison.py --level 8；--level 16；--level 8 --tight；--summarize，然后code/plot_q4_fixed_comparison.py。补算日志在tmp/q4_fixed_*.log；运行止于阈值穿越后的6h分段终点132h，240h仅为失败退出上限。

正文与原完整PDF备份在tmp/q4_comparison_paper_backup，原结果保护哈希见该目录protected_hashes.json。最终PDF与压缩包核验另见交付核验记录。
'''
    (ROOT/'reports/Q4_FIXED_COMPARISON_REPORT.md').write_text(report,encoding='utf-8')
    shutil.copy2(ROOT/'reports/Q4_FIXED_COMPARISON_REPORT.md',sup/'reports/Q4_FIXED_COMPARISON_REPORT.md')
    entry='\n\n## 2026-09-12 同物性收缩对照补充\n\n已按本轮用户指令完成q4-fixed-comparison-v1补算、技术核验与论文整合。附录4固定半径129.8448h，对比实测收缩51.0877h，节时78.7571h（60.65%）；结果限定于既定有效模型与环境。来源、配置、验证及论文位置见reports/Q4_FIXED_COMPARISON_REPORT.md。原四问主结果保持。执行与写作已获本轮授权，未代记用户已完成新结果人工验收。\n'
    for rel in ['reports/RESULTS_REPORT.md','reports/PAPER_NOTES.md','reports/REVIEW_LOG.md','reports/models/q4.md']:
        path=ROOT/rel;s=path.read_text(encoding='utf-8')
        if entry not in s:path.write_text(s+entry,encoding='utf-8')
    path=ROOT/'reports/STATE.md';s=path.read_text(encoding='utf-8')
    if entry not in s:path.write_text(entry.strip()+'\n\n'+s,encoding='utf-8')
    manifest=json.loads((sup/'source_manifest.json').read_text(encoding='utf-8'))
    for name in ['q4_fixed_comparison.py','plot_q4_fixed_comparison.py']:
        sha=hashlib.sha256((ROOT/'code'/name).read_bytes()).hexdigest()
        if not any(x['file']=='code/'+name for x in manifest):
            manifest.append({'file':'code/'+name,'original_sha256':sha,'packaged_sha256':sha,'adaptation':'none'})
    (sup/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Verified comparison integrated into manuscript and support materials')


if __name__=='__main__':main()
