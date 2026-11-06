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
