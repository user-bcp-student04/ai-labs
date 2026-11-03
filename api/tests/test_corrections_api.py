"""Pruebas de corrección por hallazgo (H-API-01, 03, 04, 07, 08, 09, 10, 12, 13).

Fallan sobre el código legado y deben pasar tras cada corrección.
"""

import importlib
import types
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient

from app.main import create_app

Headers = Callable[..., dict[str, str]]
GENERIC_TOKEN_DETAIL = "Invalid or expired token"
MAX_UPLOAD_BYTES = 1024 * 1024
ALLOWED_ORIGIN = "http://localhost:4200"
UNKNOWN_ORIGIN = "https://evil.example.test"


def preflight(client: TestClient, origin: str) -> dict[str, str]:
    response = client.options(
        "/api/tasks",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    return dict(response.headers)


def upload(client: TestClient, headers: dict[str, str], name: str, content: bytes = b"x"):
    return client.post("/api/requirements", headers=headers, files={"file": (name, content, "text/plain")})


# H-API-01
def test_quotes_in_task_text_fields_are_stored_literally(client: TestClient, auth_headers: Headers) -> None:
    payload = {"title": "O'Brien's task", "description": "it's \"quoted\"; -- end"}

    created = client.post("/api/tasks", headers=auth_headers(), json=payload)

    assert created.status_code == 201
    assert (created.json()["title"], created.json()["description"]) == (payload["title"], payload["description"])


def test_username_with_quote_is_treated_as_literal_data(client: TestClient, auth_headers: Headers) -> None:
    headers = auth_headers("o'neil")

    assert client.get("/api/tasks", headers=headers).json() == []
    assert client.get("/api/summary", headers=headers).json()["total"] == 0


# H-API-03
@pytest.mark.parametrize("path", ["/api/tasks", "/api/summary"])
def test_querying_another_owner_is_forbidden(client: TestClient, auth_headers: Headers, path: str) -> None:
    response = client.get(path, headers=auth_headers(), params={"owner": "trainer"})

    assert response.status_code == 403


def test_explicit_own_owner_is_allowed(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/tasks", headers=auth_headers(), params={"owner": "student"})

    assert response.status_code == 200
    assert {task["owner"] for task in response.json()} == {"student"}


def test_owner_in_body_is_ignored(client: TestClient, auth_headers: Headers) -> None:
    created = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "owner": "trainer"})

    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    trainer_tasks = client.get("/api/tasks", headers=auth_headers("trainer")).json()
    assert [task["title"] for task in trainer_tasks] == ["Trainer notes"]


# H-API-04
@pytest.mark.parametrize("raw_name", ["../escape.txt", "..\\escape.txt", "/tmp/escape.txt"])
def test_upload_strips_path_components(
    client: TestClient, auth_headers: Headers, upload_dir: Path, raw_name: str
) -> None:
    response = upload(client, auth_headers(), raw_name)

    assert response.status_code == 201
    assert response.json()["fileName"] == "escape.txt"
    assert (upload_dir / "escape.txt").exists()
    assert not (upload_dir.parent / "escape.txt").exists()


def test_upload_replaces_unsafe_characters(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    response = upload(client, auth_headers(), "my report (1).txt")

    assert response.json()["fileName"] == "my_report__1_.txt"
    assert (upload_dir / "my_report__1_.txt").exists()


def test_upload_rejects_disallowed_extension(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    response = upload(client, auth_headers(), "run.exe")

    assert response.status_code == 415
    assert not (upload_dir / "run.exe").exists()


@pytest.mark.parametrize("raw_name", ["..", ".", "/", "a" * 200 + ".txt"])
def test_upload_rejects_invalid_names(client: TestClient, auth_headers: Headers, raw_name: str) -> None:
    assert upload(client, auth_headers(), raw_name).status_code == 400


def test_upload_rejects_oversized_file(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    response = upload(client, auth_headers(), "big.txt", b"x" * (MAX_UPLOAD_BYTES + 1))

    assert response.status_code == 413
    assert not (upload_dir / "big.txt").exists()


def test_upload_accepts_file_at_the_size_limit(client: TestClient, auth_headers: Headers) -> None:
    response = upload(client, auth_headers(), "limit.txt", b"x" * MAX_UPLOAD_BYTES)

    assert (response.status_code, response.json()["size"]) == (201, MAX_UPLOAD_BYTES)


def test_upload_does_not_expose_server_path(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    stored_at = upload(client, auth_headers(), "requirements.txt").json()["storedAt"]

    assert stored_at == "requirements.txt"
    assert str(upload_dir) not in stored_at


# H-API-07
def test_openapi_declares_typed_models(client: TestClient) -> None:
    schemas = set(client.get("/openapi.json").json()["components"]["schemas"])

    assert {"TaskCreateRequest", "TaskResponse", "TaskSummaryResponse"} <= schemas


# H-API-08
def test_invalid_token_detail_is_generic(client: TestClient) -> None:
    response = client.get("/api/tasks", headers={"Authorization": "Bearer ***not-base64***"})

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_TOKEN_DETAIL}


def test_backend_health_hides_upstream_error_details(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: object, method: str, url: str, **kwargs: object) -> None:
        raise urllib3.exceptions.HTTPError("internal-host-secret-detail")

    monkeypatch.setattr(urllib3.PoolManager, "request", fail)

    response = client.get("/api/backend-health", headers=auth_headers())

    assert "internal-host-secret-detail" not in response.text
    assert response.json()["status"] == 0


# H-API-11
def test_backend_health_limits_upstream_body(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream = types.SimpleNamespace(status=200, data=b"x" * 5000)
    monkeypatch.setattr(urllib3.PoolManager, "request", lambda self, method, url, **kwargs: upstream)

    body = client.get("/api/backend-health", headers=auth_headers()).json()

    assert 0 < len(body["body"]) <= 1000


# H-API-09
def test_cors_allows_configured_origin(client: TestClient) -> None:
    assert preflight(client, ALLOWED_ORIGIN).get("access-control-allow-origin") == ALLOWED_ORIGIN


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    assert "access-control-allow-origin" not in preflight(client, UNKNOWN_ORIGIN)


def test_cors_origins_come_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WORKSHOP_CORS_ORIGINS", UNKNOWN_ORIGIN)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as custom_client:
        assert preflight(custom_client, UNKNOWN_ORIGIN).get("access-control-allow-origin") == UNKNOWN_ORIGIN
        assert "access-control-allow-origin" not in preflight(custom_client, ALLOWED_ORIGIN)


# H-API-10
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": 123},
        {"title": "t" * 201},
        {"title": "t", "description": "d" * 2001},
        {"title": "t", "status": "BOGUS"},
        {"title": "t", "priority": "URGENT"},
        {"title": "t", "status": "x' OR '1'='1"},
    ],
)
def test_create_task_rejects_invalid_payload(client: TestClient, auth_headers: Headers, payload: dict) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json=payload)

    assert response.status_code == 422
    assert len(client.get("/api/tasks", headers=auth_headers()).json()) == 2


# H-API-12
def test_concurrent_requests_do_not_corrupt_state(client: TestClient, auth_headers: Headers) -> None:
    headers = auth_headers()
    workers, posts_per_worker = 8, 5

    def work(index: int) -> list[int]:
        codes = [
            client.post("/api/tasks", headers=headers, json={"title": f"t{index}-{n}"}).status_code
            for n in range(posts_per_worker)
        ]
        return codes + [client.get("/api/tasks", headers=headers).status_code]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        codes = [code for result in pool.map(work, range(workers)) for code in result]

    assert set(codes) <= {200, 201}
    assert len(client.get("/api/tasks", headers=headers).json()) == 2 + workers * posts_per_worker


# H-API-13
def test_importing_main_module_has_no_disk_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.main as main_module

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WORKSHOP_DB_PATH", raising=False)
    monkeypatch.delenv("WORKSHOP_UPLOAD_DIR", raising=False)

    importlib.reload(main_module)

    assert list(tmp_path.iterdir()) == []


def test_startup_initializes_database_and_upload_dir(tmp_path: Path) -> None:
    database, uploads = tmp_path / "db" / "workshop.db", tmp_path / "files"
    app = create_app(str(database), str(uploads))
    assert not database.exists()

    with TestClient(app):
        pass

    assert database.exists() and uploads.is_dir()
