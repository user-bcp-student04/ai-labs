# api/tests/test_h03_no_server_persistence.py
"""H03 · PER-01, PER-02: la API no escribe en disco ni acepta subidas (S-1, backend §6-7).

Aísla el directorio de trabajo y las variables de subida con tmp_path y monkeypatch.
Supuesto: la app no usa UPLOAD_DIR; se fija para detectar cualquier escritura inesperada.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def aislado(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    workdir = tmp_path / "cwd"
    uploads.mkdir()
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    for var in ("UPLOAD_DIR", "UPLOADS_DIR", "DATA_DIR"):
        monkeypatch.setenv(var, str(uploads))
    return tmp_path


def _snapshot(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def test_per_01_las_peticiones_no_escriben_en_disco(aislado):
    before = _snapshot(aislado)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/no-existe").status_code == 404
        files = {"file": ("qr.png", b"\x89PNG" + b"0" * 1024, "image/png")}
        assert client.post("/health", files=files).status_code == 405
        assert client.post("/payments", json={"qrId": "qr_1", "amount": 10, "currency": "COP"}).status_code == 404
        assert client.post("/qrs/resolve", content=b"x" * (1024 * 1024)).status_code == 404
    assert _snapshot(aislado) == before
    assert list((aislado / "uploads").iterdir()) == []
    assert list((aislado / "cwd").iterdir()) == []


def test_per_02_openapi_no_declara_cuerpos_ni_subidas():
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    for path, operations in paths.items():
        for method, operation in operations.items():
            assert "requestBody" not in operation, f"{method.upper()} {path} acepta cuerpo"
