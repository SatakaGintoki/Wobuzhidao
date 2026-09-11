"""Portable CLI and conservative source scanning for the text gate.

This is not a Typst/TeX interpreter. Computed paths require compiler validation.
"""
import argparse
import os
from pathlib import Path
import re


def configure_paths():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paper', nargs='?')
    keys = ('paper-dir', 'root-dir', 'main', 'sections-dir', 'references',
            'figures-dir', 'results-file', 'problem-analysis', 'all-results')
    env_names = ('PAPER_DIR', 'ROOT_DIR', 'MAIN_FILE', 'SECTIONS_DIR', 'REFERENCES_FILE',
                 'FIGURES_DIR', 'RESULTS_FILE', 'PROBLEM_ANALYSIS_FILE', 'ALL_RESULTS_FILE')
    for key in keys:
        parser.add_argument('--' + key)
    parser.add_argument('--internal-term', action='append', default=[])
    parser.add_argument('--no-internal-check', action='store_true')
    args = parser.parse_args()
    options = {env: getattr(args, key.replace('-', '_')) or os.environ.get(env, '')
               for key, env in zip(keys, env_names)}
    explicit_main = Path(options['MAIN_FILE']).expanduser().resolve() if options['MAIN_FILE'] else None
    paper = options['PAPER_DIR'] or args.paper
    if not paper:
        paper = explicit_main.parent if explicit_main else (Path.cwd() if any(Path(n).is_file() for n in ('main.typ', 'main.tex')) else Path('paper'))
    paper = Path(paper).expanduser().resolve()
    root = Path(options['ROOT_DIR']).expanduser().resolve() if options['ROOT_DIR'] else paper.parent
    main = explicit_main or next((paper / n for n in ('main.typ', 'main.tex') if (paper / n).is_file()), paper / 'main.typ')
    if main.suffix.lower() not in ('.typ', '.tex'):
        parser.error('--main must name a .typ or .tex source')
    defaults = {
        'PAPER_DIR': paper, 'ROOT_DIR': root, 'MAIN_FILE': main,
        'SECTIONS_DIR': paper / 'sections',
        'REFERENCES_FILE': paper / ('references.tex' if main.suffix.lower() == '.tex' else 'references.typ'),
        'FIGURES_DIR': root / 'figures', 'RESULTS_FILE': root / 'reports/RESULTS_REPORT.md',
        'PROBLEM_ANALYSIS_FILE': root / 'reports/ANALYSIS_MODELING_REPORT.md',
        'ALL_RESULTS_FILE': root / 'figures/all_results.json',
    }
    for env, default in defaults.items():
        if env in ('PAPER_DIR', 'ROOT_DIR', 'MAIN_FILE'):
            value = default
        elif options[env]:
            value = Path(options[env]).expanduser().resolve()
        else:
            value = default if default.exists() else ''
        os.environ[env] = str(value)
    if args.no_internal_check:
        os.environ['NO_INTERNAL_CHECK'] = '1'
    terms = os.environ.get('EXTRA_INTERNAL_TERMS_STR', '').splitlines() + args.internal_term
    os.environ['EXTRA_INTERNAL_TERMS_STR'] = '\n'.join(terms)


def blank(text):
    return ''.join('\n' if c == '\n' else ' ' for c in text)


def sanitize_source(text, typst):
    """Mask comments and literal code examples, preserving line positions."""
    if not typst:
        text = re.sub(r'\\begin\{(verbatim\*?|lstlisting|minted)\}.*?\\end\{\1\}',
                      lambda m: blank(m.group()), text, flags=re.S)
        text = re.sub(r'\\verb\*?([^\w\s]).*?\1', lambda m: blank(m.group()), text)
        out = []
        for line in text.splitlines(keepends=True):
            for i, ch in enumerate(line):
                if ch == '%':
                    j = i - 1
                    while j >= 0 and line[j] == '\\':
                        j -= 1
                    if (i - j - 1) % 2 == 0:
                        line = line[:i] + blank(line[i:])
                        break
            out.append(line)
        return ''.join(out)
    out = list(text)
    i = 0
    while i < len(text):
        start = i
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            continue
        if text[i] == '`':
            while i < len(text) and text[i] == '`':
                i += 1
            fence = text[start:i]
            end = text.find(fence, i)
            i = len(text) if end < 0 else end + len(fence)
        elif text.startswith('//', i):
            end = text.find('\n', i)
            i = len(text) if end < 0 else end
        elif text.startswith('/*', i):
            depth = 1
            i += 2
            while i < len(text) and depth:
                if text.startswith('/*', i):
                    depth += 1
                    i += 2
                elif text.startswith('*/', i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
        else:
            i += 1
            continue
        out[start:i] = blank(text[start:i])
    return ''.join(out)


def literal_includes(text, typst):
    refs, uncertain = [], []
    if typst:
        # Ignore apparent directives occurring inside string values.
        searchable = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: blank(m.group()), text)
        pattern = r'#include\b|(?<![\w])include(?=\s*\()'
    else:
        searchable = text
        pattern = r'(?<!\\)\\(?:input|include)\b'
    for token in re.finditer(pattern, searchable):
        rest = text[token.end():]
        if typst:
            arg = re.match(r'\s*(?:\(\s*"([^"\\]*)"\s*\)|"([^"\\]*)")', rest)
            ref = (arg.group(1) if arg.group(1) is not None else arg.group(2)) if arg else None
            # A string prefix of a computed expression is not a literal path.
            if arg and re.match(r'\s*\+', rest[arg.end():]):
                ref = None
        else:
            arg = re.match(r'\s*\{([^{}]*)\}', rest)
            if not arg:
                arg = re.match(r'[ \t]+([^\s{}\\%]+)', rest)
            ref = arg.group(1).strip() if arg else None
            if ref and ('\\' in ref or '#' in ref):
                ref = None
            if ref and not Path(ref).suffix:
                ref += '.tex'
        if ref:
            refs.append(ref)
        else:
            uncertain.append('line ' + str(text.count('\n', 0, token.start()) + 1))
    return refs, uncertain


def resolve_reference(ref, source, paper, root, typst):
    if typst and ref.startswith('/'):
        return (root / ref.lstrip('/')).resolve()
    return ((source.parent if typst else paper) / ref).resolve()
