"""Package only reviewed deliverables, excluding numerical caches and test logs."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'paper' / 'guosai2026' / '支撑材料_按问复现'


def main():
    evidence = json.loads((PACKAGE / 'reproduction_verification.json').read_text(encoding='utf-8'))
    if evidence.get('pass') is not True:
        raise RuntimeError('Complete relocated verification must pass before packaging')
    paths = sorted(p for p in PACKAGE.rglob('*') if p.is_file())
    if any(part in ('_runtime', 'results', '__pycache__') for p in paths for part in p.relative_to(PACKAGE).parts):
        raise RuntimeError('Do not distribute generated caches or large solver arrays')
    path_pattern = re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/(?:Users|home)/')
    for p in paths:
        if p.suffix in ('.py', '.md', '.txt', '.json'):
            text = p.read_text(encoding='utf-8')
            if path_pattern.search(text):
                raise RuntimeError('Absolute filesystem path found in ' + p.name)
        elif p.suffix == '.xlsx':
            with zipfile.ZipFile(p) as workbook:
                for name in workbook.namelist():
                    if name.endswith(('.xml', '.rels')) and path_pattern.search(workbook.read(name).decode('utf-8')):
                        raise RuntimeError('Absolute filesystem path found inside ' + p.name)
    hashes = {p.relative_to(PACKAGE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in paths if p.name != 'file_manifest.json'}
    (PACKAGE / 'file_manifest.json').write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = PACKAGE.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PACKAGE.rglob('*')):
            if p.is_file():
                z.write(p, PACKAGE.name + '/' + p.relative_to(PACKAGE).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('Archive integrity check failed')
        for name, expected in hashes.items():
            if hashlib.sha256(z.read(PACKAGE.name + '/' + name)).hexdigest() != expected:
                raise RuntimeError('Archive content mismatch')
    count = sum(row['numeric_answer_cells'] for row in evidence['comparison']['checks'])
    maximum = max(row['maximum_absolute_difference'] for row in evidence['comparison']['checks'])
    report = f'''# 按问复现支撑材料整理与验证

交付目录：paper/guosai2026/支撑材料_按问复现/

压缩包：paper/guosai2026/支撑材料_按问复现.zip

按照用户提供的参考，将四问代码分别内嵌到Q1.py至Q4.py。配齐原始附件、模板、原答案对照、依赖清单和逐格验证程序。模型求解不读取原答案对照文件。

原方程、物性、初边值、网格、容差和数值检查保留。修改限于相对文件定位、Excel导出及执行步骤串联。第三问本机专用Node导出改为openpyxl，并保留原发布检查；第四问自动运行六组计算后核验导出。

实际将交付包复制到新的目录，从不同的当前工作目录启动；测试开始时不存在结果或缓存，从原始附件完整重算四问。全部过程返回成功，共比较{count}个答案数值单元格，最大绝对差为{maximum:g}，四位小数差异为0。工作表名称、尺寸、时间/径向坐标和域外空格也通过检查。原正式四个Excel的SHA256未改变。

额外检查：故意令第二问验证项失败，确认新的导出流程阻止写出Excel。文本文件绝对路径扫描通过；压缩包CRC与逐文件SHA256检查通过。

交付包没有数值缓存、临时测试日志或个人绝对路径。重算过程中会在收件人本机生成新的相对输出目录。依赖版本与原环境一致，本次实际验证使用Python 3.14.6；其他系统和版本未逐一测试。

本次未修改论文正文、原模型代码、原数据和原正式答案。额外二维、潜热、敏感性与同物性对照程序仍在原支撑材料中，本包聚焦四个主答案。

机器验证明细见交付目录内reproduction_verification.json；代码来源映射见source_manifest.json；交付文件校验见file_manifest.json。
'''
    (ROOT / 'reports' / 'QUESTION_REPRODUCTION_20260913.md').write_text(report, encoding='utf-8')
    print(json.dumps({'archive_bytes': archive.stat().st_size, 'answer_cells': count,
                      'maximum_absolute_difference': maximum, 'pass': True}))


if __name__ == '__main__':
    main()
