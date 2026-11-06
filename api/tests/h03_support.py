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
