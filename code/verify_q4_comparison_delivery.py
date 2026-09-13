"""Audit the new comparison, protected baseline files and delivered archives."""
from pathlib import Path
import hashlib
import json
import shutil
from zipfile import ZipFile
import numpy as np
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper/guosai2026'
D=ROOT/'论文交付_20260912_收缩对照'
O=ROOT/'results/q4_fixed_comparison'


def main():
    v=json.loads((O/'comparison.json').read_text(encoding='utf-8'))
    assert v['pass'] and all(v['checks'].values())
    hashes=json.loads((ROOT/'tmp/q4_comparison_paper_backup/protected_hashes.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    assert abs(v['saving_report_h']-(v['fixed_report_h']-v['shrink_report_h']))<1e-10
    assert abs(v['saving_percent']-100*v['saving_report_h']/v['fixed_report_h'])<1e-10
    for key,path in [('fixed',O/'fixed_solution.npz'),('shrink',ROOT/'results/q4_solution.npz')]:
        z=np.load(path); csv=np.loadtxt(O/f'{key}_center.csv',delimiter=',',skiprows=1,encoding='utf-8-sig')
        assert np.array_equal(csv[:,0],z['times_s'])
        assert np.array_equal(csv[:,1],z['Y'][:,len(z['xi'])])
    reading=pdfium.PdfDocument(str(D/'药材烘干论文_正文阅读版.pdf'))
    full=pdfium.PdfDocument(str(D/'药材烘干论文_含完整程序附录.pdf'))
    for i in range(len(reading)):
        assert reading[i].get_textpage().get_text_range()==full[i].get_textpage().get_text_range()
    txt='\n'.join(reading[i].get_textpage().get_text_range() for i in range(len(reading)))
    for token in ['129.8448','78.7571','60.65','同物性对照与收缩贡献']:
        assert token in txt
    table=(P/'sections/06_q4.tex').read_text(encoding='utf-8')
    assert '该对照未做' not in table
    archive_info={}
    for name in ['药材烘干论文_Overleaf源码.zip','支撑材料.zip']:
        with ZipFile(D/name) as z:
            assert z.testzip() is None
            prefix='support/' if name.startswith('药材') else ''
            for file in ['q4_fixed_comparison.py','plot_q4_fixed_comparison.py']:
                assert z.read(prefix+'code/'+file)==(ROOT/'code'/file).read_bytes()
            assert z.read(prefix+'results/q4_fixed_comparison/comparison.json')==(O/'comparison.json').read_bytes()
            assert z.read(prefix+'results/q4_fixed_comparison/fixed_center.csv')==(O/'fixed_center.csv').read_bytes()
            if prefix:
                assert z.read('sections/06_q4.tex')==(P/'sections/06_q4.tex').read_bytes()
                assert z.read('figures/q4_fixed_vs_shrink.pdf')==(ROOT/'figures/q4_fixed_vs_shrink.pdf').read_bytes()
            archive_info[name]={'members':len(z.namelist()),'bytes':(D/name).stat().st_size,'crc_pass':True}
    qa=json.loads((P/'qa_comparison/verification.json').read_text(encoding='utf-8'))
    out={'comparison_pass':True,'protected_files_unchanged':len(hashes),'original_table_cells_checked':qa['total_cells'],
         'reading_pages':len(reading),'full_pages':len(full),'reading_matches_full_body':True,
         'figure_csv_matches_sources':True,'new_values_in_pdf':True,'archives':archive_info,
         'visual_review':'Comparison figure, updated page 25, validation page 28, conclusion page 29, abstract contact sheet and AI statement inspected.'}
    (D/'新增对照核验.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copy2(ROOT/'reports/Q4_FIXED_COMPARISON_REPORT.md',D/'第四问同物性对照报告.md')
    (D/'阅读说明.md').write_text('''# 同物性收缩对照更新版

本目录为2026-09-12完成附录4固定半径对照后的最新交付，基于此前组员合稿更新。

优先阅读“药材烘干论文_正文阅读版.pdf”（30页）：第25页8.6节包含对照设计、表8、节时公式和图8；第28页9.4节为新增验证；摘要和第29页结论已同步更新。

相同附录4物性与既定环境下，固定半径组严格达标129.8448h，实测收缩组51.0877h；预测节时78.7571h，即固定组时长的60.65%。这是模型中的几何干预对照，保留有效热容量、等效水分边界和长期环境假设的限制。

原四问生产结果和四个Excel保持不变，六张题定表216个有效数值重新核对通过。新的两组中心曲线替换原中心/表面历程展示，原径向剖面和题定表保留。

“药材烘干论文_含完整程序附录.pdf”共101页，前30页与阅读版一致；含新增补算与绘图程序。“AI工具使用详情.pdf”已补记这次计算与写作范围。

“药材烘干论文_Overleaf源码.zip”含完整更新源码、图、代码和支撑材料。上传后选择XeLaTeX，完整版本编译main.tex，阅读版编译reading.tex。“支撑材料.zip”含原结果、新增JSON/CSV、程序与复现说明；较大内部NPZ可重算。

计算与验证详见“第四问同物性对照报告.md”和“新增对照核验.json”。本轮技术核验与论文修改已完成，不代替参赛队最终人工审阅。
''',encoding='utf-8')
    update='\n> 交付完成：最新目录为论文交付_20260912_收缩对照/；阅读版30页、完整程序版101页，第25页为同物性对照。新增14项数值检查及交付审计通过，13个受保护文件哈希不变，原六表216个有效数值一致。新结果已依本轮指令写入论文，未代记人工验收。\n'
    s=(ROOT/'reports/STATE.md').read_text(encoding='utf-8')
    if update not in s:(ROOT/'reports/STATE.md').write_text(update+'\n'+s,encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False))


if __name__=='__main__': main()
