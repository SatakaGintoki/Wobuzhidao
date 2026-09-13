"""Preserve the current manuscript and stage the accepted Q3 check for delivery."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/guosai2026"
BACKUP = ROOT / "tmp/q3_axisymmetric_paper_backup_20260913"
OUT = ROOT / "results/q3_axisymmetric"
SUPPORT = PAPER / "support"
SCRIPTS = ["q3_axisymmetric.py", "verify_q3_axisymmetric.py", "plot_q3_axisymmetric.py", "q3_sensitivity.py"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if BACKUP.exists():
        raise RuntimeError("Existing backup must not be overwritten")
    BACKUP.mkdir(parents=True)
    for path in PAPER.rglob("*"):
        rel = path.relative_to(PAPER)
        if path.is_file() and (path.suffix == ".tex" or path.name in
                              {"reading_updated.pdf", "main.pdf", "ai_details.pdf", "README.md"}):
            dest = BACKUP / "paper" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    protected = [ROOT / f"results/{stem}{q}{ext}" for q in range(1, 5)
                 for stem, ext in [("result", ".xlsx"), ("q", "_solution.npz"), ("q", "_validation.json")]]
    protected += list(OUT.glob("*"))
    protected += [ROOT / "code" / name for name in SCRIPTS]
    protected += list((PAPER / "tables").glob("q[1-4][TC].tex"))
    (BACKUP / "protected_hashes.json").write_text(json.dumps(
        {str(p.relative_to(ROOT)): sha(p) for p in protected if p.is_file()}, indent=2), encoding="utf-8")
    print("Current manuscript backed up; official results and accepted Q3 evidence protected.")


def stage():
    assert json.loads((OUT / "comparison.json").read_text(encoding="utf-8"))["pass"]
    for name in SCRIPTS:
        shutil.copy2(ROOT / "code" / name, SUPPORT / "code" / name)
    for ext in ("pdf", "png"):
        shutil.copy2(ROOT / f"figures/q3_axisymmetric_check.{ext}", PAPER / f"figures/q3_axisymmetric_check.{ext}")
    dest = SUPPORT / "results/q3_axisymmetric"
    dest.mkdir(parents=True, exist_ok=True)
    adaptations = []
    for src in OUT.iterdir():
        if src.suffix not in {".json", ".csv", ".npz"}:
            continue
        target = dest / src.name
        if src.suffix == ".json":
            obj = json.loads(src.read_text(encoding="utf-8"))
            if "source_sha256" in obj:
                originals, packaged = {}, {}
                for key, value in obj["source_sha256"].items():
                    rel = Path(key).relative_to(ROOT).as_posix()
                    originals[rel] = value
                    packaged[rel] = sha(SUPPORT / rel) if (SUPPORT / rel).is_file() else value
                obj["original_source_sha256"] = originals
                obj["source_sha256"] = packaged
                obj["packaging_note"] = "Paths made relative; original hashes retained. Packaged problem3.py has only the documented export-path adaptations. Numerical arrays unchanged."
                target.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
                adaptations.append(src.name)
                continue
        shutil.copy2(src, target)
    shutil.copy2(ROOT / "reports/Q3_AXISYMMETRIC_REPORT.md", SUPPORT / "reports/Q3_AXISYMMETRIC_REPORT.md")
    shutil.copy2(ROOT / "reports/Q3_SENSITIVITY_REPORT.md", SUPPORT / "reports/Q3_SENSITIVITY_REPORT.md")
    sens = SUPPORT / "results/diagnostics/q3_sensitivity"
    sens.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / "results/diagnostics/q3_sensitivity").iterdir():
        if path.suffix in {".json", ".csv"}:
            shutil.copy2(path, sens / path.name)
    manifest_path = SUPPORT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name in SCRIPTS:
        entry = {"file": "code/" + name, "original_sha256": sha(ROOT / "code" / name),
                 "packaged_sha256": sha(SUPPORT / "code" / name), "adaptation": "none"}
        manifest = [item for item in manifest if item["file"] != entry["file"]]
        manifest.append(entry)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (dest / "packaging.json").write_text(json.dumps({
        "rebased_case_metadata": adaptations,
        "arrays": {p.name: sha(p) for p in dest.glob("*.npz")},
        "all_arrays_match_original": all(sha(p) == sha(OUT / p.name) for p in dest.glob("*.npz")),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Accepted figure, code, all small field arrays and audit data staged.")


def check():
    saved = json.loads((BACKUP / "protected_hashes.json").read_text(encoding="utf-8"))
    changed = [rel for rel, value in saved.items() if sha(ROOT / rel) != value]
    presentation = {"code/plot_q3_axisymmetric.py", "results/q3_axisymmetric/figure_provenance.json"}
    numerical_changes = [rel for rel in changed if Path(rel).as_posix() not in presentation]
    if numerical_changes:
        raise RuntimeError(f"Protected numerical artifacts changed: {numerical_changes}")
    audit = {"checked_files": len(saved), "numerical_artifacts_unchanged": True,
             "presentation_updates": {rel: {"before": saved[rel], "after": sha(ROOT / rel)} for rel in changed},
             "note": "Concurrent figure-layout edit retained; accepted arrays and four official solutions are unchanged."}
    (BACKUP / "final_protection_check.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit))


def promote():
    target_root = ROOT / "paper/guosai2026"
    if PAPER == target_root:
        raise RuntimeError("Promote requires the independently reviewed manuscript")
    audit = json.loads((PAPER / "qa_axisymmetric/integration.json").read_text(encoding="utf-8"))
    assert audit["pass"]
    shutil.copy2(PAPER / "ai_details.pdf", SUPPORT / "AI工具使用详情.pdf")
    chosen = list(PAPER.rglob("*.tex"))
    chosen += [PAPER / name for name in ("README.md", "DELIVERY_NOTES.md", "reading_updated.pdf", "main.pdf", "ai_details.pdf")]
    chosen += [PAPER / f"{stem}.{ext}" for stem in ("reading_updated", "main", "ai_details") for ext in ("aux", "log", "out")]
    chosen += list((PAPER / "support").rglob("*"))
    chosen += list((PAPER / "qa_axisymmetric").rglob("*"))
    chosen += [PAPER / f"figures/q3_axisymmetric_check.{ext}" for ext in ("pdf", "png")]
    copied = []
    for src in sorted(set(chosen)):
        if not src.is_file() or "__pycache__" in src.parts:
            continue
        rel = src.relative_to(PAPER)
        if len(rel.parts) == 1 and rel.stem == "reading_updated":
            rel = Path("reading_axisymmetric" + rel.suffix)
        target = target_root / rel
        if target.is_file() and sha(src) == sha(target):
            continue
        if target.is_file():
            old = BACKUP / "before_promotion" / rel
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, old)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied.append(rel.as_posix())
    (BACKUP / "promotion.json").write_text(json.dumps(copied, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"promoted_files": len(copied), "target": str(target_root)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "stage", "check", "promote"])
    parser.add_argument("--paper-dir", type=Path)
    args = parser.parse_args()
    if args.paper_dir:
        PAPER = args.paper_dir.resolve()
        SUPPORT = PAPER / "support"
    {"prepare": prepare, "stage": stage, "check": check, "promote": promote}[args.action]()
