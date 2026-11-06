# api/tests/test_h03_detectors.py
"""Fiabilidad de los detectores H03: positivos, negativos y de borde (sin tocar el repositorio real)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h03_support as s  # noqa: E402

LONG_A = "Instrucciones originales del agente de backend, sin cambios en el alcance W2. "
LONG_B = "Instrucciones nuevas del agente de backend: Sin cambios en backend y solo contrato W2. "


def make_src(text=LONG_A, key="backend", extract="re:extraer", order=("a", "b", "c"), arg="feature"):
    return (
        f'KEY = "{key}"\nLABEL = "Backend"\nSPEC_FILE = "backend_spec.md"\n'
        f'EXTRACT_CODE = "{extract}"\nPIPELINE = {list(order)!r}\nagent = object()\n\n'
        f'def build_task({arg}):\n    return """{text}"""\n'
    )


def test_is_agent_module_positive_negative_and_border():
    assert s.is_agent_module(make_src())
    assert not s.is_agent_module(make_src().replace("EXTRACT_CODE", "OTRO"))
    assert not s.is_agent_module("def (")  # sintaxis inválida
    assert not s.is_agent_module("")


def test_check_structure_positive_and_negative():
    assert s.check_structure(make_src()) == []
    assert any("feature" in v for v in s.check_structure(make_src(arg="task")))
    assert any("EXTRACT_CODE" in v for v in s.check_structure(make_src().replace("EXTRACT_CODE", "X")))
    assert s.check_structure("def (") == ["no es Python válido"]


def test_check_preserved_allows_text_only_change():
    assert s.check_preserved(make_src(LONG_A), make_src(LONG_B)) == []


def test_check_preserved_detects_identifier_extraction_order_and_signature_changes():
    base = make_src()
    assert any("KEY" in v for v in s.check_preserved(base, make_src(key="otro")))
    assert any("EXTRACT_CODE" in v for v in s.check_preserved(base, make_src(extract="re:distinto")))
    assert s.check_preserved(base, make_src(order=("b", "a", "c")))  # orden del pipeline
    assert s.check_preserved(base, make_src(arg="task"))


def test_unnegated_mentions_cases():
    pats = [r"\bng test\b", r"tools/lab\.py"]
    assert s.unnegated_mentions("No uses `ng test` ni `tools/lab.py`.", pats) == []
    assert s.unnegated_mentions("Comandos prohibidos:\n- ng test\n- tools/lab.py", pats) == []
    assert len(s.unnegated_mentions("Ejecuta `ng test` para validar", pats)) == 1
    assert len(s.unnegated_mentions("Corre python tools/lab.py test api", pats)) == 1


def test_check_required_is_accent_and_case_insensitive():
    text = "Proponer PÁGINA Angular. Usar bcp-wallet-mock-openapi.yaml y detalle H3.txt como contratos."
    assert s.check_required("arquitectura", text) == []


def test_check_required_negative_and_forbidden():
    assert s.check_required("backend", "Documenta endpoints propios.")
    assert s.check_forbidden("seguridad", "Exigir autenticación obligatoria")
    assert s.check_forbidden("seguridad", "No exigir autenticación ni QR; sin cambios FastAPI") == []
    assert s.check_forbidden("arquitectura", "Diseña una API propia")
    assert s.check_forbidden("arquitectura", "Proponer página Angular, no API propia") == []


def test_role_of_by_spec_and_keyword():
    assert s.role_of(make_src(), "x.py") == "backend"
    other = make_src().replace("backend_spec.md", "x.md").replace('KEY = "backend"', 'KEY = "seguridad"')
    other = other.replace('LABEL = "Backend"', 'LABEL = "Seguridad y Chapter"')
    assert s.role_of(other, "x.py") == "seguridad"
    unknown = make_src().replace("backend_spec.md", "x.md").replace('KEY = "backend"', 'KEY = "zzz"')
    unknown = unknown.replace('LABEL = "Backend"', 'LABEL = "zzz"')
    assert s.role_of(unknown, "zzz.py") is None


def test_discover_excludes_tests_and_node_modules(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # el resultado no depende del cwd
    for rel in ("tools/a.py", "tests/b.py", "node_modules/c.py"):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(make_src(), encoding="utf-8")
    assert s.discover_agent_files(tmp_path) == [tmp_path / "tools" / "a.py"]


def test_is_out_of_scope_borders():
    for path in ("api/app/main.py", "api/requirements.txt", "requirements-dev.txt", "web/index.html",
                 "frontend-angular/src/main.ts", "tools/verify.py", "detalle H3.txt",
                 "docs/bcp-wallet-mock-openapi.yaml"):
        assert s.is_out_of_scope(path), path
    for path in ("api/tests/test_x.py", "docs/readme.md", "frontend-angular-notes.md", "tools/agents.py"):
        assert not s.is_out_of_scope(path), path


def test_git_helpers_in_temporary_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def g(*args):
        return s.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                     "-c", "commit.gpgsign=false", *args, cwd=tmp_path)

    g("init")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    g("add", ".")
    g("commit", "-m", "base")
    base = g("rev-parse", "HEAD").strip()
    (tmp_path / "a.py").write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "detalle H3.txt").write_text("c", encoding="utf-8")  # ruta con espacio, sin seguimiento
    assert s.changed_status(base, cwd=tmp_path) == {"a.py": "M", "detalle H3.txt": "A"}
    assert s.base_source(base, "a.py", cwd=tmp_path).strip() == "x = 1"
    assert s.base_source(base, "nuevo.py", cwd=tmp_path) is None
