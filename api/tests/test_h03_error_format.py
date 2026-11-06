# api/tests/test_h03_error_format.py
"""H03 · ERR-01…ERR-06: formato único de error y no filtración de datos.

Se usa una app local con los handlers reales de app.errors, sin modificar la app principal.
"""
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.errors import register_error_handlers


class _Body(BaseModel):
    amount: int = Field(gt=0)


def _build_app() -> FastAPI:
    local = FastAPI()
    register_error_handlers(local)

    @local.get("/n")
    def n(n: int):
        return {"n": n}

    @local.post("/pay")
    def pay(body: _Body):
        return {"ok": True}

    @local.get("/boom")
    def boom():
        raise RuntimeError("clave-secreta-123")

    @local.get("/http/{status}")
    def http_error(status: int, detail: str):
        raise HTTPException(status_code=status, detail=detail)

    @local.get("/auth")
    def auth():
        raise HTTPException(status_code=401, detail="x", headers={"WWW-Authenticate": "Bearer"})

    return local


@pytest.fixture()
def client():
    return TestClient(_build_app(), raise_server_exceptions=False)


@pytest.mark.parametrize(
    "status,detail,code,message",
    [
        (400, "secreto-400", "INVALID_INPUT", "Entrada inválida."),
        (401, "secreto-401", "UNAUTHORIZED", "Autenticación requerida."),
        (403, "secreto-403", "FORBIDDEN", "No tienes permisos para esta operación."),
        (409, "secreto-409", "CONFLICT", "Conflicto con el estado actual del recurso."),
        (413, "secreto-413", "PAYLOAD_TOO_LARGE", "El contenido enviado supera el tamaño permitido."),
        (418, "soy-tetera", "HTTP_ERROR", "soy-tetera"),
        (503, "password=abc", "INTERNAL_ERROR", "Error interno del servidor."),
    ],
)
def test_err_01_httpexception_usa_formato_unico_y_mensajes_fijos(client, status, detail, code, message):
    resp = client.get(f"/http/{status}", params={"detail": detail})
    assert resp.status_code == status
    assert resp.json() == {"code": code, "message": message}
    assert set(resp.json()) == {"code", "message"}


def test_err_02_se_conservan_las_cabeceras_de_la_excepcion(client):
    resp = client.get("/auth")
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"
    assert resp.json()["code"] == "UNAUTHORIZED"


def test_err_03_422_en_query_lista_solo_nombres_de_campo(client):
    resp = client.get("/n", params={"n": "valor-sentinela-987654"})
    assert resp.status_code == 422
    assert resp.json() == {"code": "VALIDATION_ERROR", "message": "Entrada inválida en: query.n."}
    assert "valor-sentinela-987654" not in resp.text


def test_err_04_422_en_cuerpo_no_devuelve_los_valores_enviados(client):
    resp = client.post("/pay", json={"amount": -987654})
    assert resp.status_code == 422
    assert resp.json() == {"code": "VALIDATION_ERROR", "message": "Entrada inválida en: body.amount."}
    assert "987654" not in resp.text

    missing = client.post("/pay", json={})
    assert missing.status_code == 422
    assert missing.json()["message"] == "Entrada inválida en: body.amount."


def test_err_05_422_con_json_ilegible_no_refleja_el_cuerpo(client):
    resp = client.post("/pay", content="no-json-secret", headers={"content-type": "application/json"})
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
    assert "no-json-secret" not in resp.text


def test_err_06_500_es_generico_y_la_traza_solo_va_al_log(client, caplog):
    with caplog.at_level(logging.ERROR, logger="app.errors"):
        resp = client.get("/boom")
    assert resp.status_code == 500
    assert resp.json() == {"code": "INTERNAL_ERROR", "message": "Error interno del servidor."}
    assert "clave-secreta-123" not in resp.text
    assert "Traceback" not in resp.text
    assert any(r.name == "app.errors" and r.levelno == logging.ERROR and r.exc_info for r in caplog.records)
