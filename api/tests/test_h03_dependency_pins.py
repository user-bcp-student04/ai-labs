# api/tests/test_h03_dependency_pins.py
"""H03 · DEP-01, DEP-02: pines exactos de api/requirements.txt y coincidencia con lo instalado.

No consulta PyPI/OSV (requiere red): ver el procedimiento manual obligatorio del informe, §8.5.
"""
from importlib.metadata import version
from pathlib import Path

import pytest

REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements.txt"


def _lines():
    out = []
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def test_dep_01_todas_las_dependencias_estan_fijadas_con_igualdad_exacta():
    lines = _lines()
    assert lines, "requirements.txt no contiene dependencias"
    for line in lines:
        assert "==" in line, f"Dependencia sin pin exacto: {line}"
        assert not any(op in line for op in (">=", "<=", "~=", ">", "<", "*")), line


@pytest.mark.parametrize("line", _lines())
def test_dep_02_la_version_instalada_coincide_con_el_pin(line):
    name, pinned = [part.strip() for part in line.split("==", 1)]
    assert version(name) == pinned
