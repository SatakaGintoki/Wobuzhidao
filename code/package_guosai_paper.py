"""Prepare source appendix and compact support directory, without changing results."""
from pathlib import Path
import hashlib,json,re,shutil

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper/guosai2026'
SUP=PAPER/'support'
SOURCES=['utils.py','appendix3.py','radial_fvm.py','radial_coupled.py','q1_analytic.py','delivery.py',
         'problem1.py','problem2.py','problem3.py','q3_balance.py','q3_closeout.py','problem4.py',
         'verify_q4_results.py','plot_q3_results.py','verify_closeout.py','verify_q2_results.py',
         'verify_q3_closeout.py','verify_q4_delivery.py']

def write(p,t):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(t,encoding='utf8')

def main():
    manifest=[]
    for name in SOURCES:
        src=ROOT/'code'/name
        content=src.read_text(encoding='utf8')
        if name=='q3_closeout.py':
            content=re.sub(r"NODE=Path\('[^']*node.exe'\)","NODE=Path(__import__('shutil').which('node') or 'node')",content)
        dest=SUP/'code'/name
        write(dest,content)
        compile(content,str(dest),'exec')
        manifest.append({'file':'code/'+name,'original_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                         'packaged_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
                         'adaptation':'Node path uses PATH; numerical code unchanged' if name=='q3_closeout.py' else 'none'})
    for sub in ['q3_export','q4_export']:
        for name in (['build.mjs','gate.mjs','test_gate.mjs'] if sub=='q3_export' else ['build.mjs']):
            txt=(ROOT/'tmp'/sub/name).read_text(encoding='utf8')
            if sub=='q3_export' and name=='build.mjs':
                # Reuse a local bundled workbook as the import layout, not a historical archive dependency.
                txt=txt.replace("results/archive/q3-pre-closeout-20260911/results/result3.xlsx","results/result3.xlsx")
            write(SUP/'tmp'/sub/name,txt)
    (SUP/'results').mkdir(parents=True,exist_ok=True)
    for q in range(1,5):
        for suffix in [f'result{q}.xlsx',f'q{q}_validation.json']:
            shutil.copy2(ROOT/'results'/suffix,SUP/'results'/suffix)
    for pattern in ['q*_table*.csv','q4_radius_output.csv']:
        for p in (ROOT/'results').glob(pattern):
            shutil.copy2(p,SUP/'results'/p.name)
    for f in ['Q12_CLOSEOUT_REPORT.md','Q3_VERIFY_REPORT.md','Q4_VERIFY_REPORT.md','PAPER_CITATION_AUDIT.md']:
        s=(ROOT/'reports'/f).read_text(encoding='utf8')
        s=s.replace('C:/Users/chens/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe','node')
        s=s.replace('D:/python/python.exe','python')
        write(SUP/'reports'/f,s)
    # Raw contest attachments are omitted from the submission support archive; instructions identify locations.
    write(SUP/'requirements.txt','numpy\nscipy\nopenpyxl\nmatplotlib\npypdfium2\npillow\n')
    write(SUP/'source_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    write(SUP/'README.md',r'''# 支撑材料使用说明

本文计算使用 Python、NumPy、SciPy、openpyxl 与 Matplotlib。原生产环境记录为 Python 3.14.6、NumPy 2.5.1、SciPy 1.18.0；程序相对项目根读取文件。Excel 3、4 的原导出脚本另需 Node.js 与 @oai/artifact-tool；已包含正式结果文件。

## 输入位置

把赛题原始附件置于 data/附件/附件1.xlsx、data/附件/附件2.xlsx、data/附件/附件3/result1.xlsx 至 result4.xlsx。原题数据按官方要求不重复放入支撑材料压缩包。

## 复算数值

先安装 requirements.txt 中依赖，在本目录运行：

```text
python code/problem1.py
python code/problem2.py
python code/problem3.py --no-xlsx
python code/problem4.py --level 2
python code/problem4.py --level 4
python code/problem4.py --level 4 --tight
python code/problem4.py --level 8
python code/problem4.py --level 16
python code/problem4.py --level 8 --tight
python code/verify_q4_results.py
python code/plot_q3_results.py
```

上述过程重新计算四问及所用加密对照并生成NPZ/CSV/图；第3问 --no-xlsx 不重新导出Excel，现有随附结果表保留。第1、2问脚本会覆盖本支撑目录下对应结果，建议在副本中复算。各类目录由程序建立，必要时预先创建 results、figures、reports、tmp。

## 原Excel 3、4导出路径

第3问完整导出需要预先配置 Node.js 和 @oai/artifact-tool 并运行不带 --no-xlsx 的 problem3.py；第4问数值核验完成后执行 node tmp/q4_export/build.mjs。Node 模块须能从两个脚本目录解析。若只需复核方程、NPZ和CSV，则不依赖Node。第3问导入随附result3.xlsx作为原布局。

## 程序附录与变更范围

code/ 包含全文模型、计算与对应验证所用18个完整Python文件；tmp/ 包含4个原Excel导出/门禁脚本。附录逐字载入这些文件。仅把原计算机的Node绝对路径改为从PATH查找，并把第三问历史Excel模板路径改为随附结果表路径；未改物性、方程、积分容差、网格或数值流程。哈希映射见source_manifest.json。

较大的NPZ与网格诊断数组可按上述指令重建，不放入20MB以内的支撑材料包。报告中历史工作区归档路径是既有验证的来源记录，不表示本压缩包已包含全部历史备份。部分历史回归脚本需先生成完整诊断目录再运行。

## AI记录

AI工具使用详情.pdf记录本次可确认的工具、用途与核验边界；历史工具版本及人工逐项核验须由参赛队据实补全，不能把自动检查等同于人工审阅。
''')
    intro=r'''\section*{附录A\quad 支撑材料清单与复现说明}
支撑材料包含\texttt{code/}中的18个Python源文件、\texttt{tmp/}中的4个JavaScript导出与检查脚本、四个正式Excel结果文件、题定结果CSV、四问验证JSON、主要验证报告、依赖清单、源文件哈希映射和AI工具使用详情。赛题原始数据按原附件目录放置，较大的内部网格数组可通过程序复算生成。

Python依赖为NumPy、SciPy、openpyxl和Matplotlib；原生产运行记录为Python 3.14.6、NumPy 2.5.1、SciPy 1.18.0。代码采用相对项目根目录，需提供\texttt{data/附件/附件1.xlsx}、\texttt{附件2.xlsx}及\texttt{附件3/}中的题给模板。所有初值、物性和时间单位与正文一致。

按下列次序可复算四问数值与所用加密对照。第三问使用\texttt{--no-xlsx}可独立复核数值而不依赖Node；随附正式Excel不受该参数更新。
\begin{Verbatim}[fontsize=\small,breaklines=true]
python code/problem1.py
python code/problem2.py
python code/problem3.py --no-xlsx
python code/problem4.py --level 2
python code/problem4.py --level 4
python code/problem4.py --level 4 --tight
python code/problem4.py --level 8
python code/problem4.py --level 16
python code/problem4.py --level 8 --tight
python code/verify_q4_results.py
python code/plot_q3_results.py
\end{Verbatim}
原第3、4问Excel导出脚本依赖Node.js与\texttt{@oai/artifact-tool}。配置依赖后，第3问不加\texttt{--no-xlsx}运行，第4问执行\texttt{node tmp/q4\_export/build.mjs}。支撑材料附完整导出脚本。为使代码可迁移，仅将原计算机的Node路径改为从PATH查找，将第3问布局模板路径改为随附结果文件；数值方程与参数保持原实现。

以下列出本论文模型与验证所使用的完整源程序。部分文件保留历史诊断函数；正式入口及当前输出以以上复现顺序为准。各程序运行会在本地生成结果与诊断文件，宜在支撑材料副本中执行。
\section*{附录B\quad 完整源程序}
'''
    parts=[intro]
    paths=[SUP/'code'/s for s in SOURCES]+list((SUP/'tmp').rglob('*.mjs'))
    for i,p in enumerate(paths,1):
        name=p.relative_to(SUP).as_posix()
        parts.append(r'\subsection*{B.'+str(i)+r'\quad\texttt{'+name.replace('_',r'\_')+'}}\n')
        parts.append(r'\VerbatimInput[fontsize=\fontsize{7.5}{9}\selectfont,breaklines=true,breakanywhere=true,numbers=left,numbersep=5pt,xleftmargin=12pt]{support/'+name+'}\n')
    write(PAPER/'sections/appendix.tex','\n'.join(parts))
    print(json.dumps({'python_files':len(SOURCES),'appendix_files':len(paths),'source_bytes':sum(p.stat().st_size for p in paths)}))

if __name__=='__main__': main()
