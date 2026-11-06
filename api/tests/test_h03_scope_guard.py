# api/tests/test_h03_scope_guard.py
"""CA3 y alcance: compara el árbol de trabajo con la rama base (T5). Con árbol limpio las comprobaciones
de diff pasan trivialmente; el contenido real de la línea base lo aportan test_h03_agent_structure.py
y las pruebas existentes."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h03_support as s  # noqa: E402


def test_base_ref_resolves():
    assert re.fullmatch(r"[0-9a-f]{40}", s.merge_base())


def test_no_out_of_scope_paths_changed():
    status = s.changed_status(s.merge_base())
    bad = sorted(p for p in status if s.is_out_of_scope(p))
    assert not bad, f"cambios fuera de alcance (backend, frontend, web/, contratos, requirements, verify.py): {bad}"


def test_existing_tests_not_modified_or_deleted():
    status = s.changed_status(s.merge_base())
    bad = sorted(p for p, st in status.items() if s.is_test_path(p) and st != "A")
    assert not bad, f"pruebas existentes modificadas o eliminadas: {bad}"


def test_no_new_python_modules_outside_tests():
    status = s.changed_status(s.merge_base())
    bad = sorted(p for p, st in status.items()
                 if st == "A" and p.endswith(".py") and not s.is_test_path(p))
    assert not bad, f"módulos .py nuevos (no se crean agentes ni pasos): {bad}"


def test_changed_python_keeps_identifiers_and_structure():
    base = s.merge_base()
    status = s.changed_status(base)
    violations: dict[str, list[str]] = {}
    for path, st in status.items():
        if not path.endswith(".py") or s.is_test_path(path):
            continue
        if st == "D":
            violations[path] = ["módulo eliminado"]
        elif st in ("M", "T"):
            old = s.base_source(base, path)
            new = (s.REPO_ROOT / path).read_text(encoding="utf-8")
            found = s.check_preserved(old or "", new)
            if found:
                violations[path] = found
    assert not violations, violations
