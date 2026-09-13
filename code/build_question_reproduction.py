"""Build readable, self-contained Q1-Q4 scripts from the current solvers."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'paper' / 'guosai2026' / '支撑材料_按问复现'
COMMON = ['utils', 'delivery', 'q1_analytic', 'radial_fvm', 'reproduction_export']
COUPLED = ['appendix3', 'radial_coupled', 'problem2']
MODULES = {
    1: COMMON + ['problem1'],
    2: COMMON + COUPLED,
    3: COMMON + COUPLED + ['q3_balance', 'problem3', 'q3_closeout'],
    4: COMMON + COUPLED + ['problem4', 'verify_q4_results'],
}

HEADER = '''# -*- coding: utf-8 -*-
"""问题 {question}：从原始附件复算答案数据。

运行 python Q{question}.py；检查环境 python Q{question}.py --check。
本文件内嵌本问所需的全部项目模块，模块源码在下方按文件名分段列出。
运行时自动展开到相对目录 _runtime/Q{question}/code，以支持源码哈希核验。
输入、输出均相对于本文件的位置，与当前工作目录无关。
方程、物性、网格、容差和验证判据沿用原正式求解程序。
"""
import argparse
import importlib
import os
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parent
QUESTION = {question}
SOURCES = {{}}
'''

FOOTER = '''
def prepare():
    code_dir = PACKAGE_ROOT / '_runtime' / f'Q{QUESTION}' / 'code'
    code_dir.mkdir(parents=True, exist_ok=True)
    for name, source in SOURCES.items():
        (code_dir / (name + '.py')).write_text(source, encoding='utf-8')
    sys.path.insert(0, str(code_dir))
    for folder in ('results', 'figures', 'reports'):
        (PACKAGE_ROOT / folder).mkdir(exist_ok=True)
    os.environ.setdefault('MPLBACKEND', 'Agg')
    for name in SOURCES:
        importlib.import_module(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check imports and original inputs without solving')
    parser.add_argument('--export-only', action='store_true', help='Export existing validated NPZ arrays; does not solve the model')
    args = parser.parse_args()
    prepare()
    from utils import load_oven_table
    load_oven_table()
    if QUESTION == 4:
        from problem4 import Inputs
        Inputs()
    if args.check:
        print(f'Q{QUESTION}: imports and input checks passed', flush=True)
        return
    from reproduction_export import export_saved
    if args.export_only:
        export_saved(PACKAGE_ROOT, QUESTION)
        return
    if QUESTION == 1:
        import problem1
        problem1.main()
    elif QUESTION == 2:
        import problem2
        problem2.main()
    elif QUESTION == 3:
        # The original delivery gate compares Q3 with independently computed Q2.
        if not (PACKAGE_ROOT / 'results' / 'q2_solution.npz').exists():
            print('Q3: computing Q2 first for the original overlap check', flush=True)
            import problem2
            problem2.main()
            export_saved(PACKAGE_ROOT, 2)
        import q3_closeout
        q3_closeout.main(['--no-xlsx'])
    else:
        import problem4
        import verify_q4_results
        for level, tight in ((2, False), (4, False), (4, True), (8, False), (16, False), (8, True)):
            problem4.run(level, tight)
        verify_q4_results.main()
    export_saved(PACKAGE_ROOT, QUESTION)
    print(f'Q{QUESTION}: full recomputation and Excel export completed', flush=True)


if __name__ == '__main__':
    main()
'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Expected exactly one packaging edit: {old[:65]}')
    return source.replace(old, new, 1)


def adapt(name, source):
    if name == 'utils':
        source = replace_once(source, 'ROOT = Path(__file__).resolve().parents[1]',
                              'ROOT = Path(__file__).resolve().parents[3]')
    if name == 'q3_closeout':
        tree = ast.parse(source)
        # Only replace the old machine-specific Excel adapter and its metadata.
        spans = [(node.lineno - 1, node.end_lineno) for node in tree.body
                 if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('NODE', 'BUILDER') for t in node.targets)]
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'export_workbook')
        lines = source.splitlines(keepends=True)
        replacements = [(start, end, '') for start, end in spans]
        replacements.append((function.lineno - 1, function.end_lineno,
            "def export_workbook(path, C_out, times, validation):\n"
            "    require_q3_delivery(validation, DIAG / 'pre_export.json')\n"
            "    from reproduction_export import write_template\n"
            "    write_template(ROOT, 3, times, [C_out])\n"))
        for start, end, text in sorted(replacements, reverse=True):
            lines[start:end] = [text]
        source = ''.join(lines)
        source = replace_once(source, "hashlib.sha256((ROOT/p).read_bytes()).hexdigest()",
            "hashlib.sha256(((Path(__file__).parent / Path(p).name) if p.startswith('code/') else ROOT / p).read_bytes()).hexdigest()")
        source = replace_once(source, "            'tmp/q3_export/build.mjs','tmp/q3_export/gate.mjs',\n",
            "            'code/reproduction_export.py',\n")
    ast.parse(source)
    return source


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {'scope': 'Four primary answer workbooks; original numerical methods retained',
                'changes': ['Relative runtime paths', 'Python Excel export', 'Automatic execution of original prerequisite and verification steps'],
                'questions': {}}
    for question, names in MODULES.items():
        chunks = [HEADER.format(question=question)]
        records = []
        for name in names:
            original = (ROOT / 'code' / (name + '.py')).read_text(encoding='utf-8-sig')
            source = adapt(name, original)
            if "'''" in source:
                raise ValueError(f'Raw source delimiter collision: {name}')
            chunks.append(f"\n# {'=' * 72}\n# Module: {name}.py\n# {'=' * 72}\nSOURCES[{name!r}] = r'''{source}'''\n")
            records.append({'source': f'code/{name}.py', 'original_text_sha256': hashlib.sha256(original.encode()).hexdigest(),
                            'packaged_text_sha256': hashlib.sha256(source.encode()).hexdigest(), 'adapted': source != original})
        text = ''.join(chunks) + FOOTER
        ast.parse(text)
        (DEST / f'Q{question}.py').write_text(text, encoding='utf-8')
        manifest['questions'][str(question)] = records
    for name in ('附件1.xlsx', '附件2.xlsx'):
        dest = DEST / 'data' / '附件' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'data' / '附件' / name, dest)
    for question in range(1, 5):
        for source, relative in [(ROOT / 'data' / '附件' / '附件3' / f'result{question}.xlsx', f'data/附件/附件3/result{question}.xlsx'),
                                 (ROOT / 'results' / f'result{question}.xlsx', f'reference_results/result{question}.xlsx')]:
            dest = DEST / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    (DEST / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copy2(ROOT / 'code' / 'verify_reproduction_results.py', DEST / 'verify_results.py')
    print('Built paper/guosai2026/支撑材料_按问复现')


if __name__ == '__main__':
    main()
