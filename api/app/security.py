import base64
import logging
import time

from fastapi import Header, HTTPException

from app.constants import BEARER_PREFIX, INVALID_TOKEN_DETAIL
from app.schemas import Identity

logger = logging.getLogger(__name__)

# H-API-02 sigue pendiente: el formato del token se acordará con auth.
LEGACY_SECRET = "WORKSHOP_SECRET_2026"
LEGACY_TOKEN_PARTS = 4


def parse_legacy_token(token: str, now: float) -> Identity:
    username, role, expires_at, secret = _split_legacy_token(token)
    if secret != LEGACY_SECRET:
        raise ValueError("secret mismatch")
    if int(expires_at) < int(now):
        raise ValueError("token expired")
    return Identity(username=username, role=role)


def _split_legacy_token(token: str) -> list[str]:
    parts = base64.b64decode(token).decode("utf-8").split("|")
    if len(parts) != LEGACY_TOKEN_PARTS:
        raise ValueError("unexpected token shape")
    return parts


def legacy_identity(authorization: str = Header(default="")) -> Identity:
    try:
        return parse_legacy_token(authorization.removeprefix(BEARER_PREFIX), time.time())
    except ValueError as error:
        logger.warning("Rejected authorization header: %s", error)
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_DETAIL) from error
