# api/tests/test_h03_mock_contract.py
"""H03 · MOCK-01…MOCK-15: contrato W3/W2 contra el mock configurado (solo lectura).

Supuestos T-1/T-2/T-7: el contrato es el de trabajo del Arquitecto y los datos
vienen de variables de entorno H03_*. Si falta una variable, la prueba FALLA (no se omite).
Un fallo por contrato distinto es un hallazgo sobre P-1, no un defecto atribuible al cambio.
"""
import os
import time
import uuid

import httpx
import pytest

IDEM = "Idempotency-Key"


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.fail(f"Falta la variable obligatoria {name} (datos del mock configurado).", pytrace=False)
    return value


@pytest.fixture()
def w3():
    with httpx.Client(base_url=_env("H03_W3_BASE_URL"), timeout=10) as c:
        yield c


@pytest.fixture()
def w2():
    with httpx.Client(base_url=_env("H03_W2_BASE_URL"), timeout=10) as c:
        yield c


def _resolve(w3, payload: str) -> httpx.Response:
    return w3.post("/qrs/resolve", json={"payload": payload})


def _pay(w2, qr_id: str, amount, currency: str, key: str) -> httpx.Response:
    return w2.post(
        "/payments",
        json={"qrId": qr_id, "amount": amount, "currency": currency},
        headers={IDEM: key},
    )


def _resolved(w3, env_name: str) -> dict:
    resp = _resolve(w3, _env(env_name))
    assert resp.status_code == 200, resp.text
    return resp.json()


def _created(w2, qr: dict, amount) -> dict:
    resp = _pay(w2, qr["qrId"], amount, qr["currency"], str(uuid.uuid4()))
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def test_mock_01_resolve_qr_de_importe_fijo(w3):
    body = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    assert isinstance(body["qrId"], str) and body["qrId"]
    assert isinstance(body["merchant"]["name"], str) and body["merchant"]["name"]
    assert body["amountType"] == "fixed"
    assert isinstance(body["amount"], (int, float)) and body["amount"] > 0
    assert isinstance(body["currency"], str) and body["currency"]


def test_mock_02_resolve_qr_de_monto_abierto(w3):
    body = _resolved(w3, "H03_QR_PAYLOAD_OPEN")
    assert body["amountType"] == "open"
    assert body.get("amount") in (None,)
    assert body["qrId"] and body["merchant"]["name"] and body["currency"]


@pytest.mark.parametrize(
    "env_name,status,code",
    [
        ("H03_QR_PAYLOAD_INVALID", 400, "QR_INVALID"),
        ("H03_QR_PAYLOAD_UNKNOWN", 404, "QR_UNKNOWN"),
        ("H03_QR_PAYLOAD_EXPIRED", 410, "QR_EXPIRED"),
        ("H03_QR_PAYLOAD_CONFLICT", 409, "QR_CONFLICT"),
    ],
    ids=["mock_03_invalido", "mock_04_desconocido", "mock_05_expirado", "mock_06_conflicto"],
)
def test_mock_03_a_06_resolve_errores_de_recuperacion(w3, env_name, status, code):
    resp = _resolve(w3, _env(env_name))
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["code"] == code
    assert isinstance(body["message"], str)


def test_mock_07_resolve_con_payload_vacio_es_invalido(w3):
    resp = _resolve(w3, "")
    assert resp.status_code == 400, resp.text
    assert resp.json()["code"] == "QR_INVALID"


def test_mock_08_crear_pago_preserva_qr_id(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    created = _created(w2, qr, qr["amount"])
    assert created["paymentId"] and created["reference"] and created["status"]
    assert created["qrId"] == qr["qrId"]


def test_mock_09_misma_clave_y_mismo_cuerpo_devuelve_el_mismo_pago(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    key = str(uuid.uuid4())
    first = _pay(w2, qr["qrId"], qr["amount"], qr["currency"], key)
    second = _pay(w2, qr["qrId"], qr["amount"], qr["currency"], key)
    assert first.status_code in (200, 201), first.text
    assert second.status_code in (200, 201), second.text
    assert first.json()["paymentId"] == second.json()["paymentId"]


def test_mock_10_misma_clave_con_cuerpo_distinto_es_conflicto(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_OPEN")
    key = str(uuid.uuid4())
    first = _pay(w2, qr["qrId"], 10, qr["currency"], key)
    assert first.status_code in (200, 201), first.text
    second = _pay(w2, qr["qrId"], 11, qr["currency"], key)
    assert second.status_code == 409, second.text
    assert second.json()["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.parametrize("amount", [0, -1])
def test_mock_11_importe_no_positivo_en_monto_abierto_es_rechazado(w3, w2, amount):
    qr = _resolved(w3, "H03_QR_PAYLOAD_OPEN")
    resp = _pay(w2, qr["qrId"], amount, qr["currency"], str(uuid.uuid4()))
    assert resp.status_code == 422, resp.text
    assert resp.json()["code"] == "AMOUNT_INVALID"


def test_mock_12_consulta_de_estado_y_recibo(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    created = _created(w2, qr, qr["amount"])
    status = w2.get(f"/payments/{created['paymentId']}")
    assert status.status_code == 200, status.text
    assert isinstance(status.json()["status"], str) and status.json()["status"]
    receipt = w2.get(f"/payments/{created['paymentId']}/receipt")
    assert receipt.status_code == 200, receipt.text
    assert isinstance(receipt.json(), dict)


def test_mock_13_pago_inexistente_devuelve_404_en_estado_y_recibo(w2):
    unknown = f"no-existe-{uuid.uuid4()}"
    assert w2.get(f"/payments/{unknown}").status_code == 404
    assert w2.get(f"/payments/{unknown}/receipt").status_code == 404


@pytest.mark.parametrize(
    "env_name,status,code",
    [("H03_QR_ID_EXPIRED", 410, "QR_EXPIRED"), ("H03_QR_ID_CONFLICT", 409, "QR_CONFLICT")],
    ids=["mock_14a_expirado", "mock_14b_conflicto"],
)
def test_mock_14_crear_pago_con_qr_expirado_o_en_conflicto(w2, env_name, status, code):
    resp = _pay(w2, _env(env_name), 10, "COP", str(uuid.uuid4()))
    assert resp.status_code == status, resp.text
    assert resp.json()["code"] == code


def test_mock_15_el_estado_no_cambia_sin_accion_manual(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    created = _created(w2, qr, qr["amount"])
    before = w2.get(f"/payments/{created['paymentId']}").json()["status"]
    time.sleep(3)
    after = w2.get(f"/payments/{created['paymentId']}").json()["status"]
    assert before == after
