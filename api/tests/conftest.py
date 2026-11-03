import base64
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# Valor de prueba del formato legado; H-API-02 sigue pendiente de acuerdo con auth.
LEGACY_TEST_SECRET = "WORKSHOP_SECRET_2026"
DEFAULT_TOKEN_TTL_SECONDS = 3600


def build_token(
    username: str = "student",
    role: str = "STUDENT",
    ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
    secret: str = LEGACY_TEST_SECRET,
) -> str:
    raw = f"{username}|{role}|{int(time.time()) + ttl_seconds}|{secret}"
    return base64.b64encode(raw.encode()).decode()


@pytest.fixture
def auth_headers() -> Callable[..., dict[str, str]]:
    def build(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
        return {"Authorization": f"Bearer {build_token(username, role)}"}

    return build


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    return tmp_path / "uploads"


@pytest.fixture
def client(tmp_path: Path, upload_dir: Path) -> Iterator[TestClient]:
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
