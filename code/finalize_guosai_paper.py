"""Copy verified PDFs and create reviewable Overleaf/support archives."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,json,hashlib

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper/guosai2026'
D=ROOT/'论文交付_20260912'

def archive(path,files,base):
    with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for f in sorted(files):
            if f.is_file(): z.write(f,f.relative_to(base).as_posix())
    with ZipFile(path) as z: assert z.testzip() is None
    assert path.stat().st_size<20*1024*1024

def main():
    D.mkdir(exist_ok=True)
    shutil.copy2(P/'reading.pdf',D/'药材烘干论文_正文阅读版.pdf')
    shutil.copy2(P/'main.pdf',D/'药材烘干论文_含完整程序附录.pdf')
    shutil.copy2(P/'ai_details.pdf',D/'AI工具使用详情.pdf')
    shutil.copy2(P/'ai_details.pdf',P/'support/AI工具使用详情.pdf')
    allowed=[]
    for f in P.rglob('*'):
        rel=f.relative_to(P)
        if not f.is_file() or rel.parts[0]=='qa' or '__pycache__' in rel.parts:continue
        if f.suffix in {'.tex','.mjs','.py','.md','.json','.xlsx','.csv','.txt'} or f.name=='latexmkrc' or (rel.parts[0]=='figures' and f.suffix=='.pdf') or rel.as_posix()=='support/AI工具使用详情.pdf':
            allowed.append(f)
    archive(D/'药材烘干论文_Overleaf源码.zip',allowed,P)
    archive(D/'支撑材料.zip',[f for f in (P/'support').rglob('*') if '__pycache__' not in f.parts],P/'support')
    q=json.loads((P/'qa/verification.json').read_text(encoding='utf8'))
    manifest={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in D.iterdir() if f.suffix in {'.pdf','.zip'}}
    (D/'交付核验.json').write_text(json.dumps({'files':manifest,'table_cells':216,'reading_pages':21,'full_pages':87,'source_hashes_unchanged':True},ensure_ascii=False,indent=2),encoding='utf8')
    (D/'阅读说明.md').write_text('''# 药材烘干论文交付

优先阅读“药材烘干论文_正文阅读版.pdf”：共21页，包含摘要、完整四问推导、题定表1至表6、检验与结论、AI声明和参考文献。它省略源代码附录，供修改阅读。

“药材烘干论文_含完整程序附录.pdf”共87页，前21页与阅读版内容一致，后附完整数值程序和支撑材料说明。

“药材烘干论文_Overleaf源码.zip”解压或上传Overleaf后选择XeLaTeX，主文件main.tex；若只编译阅读版，选择reading.tex。所有引用的图、分章节源码及程序附录文件已打包，无需从旧论文目录补文件。单独AI说明主文件ai_details.tex。

“支撑材料.zip”含四个原结果Excel、完整模型/验证代码、结果CSV、验证JSON、使用说明和AI工具使用详情。原题附件不重复打包，内部大数组可复算。复算入口与依赖见包内README。

本轮六张题定表216个有效数值已与未舍入NPZ独立核对，正文未加入尚未完成的参数、潜热或二维实验。原论文、原数值代码和原结果保留，新稿独立存于paper/guosai2026。

请在提交前由队伍人工审阅全文，特别核对有效热容量、等效水分边界、比例收缩与后4小时环境假设；补齐此前AI工具的真实版本、使用过程和人工修改核验记录。AI说明目前准确记录本次可确认范围，没有替队伍声明已经完成所有人工核验。最终文件名、纸质承诺书和编号页按本赛区实际要求处理。
''',encoding='utf8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
