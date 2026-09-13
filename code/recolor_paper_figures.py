"""Recolor existing vector PDFs without changing paths, text, or axis ranges.

Apply this after the original result-plot generators. Input PDFs must use their
original palettes; the archived input directory makes this operation repeatable.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import numpy as np
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, FloatObject


ROOT = Path(__file__).resolve().parents[1]
BLUE, RED, TEAL = "#4358C5", "#D65244", "#1D91C0"
COUNTS = {"q1_T_profiles": 7, "q1_C_profiles": 7,
          "q2_T_profiles": 6, "q2_C_profiles": 6,
          "q3_C_profiles": 10, "q4_C_profiles": 9}
NAMES = ["q1_oven_input", "q4_R_history", *COUNTS,
         "q3_axisymmetric_check", "q4_fixed_vs_shrink"]
RGB_OPS = {b"rg", b"RG", b"g", b"G"}


def rgb(value):
    return tuple(mpl.colors.to_rgb(value))


def key(value):
    return tuple(round(float(v), 5) for v in value)


def mappings(name):
    if name in COUNTS:
        count = COUNTS[name]
        if "_T_" in name:
            # Omit near-white middle colors that disappear as thin lines.
            stops = [0.04, 0.16, 0.29, 0.70, 0.80, 0.89, 0.97]
            if count == 6:
                stops = [0.04, 0.18, 0.31, 0.72, 0.86, 0.97]
            colors = [mpl.colormaps["coolwarm"](v)[:3] for v in stops]
        else:
            # Early, wetter profiles are dark; later profiles shift to teal.
            colors = [mpl.colormaps["YlGnBu"](v)[:3]
                      for v in np.linspace(0.98, 0.43, count)]
        original = mpl.colormaps["tab10"].colors
        return {key(original[i]): tuple(c) for i, c in enumerate(colors)}
    if name == "q1_oven_input":
        return {key(rgb("#1f77b4")): rgb(RED), key(rgb("#ff7f0e")): rgb(TEAL)}
    if name == "q4_R_history":
        return {key(rgb("#1f77b4")): rgb(BLUE)}
    result = {key(rgb("#B65B3B")): rgb(RED), key(rgb("#247B87")): rgb(BLUE)}
    if name == "q3_axisymmetric_check":
        for v in np.linspace(0, 1, 256):
            result[key(mpl.colormaps["viridis"](v)[:3])] = tuple(mpl.colormaps["YlGnBu"](v)[:3])
    return result


def streams(reader):
    """Include shared Form XObjects, such as vector markers and math glyphs."""
    seen = set()
    def visit_resources(resources, prefix):
        for name, ref in resources.get("/XObject", {}).items():
            obj = ref.get_object()
            ident = getattr(ref, "idnum", id(obj))
            if ident in seen or obj.get("/Subtype") != "/Form":
                continue
            seen.add(ident)
            yield prefix + str(name), obj
            yield from visit_resources(obj.get("/Resources", {}), prefix + str(name))
    for i, page in enumerate(reader.pages):
        yield f"page{i}", page
        yield from visit_resources(page.get("/Resources", {}), f"page{i}")


def get_stream(obj, reader):
    data = obj.get_contents() if obj.get("/Type") == "/Page" else obj
    return ContentStream(data, reader)


def canonical(value):
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, (list, tuple)):
        return tuple(canonical(v) for v in value)
    return str(value)


def geometry(reader):
    return {label: [(canonical(args), op) for args, op in get_stream(obj, reader).operations
                    if op not in RGB_OPS]
            for label, obj in streams(reader)}


def compare_geometry(before, after):
    maximum = 0.0
    def compare(a, b):
        nonlocal maximum
        if isinstance(a, float):
            assert isinstance(b, float)
            maximum = max(maximum, abs(a - b))
            assert abs(a - b) <= 1e-6
        elif isinstance(a, (tuple, list)):
            assert len(a) == len(b)
            for x, y in zip(a, b):
                compare(x, y)
        else:
            assert a == b
    assert before.keys() == after.keys()
    for label in before:
        compare(before[label], after[label])
    return maximum


def recolor(source, destination, name):
    reader = PdfReader(source)
    assert len(reader.pages) == 1
    before = geometry(reader)
    writer = PdfWriter(clone_from=reader)
    palette = mappings(name)
    changed, unmapped = Counter(), set()
    for _, obj in streams(writer):
        content = get_stream(obj, writer)
        for index, (args, op) in enumerate(content.operations):
            if op not in RGB_OPS:
                continue
            old = key(args * 3 if op in {b"g", b"G"} else args)
            if old in palette:
                new_op = {b"g": b"rg", b"G": b"RG"}.get(op, op)
                content.operations[index] = ([FloatObject(v) for v in palette[old]], new_op)
                changed[str(old)] += 1
            elif max(old) - min(old) > 0.001:
                unmapped.add(old)
        if obj.get("/Type") == "/Page":
            obj.replace_contents(content)
        else:
            obj.set_data(content.get_data())
    assert not unmapped, (name, "Unmapped colors", unmapped)
    assert changed, (name, "No colors changed")
    writer.write(destination)
    actual = PdfReader(destination)
    numeric_drift = compare_geometry(before, geometry(actual))
    assert reader.pages[0].extract_text() == actual.pages[0].extract_text()
    assert np.allclose(list(reader.pages[0].mediabox), list(actual.pages[0].mediabox), rtol=0, atol=1e-6)
    return {"source": str(source.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "color_operations_changed": sum(changed.values()),
            "geometry_and_text_unchanged": True,
            "max_pdf_serialization_numeric_drift": numeric_drift,
            "color_mapping": {str(k): mpl.colors.to_hex(v) for k, v in palette.items()
                              if str(k) in changed}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source_dir, output_dir = args.source_dir.resolve(), args.output_dir.resolve()
    assert source_dir != output_dir, "Keep original inputs for reproducibility"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"palette": "coolwarm + YlGnBu", "figures": {}}
    for name in NAMES:
        report["figures"][name] = recolor(source_dir / f"{name}.pdf", output_dir / f"{name}.pdf", name)
        print(name, report["figures"][name]["color_operations_changed"], "color operations; geometry unchanged")
    (output_dir / "recolor_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
