# api/tests/test_h03_health_contract.py
"""H03 · API-01…API-10: contrato de /health, rutas inexistentes y configuración.

Supuesto T-3: `app` es importable (se ejecuta con api/ como directorio de trabajo).
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app

API_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_api_01_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json() == {"status": "ok", "service": config.SERVICE_NAME}


def test_api_02_health_usa_el_nombre_de_servicio_configurado(client, monkeypatch):
    monkeypatch.setattr(config, "SERVICE_NAME", "svc-h03-prueba")
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "svc-h03-prueba"}


def test_api_03_health_ignora_parametros_de_consulta(client):
    resp = client.get("/health", params={"x": "1", "payload": "abc"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": config.SERVICE_NAME}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_api_04_health_rechaza_otros_metodos(client, method):
    resp = getattr(client, method)("/health")
    assert resp.status_code == 405
    assert resp.json() == {"code": "METHOD_NOT_ALLOWED", "message": "Método no permitido."}
    assert "GET" in resp.headers.get("allow", "")


def test_api_05_ruta_inexistente_devuelve_404_con_formato_unico(client):
    resp = client.get("/no-existe")
    assert resp.status_code == 404
    assert resp.json() == {"code": "NOT_FOUND", "message": "Recurso no encontrado."}


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/qrs/resolve"),
        ("post", "/payments"),
        ("get", "/payments/pay_1"),
        ("get", "/payments/pay_1/receipt"),
    ],
)
def test_api_06_los_endpoints_w2_w3_no_viven_en_esta_api(client, method, path):
    """S-1: W2/W3 son servicios externos; FastAPI no los implementa ni los proxifica."""
    resp = getattr(client, method)(path)
    assert resp.status_code == 404
    assert resp.json() == {"code": "NOT_FOUND", "message": "Recurso no encontrado."}


def test_api_07_openapi_expone_solo_health(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert set(resp.json()["paths"]) == {"/health"}


def _read_config(extra_env: dict, drop: tuple) -> list:
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env.update(extra_env)
    env["PYTHONPATH"] = str(API_DIR)
    code = (
        "import json; from app import config; "
        "print(json.dumps([config.SERVICE_NAME, config.API_VERSION, config.LOG_LEVEL]))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_api_08_configuracion_por_defecto():
    values = _read_config({}, drop=("SERVICE_NAME", "API_VERSION", "LOG_LEVEL"))
    assert values == ["merchant-qr-api", "0.1.0", "INFO"]


def test_api_09_configuracion_desde_variables_de_entorno():
    values = _read_config(
        {"SERVICE_NAME": "otro-servicio", "API_VERSION": "9.9.9", "LOG_LEVEL": "debug"},
        drop=(),
    )
    assert values == ["otro-servicio", "9.9.9", "DEBUG"]


def _one_health_call(_: int) -> tuple:
    with TestClient(app) as c:
        resp = c.get("/health")
        return resp.status_code, resp.json()


def test_api_10_health_concurrente_sin_estado_compartido():
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(_one_health_call, range(20)))
    assert len(results) == 20
    assert all(status == 200 for status, _ in results)
    assert all(body == {"status": "ok", "service": config.SERVICE_NAME} for _, body in results)
