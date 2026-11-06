# api/tests/test_h03_agent_structure.py
"""Línea base: la estructura de los agentes (identificadores) existe y es coherente en la versión actual."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h03_support as s  # noqa: E402

ROLES = ("arquitectura", "backend", "frontend", "pruebas", "seguridad")


def test_agents_discovered_with_five_roles():
    files = s.discover_agent_files()
    assert files, "no se encontró ningún módulo de agente (supuesto T2, pendiente P1)"
    agents = s.agents_by_role()
    missing = [r for r in ROLES if r not in agents]
    assert not missing, f"roles sin agente: {missing}; módulos hallados: {[str(f) for f in files]}"


def test_identifiers_present():
    problems = {}
    for path in s.discover_agent_files():
        violations = s.check_structure(path.read_text(encoding="utf-8"))
        if violations:
            problems[str(path)] = violations
    assert not problems, problems


def test_build_task_takes_feature():
    bad = []
    for path in s.discover_agent_files():
        if any("feature" in v for v in s.check_structure(path.read_text(encoding="utf-8"))):
            bad.append(str(path))
    assert not bad, bad


def test_keys_and_spec_files_are_unique():
    keys, specs = [], []
    for path in s.discover_agent_files():
        src = path.read_text(encoding="utf-8")
        for bucket, name in ((keys, "KEY"), (specs, "SPEC_FILE")):
            value = s.literal_value(src, name)
            if value is not None:
                bucket.append(value)
    assert len(keys) == len(set(keys)), f"KEY duplicado: {keys}"
    assert len(specs) == len(set(specs)), f"SPEC_FILE duplicado: {specs}"
