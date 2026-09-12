"""Fail-closed numerical delivery checks shared by Q1 and Q2."""
import json
from pathlib import Path


def make_gate(checks):
    checks = {name: bool(value) for name, value in checks.items()}
    return {"checks": checks, "failed_checks": [k for k, v in checks.items() if not v],
            "meets_delivery_gate": bool(checks) and all(checks.values())}


def require_delivery(validation, diagnostic_path):
    """Persist diagnostics first; never reach any production writer on failure."""
    path = Path(diagnostic_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validation, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    gate = validation["delivery_gate"]
    checks = gate.get("checks", {})
    if not checks or not all(value is True for value in checks.values()) or gate.get("meets_delivery_gate") is not True:
        raise RuntimeError("Delivery blocked; see " + str(path) + ": " + str(gate.get("failed_checks", [])))
