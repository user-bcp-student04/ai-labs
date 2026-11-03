"""Pruebas por endpoint según docs/ENDPOINTS.md (sección api).

Cada endpoint cubre camino feliz, casos borde y cada respuesta de error documentada.
Sin red real: la llamada a `auth` se simula con `urllib3.PoolManager.request`.
"""

import types
from collections.abc import Callable
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient

from app.repository import TaskRepository
from test_characterization import PROTECTED_REQUESTS

Headers = Callable[..., dict[str, str]]

UNAUTHORIZED_BODY = {"detail": "Invalid or expired token"}
FORBIDDEN_BODY = {"detail": "Access to another owner's data is not allowed"}
MAX_UPLOAD_BYTES = 1024 * 1024
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
HEALTH_BODY_LIMIT = 1000
CONFIGURED_HEALTH_URL = "http://auth.test:8080/q/health"
HEALTH_TIMEOUT_SECONDS = 3.0


def stub_upstream(monkeypatch: pytest.MonkeyPatch, status: int, data: bytes) -> list[tuple]:
    calls: list[tuple] = []

    def fake_request(self: object, method: str, url: str, **kwargs: object) -> types.SimpleNamespace:
        calls.append((method, url, kwargs))
        return types.SimpleNamespace(status=status, data=data)

    monkeypatch.setattr(urllib3.PoolManager, "request", fake_request)
    return calls


def create_task(client: TestClient, headers: dict[str, str], **fields: object) -> dict:
    response = client.post("/api/tasks", headers=headers, json=fields)
    assert response.status_code == 201
    return response.json()


def upload(client: TestClient, headers: dict[str, str], name: str, content: bytes = b"x"):
    return client.post("/api/requirements", headers=headers, files={"file": (name, content, "text/plain")})


# --- Errores comunes (todos los endpoints) ---------------------------------------------------


@pytest.mark.parametrize("request_spec", PROTECTED_REQUESTS.values(), ids=PROTECTED_REQUESTS.keys())
def test_unauthorized_response_body_is_generic_on_every_endpoint(
    client: TestClient, request_spec: tuple
) -> None:
    method, path, kwargs = request_spec

    response = client.request(method, path, **kwargs)

    assert (response.status_code, response.json()) == (401, UNAUTHORIZED_BODY)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("delete", "/api/tasks"),
        ("put", "/api/tasks"),
        ("post", "/api/summary"),
        ("get", "/api/requirements"),
        ("post", "/api/backend-health"),
    ],
)
def test_undefined_method_returns_405(client: TestClient, auth_headers: Headers, method: str, path: str) -> None:
    response = client.request(method, path, headers=auth_headers())

    assert (response.status_code, response.json()) == (405, {"detail": "Method Not Allowed"})


def test_unexpected_error_returns_generic_500(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(self: object, owner: str) -> None:
        raise RuntimeError("db exploded")

    monkeypatch.setattr(TaskRepository, "list_by_owner", explode)

    response = client.get("/api/tasks", headers=auth_headers())

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "db exploded" not in response.text


# --- GET /api/tasks -------------------------------------------------------------------------


def test_list_tasks_returns_only_own_tasks_in_id_order(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers("trainer"), title="Trainer secret")
    create_task(client, auth_headers(), title="Mine")

    tasks = client.get("/api/tasks", headers=auth_headers()).json()

    assert [task["title"] for task in tasks] == ["Refactor login", "Review API", "Mine"]
    assert {task["owner"] for task in tasks} == {"student"}
    assert [task["id"] for task in tasks] == sorted(task["id"] for task in tasks)


def test_list_tasks_returns_empty_array_for_user_without_tasks(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/tasks", headers=auth_headers("nobody"))

    assert (response.status_code, response.json()) == (200, [])


def test_list_tasks_blank_owner_parameter_means_own_tasks(client: TestClient, auth_headers: Headers) -> None:
    without_param = client.get("/api/tasks", headers=auth_headers()).json()

    with_blank_param = client.get("/api/tasks", headers=auth_headers(), params={"owner": ""})

    assert (with_blank_param.status_code, with_blank_param.json()) == (200, without_param)


def test_user_cannot_read_another_owners_tasks(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers("trainer"), title="Trainer secret")

    forbidden = client.get("/api/tasks", headers=auth_headers(), params={"owner": "trainer"})
    own = client.get("/api/tasks", headers=auth_headers())

    assert (forbidden.status_code, forbidden.json()) == (403, FORBIDDEN_BODY)
    assert "Trainer" not in forbidden.text
    assert "Trainer secret" not in own.text


# --- POST /api/tasks ------------------------------------------------------------------------


def test_create_task_happy_path_persists_and_lists_the_task(client: TestClient, auth_headers: Headers) -> None:
    created = create_task(
        client, auth_headers(), title="Write docs", description="Document", status="IN_PROGRESS", priority="HIGH"
    )

    listed = client.get("/api/tasks", headers=auth_headers()).json()

    assert created in listed
    assert (created["owner"], created["status"], created["priority"]) == ("student", "IN_PROGRESS", "HIGH")


@pytest.mark.parametrize("status", ["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"])
def test_create_task_accepts_every_documented_status(client: TestClient, auth_headers: Headers, status: str) -> None:
    assert create_task(client, auth_headers(), title="t", status=status)["status"] == status


@pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
def test_create_task_accepts_every_documented_priority(
    client: TestClient, auth_headers: Headers, priority: str
) -> None:
    assert create_task(client, auth_headers(), title="t", priority=priority)["priority"] == priority


def test_create_task_accepts_minimum_and_maximum_lengths(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers(), title="a")
    longest = create_task(
        client, auth_headers(), title="t" * MAX_TITLE_LENGTH, description="d" * MAX_DESCRIPTION_LENGTH
    )

    assert (len(longest["title"]), len(longest["description"])) == (MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH)


def test_create_task_ignores_unknown_fields(client: TestClient, auth_headers: Headers) -> None:
    created = create_task(client, auth_headers(), title="t", owner="trainer", unexpected="value")

    assert "unexpected" not in created
    assert created["owner"] == "student"


def test_create_task_missing_title_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert (error["type"], error["loc"], error["msg"]) == ("missing", ["body", "title"], "Field required")


def test_create_task_invalid_status_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "status": "BOGUS"})

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"], error["input"]) == ("enum", ["body", "status"], "BOGUS")


def test_create_task_invalid_priority_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "priority": "URGENT"})

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("enum", ["body", "priority"])


def test_create_task_null_description_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "description": None})

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("string_type", ["body", "description"])


@pytest.mark.parametrize(
    ("payload", "error_type"),
    [
        ({"title": ""}, "string_too_short"),
        ({"title": "t" * (MAX_TITLE_LENGTH + 1)}, "string_too_long"),
        ({"title": "t", "description": "d" * (MAX_DESCRIPTION_LENGTH + 1)}, "string_too_long"),
        ({"title": 123}, "string_type"),
    ],
)
def test_create_task_length_and_type_error_bodies(
    client: TestClient, auth_headers: Headers, payload: dict, error_type: str
) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == error_type


def test_create_task_malformed_json_error_body(client: TestClient, auth_headers: Headers) -> None:
    headers = {**auth_headers(), "Content-Type": "application/json"}

    response = client.post("/api/tasks", headers=headers, content="nope")

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


def test_create_task_cannot_assign_another_owner(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers(), title="Planted", owner="trainer")

    trainer_titles = [task["title"] for task in client.get("/api/tasks", headers=auth_headers("trainer")).json()]

    assert trainer_titles == ["Trainer notes"]


# --- GET /api/summary -----------------------------------------------------------------------


def test_summary_happy_path_for_seeded_user(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/summary", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_summary_accepts_explicit_own_owner(client: TestClient, auth_headers: Headers) -> None:
    implicit = client.get("/api/summary", headers=auth_headers()).json()

    explicit = client.get("/api/summary", headers=auth_headers(), params={"owner": "student"})

    assert (explicit.status_code, explicit.json()) == (200, implicit)


def test_summary_blank_owner_parameter_means_own_summary(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/summary", headers=auth_headers(), params={"owner": ""})

    assert response.json()["owner"] == "student"


def test_summary_excludes_other_users_tasks(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers("trainer"), title="x", priority="HIGH")

    summary = client.get("/api/summary", headers=auth_headers()).json()

    assert (summary["total"], summary["highPriorityOpen"]) == (2, 1)


def test_summary_of_another_owner_is_forbidden(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/summary", headers=auth_headers(), params={"owner": "trainer"})

    assert (response.status_code, response.json()) == (403, FORBIDDEN_BODY)


# --- POST /api/requirements -----------------------------------------------------------------


@pytest.mark.parametrize("file_name", ["notes.txt", "notes.md", "notes.pdf", "NOTES.TXT"])
def test_upload_accepts_each_allowed_extension(
    client: TestClient, auth_headers: Headers, upload_dir: Path, file_name: str
) -> None:
    response = upload(client, auth_headers(), file_name, b"abc")

    assert (response.status_code, response.json()) == (
        201,
        {"owner": "student", "fileName": file_name, "storedAt": file_name, "size": 3},
    )
    assert (upload_dir / file_name).read_bytes() == b"abc"


def test_upload_rejects_file_without_extension(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    response = upload(client, auth_headers(), "README")

    assert (response.status_code, response.json()) == (415, {"detail": "File extension not allowed"})
    assert not (upload_dir / "README").exists()


def test_upload_size_limit_boundary(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    at_limit = upload(client, auth_headers(), "at-limit.txt", b"x" * MAX_UPLOAD_BYTES)
    over_limit = upload(client, auth_headers(), "over-limit.txt", b"x" * (MAX_UPLOAD_BYTES + 1))

    assert at_limit.status_code == 201
    assert (over_limit.status_code, over_limit.json()) == (413, {"detail": "File exceeds the maximum allowed size"})
    assert not (upload_dir / "over-limit.txt").exists()


@pytest.mark.parametrize(
    ("file_name", "expected_status", "expected_detail"),
    [
        ("..", 400, "Invalid file name"),
        ("a" * 101 + ".txt", 400, "Invalid file name"),
        ("run.exe", 415, "File extension not allowed"),
        ("archive.tar.gz", 415, "File extension not allowed"),
    ],
)
def test_upload_rejection_bodies(
    client: TestClient, auth_headers: Headers, file_name: str, expected_status: int, expected_detail: str
) -> None:
    response = upload(client, auth_headers(), file_name)

    assert (response.status_code, response.json()) == (expected_status, {"detail": expected_detail})


def test_upload_missing_file_part_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/requirements", headers=auth_headers())

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("missing", ["body", "file"])


def test_upload_empty_filename_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = upload(client, auth_headers(), "")

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("value_error", ["body", "file"])


def test_upload_keeps_files_inside_upload_directory(
    client: TestClient, auth_headers: Headers, upload_dir: Path
) -> None:
    upload(client, auth_headers(), "../../outside.txt")

    assert sorted(path.name for path in upload_dir.iterdir()) == ["outside.txt"]
    assert not (upload_dir.parent / "outside.txt").exists()


# --- GET /api/backend-health ----------------------------------------------------------------


def test_health_happy_path_reports_upstream_status_and_body(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub_upstream(monkeypatch, 200, b'{"status":"UP"}')

    response = client.get("/api/backend-health", headers=auth_headers("ana"))

    assert (response.status_code, response.json()) == (
        200,
        {"requestedBy": "ana", "status": 200, "body": '{"status":"UP"}'},
    )


def test_health_forwards_upstream_error_status_with_http_200(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub_upstream(monkeypatch, 503, b"down for maintenance")

    response = client.get("/api/backend-health", headers=auth_headers())

    assert (response.status_code, response.json()["status"], response.json()["body"]) == (
        200,
        503,
        "down for maintenance",
    )


def test_health_body_is_cut_at_the_documented_limit(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub_upstream(monkeypatch, 200, b"x" * (HEALTH_BODY_LIMIT + 500))

    body = client.get("/api/backend-health", headers=auth_headers()).json()["body"]

    assert body == "x" * HEALTH_BODY_LIMIT


@pytest.mark.parametrize("failure", [urllib3.exceptions.HTTPError("refused"), ConnectionRefusedError("refused")])
def test_health_reports_unavailable_backend_with_http_200(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    def fail(self: object, method: str, url: str, **kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(urllib3.PoolManager, "request", fail)

    response = client.get("/api/backend-health", headers=auth_headers())

    assert (response.status_code, response.json()) == (
        200,
        {"requestedBy": "student", "status": 0, "body": "Backend unavailable"},
    )


def test_health_uses_server_configured_url_and_timeout(
    tmp_path: Path, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.main import create_app

    monkeypatch.setenv("AUTH_HEALTH_URL", CONFIGURED_HEALTH_URL)
    calls = stub_upstream(monkeypatch, 200, b"UP")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as configured_client:
        configured_client.get("/api/backend-health", headers=auth_headers(), params={"url": "http://evil.test"})

    assert [(method, url, kwargs["timeout"]) for method, url, kwargs in calls] == [
        ("GET", CONFIGURED_HEALTH_URL, HEALTH_TIMEOUT_SECONDS)
    ]
