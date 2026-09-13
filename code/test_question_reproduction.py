"""Relocate the package and run all four complete solves from clean inputs."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'paper' / 'guosai2026' / '支撑材料_按问复现'
TEST = ROOT / '_tmp' / 'reproduction_portable'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_question(q):
    start = time.perf_counter()
    with (TEST / f'Q{q}_test.log').open('w', encoding='utf-8') as log:
        process = subprocess.run([sys.executable, '-u', str(TEST / f'Q{q}.py')],
                                 cwd=ROOT.parent, stdout=log, stderr=subprocess.STDOUT, timeout=2400)
    record = {'question': q, 'exit_code': process.returncode, 'seconds': time.perf_counter() - start}
    print(json.dumps(record), flush=True)
    if process.returncode:
        raise RuntimeError(f'Q{q} failed; see relocated test log')
    return record


def chain(questions):
    return [run_question(q) for q in questions]


def main():
    if TEST.exists():
        raise RuntimeError('Test target already exists; do not reuse numerical caches')
    protected = {f'results/result{q}.xlsx': digest(ROOT / 'results' / f'result{q}.xlsx') for q in range(1, 5)}
    shutil.copytree(PACKAGE, TEST)
    # No solver arrays or generated answers may be present at test start.
    assert not (TEST / 'results').exists()
    for q in range(1, 5):
        subprocess.run([sys.executable, str(TEST / f'Q{q}.py'), '--check'], cwd=ROOT.parent, check=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(chain, [1, 4])
        b = pool.submit(chain, [2, 3])
        runs = a.result() + b.result()
    subprocess.run([sys.executable, str(TEST / 'verify_results.py')], cwd=ROOT.parent, check=True)
    comparison = json.loads((TEST / 'reproduction_check.json').read_text(encoding='utf-8'))
    unchanged = all(digest(ROOT / p) == checksum for p, checksum in protected.items())
    if not unchanged:
        raise RuntimeError('Original answer files changed during the test')
    evidence = {'test': 'Clean relocated full numerical recomputation, launched from a different working directory',
                'original_workbooks_unchanged': unchanged, 'runs': sorted(runs, key=lambda r: r['question']),
                'comparison': comparison, 'pass': comparison['pass'] and unchanged}
    (PACKAGE / 'reproduction_verification.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ALL FOUR RELOCATED FULL RUNS PASSED', flush=True)


if __name__ == '__main__':
    main()
