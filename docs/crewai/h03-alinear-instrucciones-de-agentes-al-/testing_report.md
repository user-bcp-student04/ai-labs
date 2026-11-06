# testing_report.md

**Issue:** [H03] Alinear instrucciones de agentes al alcance web-only
**Rol:** Ingeniero de pruebas
**Estado global:** **NO EJECUTADO.** No dispongo de salida real de ningún comando. Este informe no afirma resultados ni cobertura. Una persona debe ejecutar los comandos y adjuntar la salida literal (sección 8).

---

## 1. Naturaleza del cambio y consecuencias para las pruebas

- H03 cambia **texto de instrucciones de agentes**. No añade endpoints, no toca FastAPI, el frontend, la persistencia ni las dependencias (`user_story.md`, `backend_spec.md`, `frontend_spec.md`).
- Por eso no existe contrato HTTP nuevo, persistencia nueva ni subida de archivos. No hay casos de upload que probar, y no invento rutas ni esquemas del contrato W2, cuyo contenido no está en el contexto (P2).
- Las pruebas verifican tres cosas:
  1. El contenido de las instrucciones (CA1).
  2. La preservación de identificadores, extracción/publicación y orden del pipeline (CA3).
  3. Que el API existente sigue arrancando (humo con `TestClient`) y que `tools/verify.py` y las pruebas existentes pasan (CA2).
- **Aislamiento (`tmp_path` / `monkeypatch`):** no hay directorio de subidas que aislar.
  - `tmp_path` se usa para fabricar agentes sintéticos y repositorios git temporales.
  - `monkeypatch` se usa para `chdir` y variables de entorno, de modo que ninguna prueba escriba en el repositorio real.
  - La prueba de humo del API ejecuta con `monkeypatch.chdir(tmp_path)`, de modo que cualquier ruta relativa que `config.py` cree al importar quede en un directorio temporal.

### Conflicto de instrucciones declarado

El encargo genérico menciona `python tools/lab.py test api`. La tarea 2.4 del Issue prohíbe inventar `tools/lab.py` y `ng test`. **Prevalece el Issue**, así que no uso `tools/lab.py`. Los comandos son `python -m pytest ...` y `python tools/verify.py`. No uso JUnit ni Quarkus.

---

## 2. Supuestos (cada prueba depende solo de lo declarado aquí)

| ID | Supuesto | Si es falso |
|---|---|---|
| T1 | Las pruebas viven en `api/tests/` (según `backend_spec.md`) y se ejecutan desde la raíz del repositorio. | Ajustar `REPO_ROOT` en `h03_support.py` (una línea). |
| T2 | Un módulo de agente es un `.py` que define a nivel superior `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent` y `build_task` (P1: ruta desconocida). Se descubre por AST, sin fijar ruta. Se excluyen `.git`, `node_modules`, `venv`, `web`, `frontend-angular` y `tests`. | La prueba `test_agents_discovered_with_five_roles` falla con mensaje claro. |
| T3 | El rol se deduce de `SPEC_FILE`: `user_story.md` → arquitectura, `backend_spec.md` → backend, `frontend_spec.md` → frontend, `testing_report.md` → pruebas. Seguridad se deduce por `segur`, `secur` o `chapter` en `KEY`, `LABEL` o nombre de archivo. | Falla de forma explícita (no hay skip). Se corrige el mapeo en `h03_support.py`. |
| T4 | El texto de las instrucciones está en **literales de cadena** del módulo del agente. | Si las instrucciones se cargan desde otros archivos, las pruebas de contenido fallan y hay que ampliar `instruction_text`. |
| T5 | La rama base es `main` (`BASE_REF`), accesible localmente. Las comprobaciones de alcance comparan el árbol de trabajo con `git merge-base HEAD main`. | Cambiar `BASE_REF`. No hay variable opcional que pueda dejar la prueba sin ejecutar. |
| T6 | "Texto de instrucciones" = cadenas de ≥60 caracteres o con salto de línea. Al comparar contra la base se neutralizan solo esas cadenas. Las cadenas cortas (claves, etiquetas, rutas, listas de orden) se comparan literalmente. | Un cambio legítimo en una cadena corta de instrucciones se marcaría como violación y se resolvería por revisión manual. |
| T7 | `api/app/main.py` expone `app` y mantiene habilitado `/openapi.json` (nombres de `backend_spec.md`). `fastapi`, `httpx` y `pytest` ya están instalados. No se modifica ningún `requirements*.txt`. | La prueba de humo falla. Se declara el hallazgo, no se oculta. |
| T8 | Las frases de las tareas 2.1–2.5 («Sin cambios en backend», «página Angular», «Angular 17», `environment.ts`, etc.) deben aparecer, sin tildes ni mayúsculas. Los comandos prohibidos (`tools/lab.py`, `ng test`) y los temas excluidos (autenticación, QR, FastAPI) solo se admiten en frases con negación. | Una paráfrasis se marca como fallo y se decide en revisión (corregir la instrucción o ampliar el patrón). |
| T9 | P3 sigue pendiente. `python -m pytest api/tests` es el comando propuesto para las pruebas existentes y no está confirmado. | Sustituir por el comando real una vez confirmado. |

---

## 3. Trazabilidad: criterio → prueba → resultado esperado → estado

| Criterio / tarea | Prueba (archivo::función) | Resultado esperado | Estado |
|---|---|---|---|
| **CA1 / 2.1** Arquitectura cita los dos contratos fuente y propone página Angular, sin API propia | `test_h03_agent_instructions.py::test_arquitectura_2_1_contratos_y_pagina_angular`, `::test_arquitectura_2_1_sin_api_propia` | Aparecen `bcp-wallet-mock-openapi.yaml`, `detalle H3.txt` y «página Angular». «API propia» solo aparece negada. | NO EJECUTADO |
| **CA1 / 2.2** Backend entrega «Sin cambios en backend» y solo contrato W2 | `::test_backend_2_2_sin_cambios_y_contrato_w2` | Aparecen «sin cambios en backend» y `W2`. | NO EJECUTADO |
| **CA1 / 2.3** Frontend: Angular 17 standalone, servicios tipados, `environment.ts`, estados, accesibilidad, idempotencia, `frontend-angular/` → `web/` | `::test_frontend_2_3_requisitos` | Todos los patrones presentes. | NO EJECUTADO |
| **CA1 / 2.4** Pruebas: navegador/mock, sin comandos inventados | `::test_pruebas_2_4_navegador_mock`, `::test_pruebas_2_4_sin_comandos_inventados` | Aparecen «navegador» y «mock». `tools/lab.py` y `ng test` solo aparecen en frases con negación. | NO EJECUTADO |
| **CA1 / 2.5** Seguridad y Chapter: datos ficticios, errores, `/control/*`, CORS, H03 adaptados; sin autenticación, FastAPI ni QR exigidos | `::test_seguridad_2_5_temas_requeridos`, `::test_seguridad_2_5_sin_temas_fuera_de_alcance` | Todos los temas presentes. Autenticación, FastAPI y QR solo con negación. | NO EJECUTADO |
| **CA2 / 2.6** Pruebas existentes pasan | `python -m pytest api/tests` (T9) | Sin fallos ni `skipped`, código 0. Si falla, se pega la salida real. | NO EJECUTADO |
| **CA2 / 2.6** `python tools/verify.py` pasa | Comando `python tools/verify.py; echo $?` | Código 0. Si falla, se documenta con la salida completa. | NO EJECUTADO |
| **CA3** Identificadores presentes y estables | `test_h03_agent_structure.py::test_identifiers_present`, `::test_build_task_takes_feature`; `test_h03_scope_guard.py::test_changed_python_keeps_identifiers_and_structure` | Los seis nombres siguen definidos. `build_task` recibe `feature` primero. Los valores de `KEY`, `LABEL`, `SPEC_FILE` y `EXTRACT_CODE` coinciden con la base. | NO EJECUTADO |
| **CA3** Extracción/publicación `frontend-angular/` → `web/` intacta | `test_h03_scope_guard.py::test_no_out_of_scope_paths_changed`, `::test_changed_python_keeps_identifiers_and_structure` | Sin cambios en `frontend-angular/`, `web/` ni `EXTRACT_CODE`. | NO EJECUTADO |
| **CA3** Orden del pipeline intacto | `::test_changed_python_keeps_identifiers_and_structure`, `::test_no_new_python_modules_outside_tests` | Los `.py` cambiados son idénticos a la base salvo texto largo. No hay módulos `.py` nuevos fuera de tests. | NO EJECUTADO |
| **Alcance** Sin cambios en backend, contratos fuente, dependencias ni `tools/verify.py` | `::test_no_out_of_scope_paths_changed` | Lista vacía de rutas fuera de alcance. | NO EJECUTADO |
| **Regla** No cambiar pruebas existentes | `::test_existing_tests_not_modified_or_deleted` | Ningún archivo de test existente aparece como modificado o eliminado. | NO EJECUTADO |
| **Contrato API existente** (humo) | `test_h03_api_contract_smoke.py::test_app_imports_and_exposes_openapi`, `::test_unknown_route_returns_404` | `/openapi.json` responde 200 con `openapi` y `paths`. Una ruta inexistente responde 404. | NO EJECUTADO |
| **Fiabilidad de los detectores** | `test_h03_detectors.py` (varias pruebas) | Los detectores aceptan entradas válidas y rechazan las mutaciones. | NO EJECUTADO |

**Persistencia:** no aplica (A3). No hay SQL, migración ni almacenamiento, y no se afirma ninguna prueba de persistencia.

**Correcciones propuestas por Seguridad:** no recibí entrega de Seguridad en el contexto, solo la tarea 2.5. Cubro los criterios de 2.5 con las dos pruebas de la tabla.
- Los «criterios H03 adaptados» (P6) no se conocen y por eso no se verifican uno a uno.
- Los `/control/*` solo se verifican como mención en el texto. No se prueban rutas del mock, cuyo contenido es desconocido (P2).

**Brecha (P4, P7):** `tools/verify.py` tiene un alcance desconocido. Las pruebas de contenido son textuales y no demuestran que un agente produzca buenos entregables. No hay prueba automática de navegador: Cypress, Playwright y `ng test` no constan como disponibles (P5, 2.4). La cobertura de navegador/mock se verifica solo como presencia de la instrucción, no por ejecución. No afirmo cobertura.

---

## 4. Casos por tipo

| Tipo | Casos |
|---|---|
| **Positivos** | Módulos de agente con los seis nombres. Las instrucciones de cada rol contienen sus frases requeridas. Cambiar solo texto largo no es violación (`test_check_preserved_allows_text_only_change`). El API responde 200 en `/openapi.json`. |
| **Negativos** | Falta `EXTRACT_CODE`. `build_task(task)` en lugar de `feature`. Cambia `KEY`, `EXTRACT_CODE`, el orden del pipeline o el argumento. `ng test` o `tools/lab.py` sin negación. Autenticación o QR exigidos. Ruta fuera de alcance modificada. Test existente modificado. Falta «Sin cambios en backend». |
| **Borde** | Código con error de sintaxis o vacío. Tildes y mayúsculas en las frases. Negación en la línea anterior (listas «Prohibido:» + viñeta). Directorios `tests` y `node_modules` excluidos del descubrimiento. Rutas con espacios (`detalle H3.txt`). Prefijo `frontend-angular-notes.md` que no debe confundirse con `frontend-angular/`. Archivos sin seguimiento (untracked). |
| **Integración** | Repositorio git temporal para `changed_status` y `base_source`. `TestClient` sobre `app.main:app` con directorio de trabajo aislado. Ejecución conjunta con las pruebas existentes y `tools/verify.py`. |

---

## 5. Preparación y datos de prueba

**Datos:** no hay datos de negocio. Se usan cadenas sintéticas dentro de `test_h03_detectors.py` y un repositorio git temporal en `tmp_path`.

**Preparación (la hace una persona, no el pipeline):**

```bash
# 1. Verificar herramientas ya instaladas (no se instala nada nuevo)
python --version
git --version
python -c "import fastapi, httpx, pytest; print('ok')"

# 2. Verificar que existe la rama base (T5)
git rev-parse --verify main

# 3. Carpeta de evidencia FUERA del repositorio
mkdir -p ../h03_evidencia
```

**Archivos nuevos (ninguna prueba existente se modifica):**
- `api/tests/h03_support.py`
- `api/tests/test_h03_detectors.py`
- `api/tests/test_h03_agent_structure.py`
- `api/tests/test_h03_scope_guard.py`
- `api/tests/test_h03_agent_instructions.py`
- `api/tests/test_h03_api_contract_smoke.py`

---

## 6. Código de las pruebas

```python
# api/tests/h03_support.py
"""Utilidades de las pruebas H03 (alinear instrucciones de agentes).

Supuestos T1-T8 declarados en testing_report.md. Este módulo no es una prueba.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # T1: api/tests/h03_support.py
BASE_REF = "main"  # T5
IDENTIFIERS = ("KEY", "LABEL", "SPEC_FILE", "EXTRACT_CODE")
REQUIRED_NAMES = IDENTIFIERS + ("agent", "build_task")
EXCLUDED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "site-packages",
    ".pytest_cache", "dist", "web", "frontend-angular", "tests",
}
TEXT_MIN_LEN = 60  # T6
CONTRACT_FILES = {"bcp-wallet-mock-openapi.yaml", "detalle H3.txt"}

ROLE_BY_SPEC = {  # T3
    "user_story.md": "arquitectura",
    "backend_spec.md": "backend",
    "frontend_spec.md": "frontend",
    "testing_report.md": "pruebas",
}
ROLE_PATTERNS = (
    ("seguridad", r"segur|secur|chapter"),
    ("arquitectura", r"arquitect|architect"),
    ("backend", r"backend"),
    ("frontend", r"frontend"),
    ("pruebas", r"prueba|test|qa"),
)

REQUIRED_PATTERNS = {  # T8, sobre texto normalizado (sin tildes, minúsculas)
    "arquitectura": [
        r"bcp-wallet-mock-openapi\.yaml",
        r"detalle h3\.txt",
        r"pagina angular",
    ],
    "backend": [r"sin cambios en backend", r"\bw2\b"],
    "frontend": [
        r"angular 17",
        r"standalone",
        r"environment\.ts",
        r"tipad",
        r"\bestados?\b",
        r"accesibilidad",
        r"idempoten",
        r"frontend-angular/",
        r"\bweb/",
    ],
    "pruebas": [r"navegador", r"\bmock\b"],
    "seguridad": [r"ficticio", r"/control/", r"\bcors\b", r"\bh03\b", r"\berrores?\b"],
}
FORBIDDEN_UNLESS_NEGATED = {
    "arquitectura": [r"api propi"],
    "pruebas": [r"tools/lab\.py", r"\bng test\b"],
    "seguridad": [r"autenticaci", r"\bqr\b", r"fastapi"],
}
NEGATION = re.compile(
    r"\b(no|nunca|ni|sin|prohib\w*|evit\w*|excluy\w*|inventes?|inventar|fuera de alcance)\b"
)


# ----------------------------------------------------------------- texto / AST
def norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def parse(source: str):
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError):
        return None


def defined_names(tree: ast.AST) -> dict:
    names: dict = {}
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names[target.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names[node.target.id] = node
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names[node.name] = node
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names[alias.asname or alias.name] = node
    return names


def is_agent_module(source: str) -> bool:
    tree = parse(source)
    return tree is not None and set(REQUIRED_NAMES) <= set(defined_names(tree))


def literal_value(source: str, name: str):
    tree = parse(source)
    if tree is None:
        return None
    node = defined_names(tree).get(name)
    if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
        try:
            return ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            return None
    return None


def instruction_text(source: str) -> str:
    tree = parse(source)
    if tree is None:
        return ""
    return "\n".join(
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )


class _TextNormalizer(ast.NodeTransformer):
    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str) and (len(node.value) >= TEXT_MIN_LEN or "\n" in node.value):
            return ast.copy_location(ast.Constant(value="<TEXT>"), node)
        return node


def structural_dump(source: str) -> str:
    tree = _TextNormalizer().visit(ast.parse(source))
    return ast.dump(tree)


def identifier_snapshot(source: str) -> dict:
    tree = parse(source)
    names = defined_names(tree) if tree is not None else {}
    snap: dict = {}
    for name in IDENTIFIERS:
        snap[name] = ast.dump(names[name]) if name in names else None
    snap["agent_defined"] = "agent" in names
    build_task = names.get("build_task")
    if isinstance(build_task, (ast.FunctionDef, ast.AsyncFunctionDef)):
        snap["build_task_args"] = ast.dump(build_task.args)
    else:
        snap["build_task_args"] = None if build_task is None else "no-funcion"
    return snap


# ------------------------------------------------------------------ descubrir
def discover_agent_files(root: Path = REPO_ROOT) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = Path(dirpath) / filename
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if is_agent_module(source):
                found.append(path)
    return sorted(found)


def role_of(source: str, path) -> str | None:
    spec = literal_value(source, "SPEC_FILE")
    if isinstance(spec, str):
        role = ROLE_BY_SPEC.get(Path(spec).name)
        if role:
            return role
    ident = norm(
        " ".join(str(literal_value(source, n) or "") for n in ("KEY", "LABEL"))
        + " " + Path(path).stem
    )
    for role, pattern in ROLE_PATTERNS:
        if re.search(pattern, ident):
            return role
    return None


def agents_by_role(root: Path = REPO_ROOT) -> dict[str, list[tuple[Path, str]]]:
    result: dict[str, list[tuple[Path, str]]] = {}
    for path in discover_agent_files(root):
        source = path.read_text(encoding="utf-8")
        role = role_of(source, path)
        if role:
            result.setdefault(role, []).append((path, source))
    return result


# ----------------------------------------------------------------- validadores
def check_structure(source: str) -> list[str]:
    tree = parse(source)
    if tree is None:
        return ["no es Python válido"]
    names = defined_names(tree)
    violations = [f"falta {n}" for n in REQUIRED_NAMES if n not in names]
    build_task = names.get("build_task")
    if isinstance(build_task, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [a.arg for a in build_task.args.posonlyargs + build_task.args.args]
        if not args or args[0] != "feature":
            violations.append(f"build_task debe recibir 'feature' primero, recibe {args}")
    elif build_task is not None and not isinstance(build_task, ast.ImportFrom):
        violations.append("build_task no es una función")
    return violations


def check_preserved(base_src: str, new_src: str) -> list[str]:
    if parse(base_src) is None:
        return ["la línea base no es Python válido"]
    if parse(new_src) is None:
        return ["la versión nueva no es Python válido"]
    violations: list[str] = []
    snap_base, snap_new = identifier_snapshot(base_src), identifier_snapshot(new_src)
    for key, value in snap_base.items():
        if value != snap_new[key]:
            violations.append(f"cambió {key}")
    if structural_dump(base_src) != structural_dump(new_src):
        violations.append("cambió la estructura (orden, firmas o código) fuera del texto de instrucciones")
    return violations


def check_required(role: str, text: str) -> list[str]:
    normalized = norm(text)
    return [f"falta patrón {p!r}" for p in REQUIRED_PATTERNS[role] if not re.search(p, normalized)]


def unnegated_mentions(text: str, patterns: list[str]) -> list[str]:
    lines = norm(text).splitlines()
    bad: list[str] = []
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line):
                context = line + " " + (lines[i - 1] if i > 0 else "")
                if not NEGATION.search(context):
                    bad.append(f"{pattern!r} sin negación: {line.strip()[:120]}")
    return bad


def check_forbidden(role: str, text: str) -> list[str]:
    return unnegated_mentions(text, FORBIDDEN_UNLESS_NEGATED.get(role, []))


def role_text(role: str, root: Path = REPO_ROOT) -> str:
    entries = agents_by_role(root).get(role, [])
    assert entries, f"no se encontró ningún agente con rol {role!r} (supuestos T2/T3)"
    return "\n".join(instruction_text(src) for _, src in entries)


# ------------------------------------------------------------------------ git
def git(*args: str, cwd: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falló ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def merge_base(cwd: Path = REPO_ROOT, ref: str = BASE_REF) -> str:
    return git("merge-base", "HEAD", ref, cwd=cwd).strip()


def changed_status(base: str, cwd: Path = REPO_ROOT) -> dict[str, str]:
    out = git("diff", "--name-status", "--no-renames", "-z", base, cwd=cwd)
    tokens = [t for t in out.split("\0") if t]
    status = {tokens[i + 1]: tokens[i] for i in range(0, len(tokens) - 1, 2)}
    for path in git("ls-files", "--others", "--exclude-standard", "-z", cwd=cwd).split("\0"):
        if path:
            status[path] = "A"
    return status


def base_source(base: str, path: str, cwd: Path = REPO_ROOT) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{base}:{path}"], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout if result.returncode == 0 else None


def is_out_of_scope(path: str) -> bool:
    p = path.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    return (
        p.startswith(("api/app/", "frontend-angular/", "web/"))
        or (name.startswith("requirements") and name.endswith(".txt"))
        or name in CONTRACT_FILES
        or p == "tools/verify.py"
    )


def is_test_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    name = parts[-1]
    return "tests" in parts[:-1] or name.startswith("test_") or name == "conftest.py"
```

```python
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
```

```python
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
```

```python
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
```

```python
# api/tests/test_h03_agent_instructions.py
"""CA1 / tareas 2.1-2.5: contenido de las instrucciones por rol (T4, T8). Pruebas del cambio."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h03_support as s  # noqa: E402


def test_arquitectura_2_1_contratos_y_pagina_angular():
    assert not (v := s.check_required("arquitectura", s.role_text("arquitectura"))), v


def test_arquitectura_2_1_sin_api_propia():
    assert not (v := s.check_forbidden("arquitectura", s.role_text("arquitectura"))), v


def test_backend_2_2_sin_cambios_y_contrato_w2():
    assert not (v := s.check_required("backend", s.role_text("backend"))), v


def test_frontend_2_3_requisitos():
    assert not (v := s.check_required("frontend", s.role_text("frontend"))), v


def test_pruebas_2_4_navegador_mock():
    assert not (v := s.check_required("pruebas", s.role_text("pruebas"))), v


def test_pruebas_2_4_sin_comandos_inventados():
    assert not (v := s.check_forbidden("pruebas", s.role_text("pruebas"))), v


def test_seguridad_2_5_temas_requeridos():
    assert not (v := s.check_required("seguridad", s.role_text("seguridad"))), v


def test_seguridad_2_5_sin_temas_fuera_de_alcance():
    assert not (v := s.check_forbidden("seguridad", s.role_text("seguridad"))), v
```

```python
# api/tests/test_h03_api_contract_smoke.py
"""Integración: el API FastAPI existente (sin cambios) sigue arrancando. Nombres según backend_spec.md (T7).
No se prueba ningún endpoint propio: el Issue no define ninguno."""
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))


def _client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # rutas relativas de config.py quedan en un directorio temporal
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_app_imports_and_exposes_openapi(tmp_path, monkeypatch):
    response = _client(tmp_path, monkeypatch).get("/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert "openapi" in body
    assert isinstance(body["paths"], dict)


def test_unknown_route_returns_404(tmp_path, monkeypatch):
    response = _client(tmp_path, monkeypatch).get("/ruta-inexistente-h03")
    assert response.status_code == 404  # solo el código; el formato de error no se asume (A1)
```

---

## 7. Orden de ejecución y comandos

### Fase 0. Comprobaciones textuales manuales (complemento, no sustituyen a pytest)

```bash
git diff --stat
git diff -U0
git grep -n "Sin cambios en backend"
git grep -n "bcp-wallet-mock-openapi.yaml"
git grep -n "detalle H3.txt"
git grep -n "Angular 17"
git grep -n "environment.ts"
git grep -nE "^(KEY|LABEL|SPEC_FILE|EXTRACT_CODE)\b"
git diff -U0 | grep -nE "^\+.*(tools/lab\.py|ng test)"   # revisar a mano que solo haya menciones prohibitivas
```

### Fase A. Línea base (versión actual, todas las pruebas incluidas las nuevas)

Los archivos nuevos se copian a un árbol limpio de `main`:

```bash
git worktree add ../h03-baseline main
cp api/tests/h03_support.py api/tests/test_h03_*.py ../h03-baseline/api/tests/
cd ../h03-baseline

# A1. Pruebas existentes + nuevas de estructura, detectores, alcance y humo
python -m pytest api/tests -v -rA --ignore=api/tests/test_h03_agent_instructions.py \
  > ../h03_evidencia/A1_pytest_base.txt 2>&1; echo "exit=$?"

# A2. Pruebas de contenido (CA1) sobre la base, para registrar su estado inicial
python -m pytest api/tests/test_h03_agent_instructions.py -v -rA \
  > ../h03_evidencia/A2_instrucciones_base.txt 2>&1; echo "exit=$?"

# A3. Verificación del repositorio
python tools/verify.py > ../h03_evidencia/A3_verify_base.txt 2>&1; echo "exit=$?"
```

**Regla de la línea base:**
- **Las pruebas de A1 deben pasar.** Si alguna falla, se corrige la prueba (supuesto T1–T8 equivocado) o se descarta. Nunca se atribuye al cambio.
- A2 verifica el comportamiento que H03 entrega. Si todavía no está en la base, su fallo es el estado inicial esperado de CA1. Se registra como tal, no como regresión, y no se corrige la prueba para que pase en la base. Si fallan por un patrón mal formulado en algo que la base ya cumple, se corrige la prueba (T8).
- Un `skipped` cuenta como NO cumplido. Revisar que `-rA` no liste ninguno.

### Fase B. Cambio (rama con las instrucciones actualizadas)

```bash
cd <raíz del repositorio, rama con el cambio>
python -m pytest api/tests -v -rA > ../h03_evidencia/B1_pytest_cambio.txt 2>&1; echo "exit=$?"
python tools/verify.py > ../h03_evidencia/B2_verify_cambio.txt 2>&1; echo "exit=$?"   # PowerShell: $LASTEXITCODE
```

Para depurar solo el cambio, filtrar por archivo: `python -m pytest api/tests/test_h03_agent_instructions.py api/tests/test_h03_scope_guard.py -v -rA`.

**Resultado esperado en B:** 0 fallos, 0 `skipped`, y `verify.py` con código 0. Si algo falla, pegar la salida real sin resumir.

### Limpieza

```bash
cd <raíz del repositorio>
git worktree remove ../h03-baseline --force
git worktree prune
# La carpeta ../h03_evidencia se conserva hasta adjuntar las salidas, luego se puede borrar.
git status --short   # no debe quedar nada inesperado fuera de los 6 archivos de api/tests
```

Las pruebas no escriben fuera de `tmp_path`, así que no requieren limpieza adicional.

---

## 8. Registro de evidencia (a completar por la persona que ejecute)

| Fase | Comando | Código de salida | Resumen pytest (passed/failed/skipped) | Salida adjunta | Estado |
|---|---|---|---|---|---|
| A1 | pytest base (sin pruebas de contenido) | — | — | — | NO EJECUTADO |
| A2 | pytest contenido sobre base | — | — | — | NO EJECUTADO |
| A3 | `python tools/verify.py` base | — | — | — | NO EJECUTADO |
| B1 | pytest cambio (todo) | — | — | — | NO EJECUTADO |
| B2 | `python tools/verify.py` cambio | — | — | — | NO EJECUTADO |
| Fase 0 | `git grep` / `git diff` | — | — | — | NO EJECUTADO |

---

## 9. Pendientes que condicionan estas pruebas

- **P1:** ruta de los módulos de agente. Se descubren por AST (T2), pero hay que confirmar que el descubrimiento encuentra los cinco roles.
- **P2 / P6:** contenido de los contratos W2 y de los criterios H03 adaptados. Sin él, no se verifican rutas `/control/*`, errores, idempotencia ni CORS del mock. Solo se verifica que las instrucciones los mencionen.
- **P3:** comando confirmado de las pruebas existentes.
- **P4:** alcance real de `tools/verify.py` sobre identificadores y orden del pipeline.
- **P5:** comandos de navegador/mock disponibles. Mientras no consten, no se propone ni se inventa ninguno.
- **P7:** aceptar que la verificación textual no prueba la calidad de los entregables que producirán los agentes.