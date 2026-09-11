#!/usr/bin/env python3
"""Read-only, phase-specific environment probe. Never installs dependencies."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('modeling', 'writing', 'verification'), default='modeling')
    parser.add_argument('--engine', choices=('latex', 'typst'))
    parser.add_argument('--require-package', action='append', default=[])
    parser.add_argument('--tool', action='append', default=[], help='NAME=absolute executable path')
    parser.add_argument('--output', type=Path, help='Optional JSON output in the task workspace')
    args = parser.parse_args()
    if args.phase != 'modeling' and not args.engine:
        parser.error('--engine is required for writing/verification')
    required_packages = (['numpy', 'pandas', 'matplotlib'] if args.phase == 'modeling' else []) + args.require_package
    for name in required_packages:
        if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', name):
            parser.error('invalid import name: ' + name)
    names = ['typst', 'xelatex', 'drawio', 'draw.io', 'pdftoppm', 'mutool', 'magick']
    overrides = {}
    for entry in args.tool:
        name, sep, path = entry.partition('=')
        if not sep or not name or not Path(path).is_absolute():
            parser.error('--tool requires NAME=absolute path')
        if name not in names:
            parser.error('unsupported tool name: ' + name)
        overrides[name] = path
    commands = {n: overrides.get(n) or shutil.which(n) for n in names}
    commands = {n: str(Path(p).resolve()) if p and Path(p).is_file() else None for n, p in commands.items()}
    package_results = {}
    for name in dict.fromkeys(required_packages):
        code = 'import importlib,json; m=importlib.import_module(' + repr(name) + '); print(json.dumps({"version":str(getattr(m,"__version__","unknown"))}))'
        try:
            probe = subprocess.run([sys.executable, '-c', code], text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=20)
            data = json.loads(probe.stdout.splitlines()[-1]) if probe.returncode == 0 else {}
            package_results[name] = {'imported': probe.returncode == 0, **data}
            if probe.returncode:
                package_results[name]['error'] = probe.stderr.strip()[-1000:]
        except (subprocess.TimeoutExpired, ValueError, IndexError) as exc:
            package_results[name] = {'imported': False, 'error': str(exc)}
    missing = ['package:' + n for n, r in package_results.items() if not r['imported']]
    if args.engine and not commands['xelatex' if args.engine == 'latex' else 'typst']:
        missing.append('compiler:' + args.engine)
    if args.phase == 'verification' and not any(commands[n] for n in ('pdftoppm', 'mutool', 'magick')):
        missing.append('PDF rasterizer (pdftoppm/mutool/magick or verified equivalent)')
    result = {'phase': args.phase, 'engine': args.engine, 'python': str(Path(sys.executable).resolve()),
              'python_version': sys.version.split()[0], 'packages': package_results, 'commands': commands,
              'missing_required': missing, 'status': 'MISSING' if missing else 'DETECTED',
              'scope': 'Package imports and command paths only; compilation, fonts, rendering and contest readiness untested.'}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + '\n', encoding='utf-8')
    print(payload)
    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
