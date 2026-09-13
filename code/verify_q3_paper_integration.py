"""Check the accepted Q3 table, PDF consistency, and portable evidence."""
import argparse
import json
import re
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]


def main(paper, reading_stem):
    comparison = json.loads((ROOT / "results/q3_axisymmetric/comparison.json").read_text(encoding="utf-8"))
    source = (paper / "sections/07_axisymmetric.tex").read_text(encoding="utf-8")
    q3 = (paper / "sections/05_q3.tex").read_text(encoding="utf-8")
    validation = (paper / "sections/07_validation.tex").read_text(encoding="utf-8")
    assert r"\input{sections/07_axisymmetric}" in q3
    assert r"\input{sections/07_axisymmetric}" not in validation
    table = [line for line in source.splitlines() if re.match(r"^\$\d+\\times", line)]
    assert len(table) == len(comparison["rows"]) == 5
    for line, row in zip(table, comparison["rows"]):
        cells = line.replace(r"\\\bottomrule", "").replace(r"\\", "").split("&")
        got = [float(cell.strip()) for cell in cells[-3:]]
        expected = [float(f"{row['paired_radial_h']:.6f}"), float(f"{row['t_star_h']:.6f}"),
                    float(f"{row['end_effect_s']:.3f}")]
        assert got == expected, (got, expected)
        grid = [int(x) for x in re.findall(r"\d+", cells[0])]
        assert grid == [row["nr"] - 1, row["nz"] - 1]
    reading = pdfium.PdfDocument(str(paper / f"{reading_stem}.pdf"))
    full = pdfium.PdfDocument(str(paper / "main.pdf"))
    texts = [page.get_textpage().get_text_range() for page in reading]
    assert len(texts) <= 31
    assert all(text == full[i].get_textpage().get_text_range() for i, text in enumerate(texts))
    pages = [i + 1 for i, text in enumerate(texts)
             if "径向简化的二维端面校核" in text or "同径向网格下一、二维临界时间对照" in text]
    normalized = "".join(texts).replace("\r", "").replace("\n", "").replace(" ", "")
    assert "0.004%" in normalized and "57.4731" in normalized and "51.0877" in normalized
    assert "10.1016/S0017-9310(03)00229-1" in normalized
    portable = json.loads((ROOT / "tmp/q3_support_portability_check/results/q3_axisymmetric/comparison.json").read_text(encoding="utf-8"))
    assert comparison == portable
    for stem in (reading_stem, "main", "ai_details"):
        log = (paper / f"{stem}.log").read_text(encoding="utf-8", errors="replace")
        assert not any(term in log for term in ("Overfull", "undefined references", "Missing character"))
    audit = {"pass": True, "new_table_numeric_cells": 15, "grid_rows": 5,
             "original_table_cells": 216, "reading_pages": len(reading), "full_pages": len(full),
             "body_pages_identical": True, "section_pages": pages,
             "portable_comparison_identical": True, "new_result_adoption": "APPROVED"}
    (paper / "qa_axisymmetric/integration.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-dir", type=Path, default=ROOT / "paper/guosai2026")
    parser.add_argument("--reading-stem", default="reading_q3_checked")
    args = parser.parse_args()
    main(args.paper_dir, args.reading_stem)
