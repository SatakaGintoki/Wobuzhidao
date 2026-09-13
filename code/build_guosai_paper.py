"""Build paper tables from unrounded arrays; preserve every original result."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/guosai2026'

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def table(name, caption, label, hours, values, time_heading, note='', radius=None):
    columns = len(values[0]) + 1 + (radius is not None)
    header = [time_heading, '0', '0.5', '1.0', '1.5', '2.0']
    if values.shape[1] == 6:
        header += ['药材表面']
    if radius is not None:
        header += ['$R(t)$/cm']
    out = [r'\begin{table}[htbp]\centering\small',
           r'\caption{'+caption+r'}\label{'+label+'}',
           r'\renewcommand{\arraystretch}{1.12}',
           r'\begin{tabular}{'+'c'*columns+r'}\toprule',
           r' & \multicolumn{'+str(values.shape[1])+r'}{c}{到药材中心的距离/cm}'+ (' & ' if radius is not None else '') +r'\\',
           ' & '.join(header)+r'\\\midrule']
    records=[]
    for i,(t,row) in enumerate(zip(hours, values)):
        ts = f'{t:.4f}' if not np.isclose(t,round(t),rtol=0,atol=1e-7) and t>6 else f'{t:g}'
        cells = [f'{v:.4f}' if np.isfinite(v) else '' for v in row]
        if radius is not None:
            cells += [f'{radius[i]*100:.4f}']
        out.append(' & '.join([ts]+cells)+r'\\')
        records.append({'time':float(t),'values':[None if not np.isfinite(v) else float(v) for v in row], 'formatted':cells})
    out += [r'\bottomrule\end{tabular}']
    if note:
        out += [r'\par\vspace{3pt}\begin{minipage}{.96\linewidth}\footnotesize '+note+r'\end{minipage}']
    out += [r'\end{table}']
    write(PAPER/'tables'/f'{name}.tex','\n'.join(out)+'\n')
    return records

def main():
    tables={}
    source_hashes={}
    for q in range(1,5):
        src=ROOT/f'results/q{q}_solution.npz'
        source_hashes[str(src.relative_to(ROOT))]=hashlib.sha256(src.read_bytes()).hexdigest()
        z=np.load(src)
        if q in (1,2):
            tt=np.array([100,300,600,900,1200,1500,1800]) if q==1 else np.arange(1800,10801,1800)
            ids=np.searchsorted(z['times'],tt)
            assert np.array_equal(z['times'][ids],tt)
            for f,kind,unit in [('T','温度',r'$^\circ$C'),('C','水分浓度','kg/kg')]:
                vals=z[f+'_out'][ids][:,[0,5,10,15,20]]
                tables[f'q{q}{f}']=table(f'q{q}{f}',f'{"30分钟" if q==1 else "3小时"}内药材的{kind}（{unit}）',f'tab_q{q}{f}',tt if q==1 else tt/3600,vals,'时间/s' if q==1 else '时间/h')
        elif q==3:
            tables['q3C']=table('q3C','固定半径模型药材烘干过程的水分浓度（kg/kg）','tab_q3C',z['table_hours'],z['C_table'],'时间/h',r'注：终时中心未舍入值为0.1499993913 kg/kg，严格低于0.15；0.1500为四位显示。')
        else:
            ids=np.searchsorted(z['times_s'],z['table_times_s'])
            assert np.allclose(z['times_s'][ids],z['table_times_s'],rtol=0,atol=1e-8)
            tables['q4C']=table('q4C','收缩模型药材烘干过程的水分浓度（kg/kg）','tab_q4C',z['table_times_s']/3600,z['table_C'],'时间/h',r'注：域外位置留空，药材表面对应当前$R(t)$。终时中心未舍入值为0.1499989333 kg/kg。',z['radius_m'][ids])
        z.close()
    figs=['q1_oven_input','q1_T_profiles','q1_C_profiles','q2_T_profiles','q2_C_profiles','q3_C_max_history','q3_C_profiles','q3_axisymmetric_check','q4_R_history','q4_C_history','q4_C_profiles']
    (PAPER/'figures').mkdir(exist_ok=True)
    for f in figs:
        shutil.copy2(ROOT/f'figures/{f}.pdf',PAPER/f'figures/{f}.pdf')
    write(PAPER/'qa/table_sources.json',json.dumps({'source_sha256':source_hashes,'tables':tables},ensure_ascii=False,indent=2))
    print(json.dumps({'tables':len(tables),'figures':len(figs),'numeric_cells':sum(sum(v is not None for v in row['values']) for rows in tables.values() for row in rows)},ensure_ascii=False))

if __name__=='__main__':
    main()
