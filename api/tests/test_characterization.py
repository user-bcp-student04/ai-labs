"""Pruebas de caracterización (H-API-14): fijan el contrato observado.

Deben pasar igual antes y después del refactor.
"""

import types
from collections.abc import Callable
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient

from conftest import build_token

TASK_KEYS = {"id", "title", "description", "status", "owner", "priority", "createdAt"}
SUMMARY_KEYS = ["owner", "total", "byStatus", "highPriorityOpen"]
Headers = Callable[..., dict[str, str]]

PROTECTED_REQUESTS = {
    "list_tasks": ("get", "/api/tasks", {}),
    "create_task": ("post", "/api/tasks", {"json": {"title": "x"}}),
    "summary": ("get", "/api/summary", {}),
    "upload": ("post", "/api/requirements", {"files": {"file": ("a.txt", b"x", "text/plain")}}),
    "health": ("get", "/api/backend-health", {}),
}

INVALID_AUTHORIZATIONS = {
    "missing": {},
    "garbage": {"Authorization": "Bearer not-a-token"},
    "expired": {"Authorization": f"Bearer {build_token(ttl_seconds=-60)}"},
    "wrong_secret": {"Authorization": f"Bearer {build_token(secret='other')}"},
}


def create_task(client: TestClient, headers: dict[str, str], **fields: str) -> dict:
    response = client.post("/api/tasks", headers=headers, json=fields)
    assert response.status_code == 201
    return response.json()


def test_lists_seeded_tasks_with_contract_keys(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/tasks", headers=auth_headers())

    tasks = response.json()
    assert response.status_code == 200
    assert [task["title"] for task in tasks] == ["Refactor login", "Review API"]
    assert all(set(task) == TASK_KEYS for task in tasks)
    assert [task["id"] for task in tasks] == sorted(task["id"] for task in tasks)


def test_create_task_returns_full_task(client: TestClient, auth_headers: Headers) -> None:
    created = create_task(
        client, auth_headers(), title="Add tests", description="Cover api", status="DONE", priority="LOW"
    )

    assert set(created) == TASK_KEYS
    assert created["id"] == 4
    assert (created["title"], created["description"]) == ("Add tests", "Cover api")
    assert (created["status"], created["priority"], created["owner"]) == ("DONE", "LOW", "student")


def test_create_task_applies_defaults(client: TestClient, auth_headers: Headers) -> None:
    created = create_task(client, auth_headers(), title="Only title")

    assert (created["status"], created["priority"], created["owner"]) == ("TODO", "MEDIUM", "student")
    assert created["description"] == ""


def test_summary_counts_statuses_and_open_high_priority(client: TestClient, auth_headers: Headers) -> None:
    headers = auth_headers()
    for status, priority in [("DONE", "HIGH"), ("ARCHIVED", "HIGH"), ("IN_PROGRESS", "HIGH"), ("TODO", "LOW")]:
        create_task(client, headers, title="t", status=status, priority=priority)

    body = client.get("/api/summary", headers=headers).json()

    assert list(body) == SUMMARY_KEYS
    assert body == {
        "owner": "student",
        "total": 6,
        "byStatus": {"TODO": 2, "IN_PROGRESS": 2, "DONE": 1, "ARCHIVED": 1},
        "highPriorityOpen": 2,
    }


def test_summary_for_user_without_tasks(client: TestClient, auth_headers: Headers) -> None:
    body = client.get("/api/summary", headers=auth_headers("nobody")).json()

    assert body == {"owner": "nobody", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


@pytest.mark.parametrize("authorization", INVALID_AUTHORIZATIONS.values(), ids=INVALID_AUTHORIZATIONS.keys())
@pytest.mark.parametrize("request_spec", PROTECTED_REQUESTS.values(), ids=PROTECTED_REQUESTS.keys())
def test_protected_routes_reject_invalid_tokens(
    client: TestClient, request_spec: tuple, authorization: dict[str, str]
) -> None:
    method, path, kwargs = request_spec

    response = client.request(method, path, headers=authorization, **kwargs)

    assert response.status_code == 401


def test_upload_keeps_contract_fields(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    response = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
    )

    body = response.json()
    assert response.status_code == 201
    assert set(body) == {"owner", "fileName", "storedAt", "size"}
    assert (body["owner"], body["fileName"], body["size"]) == ("student", "requirements.txt", 24)
    assert (upload_dir / "requirements.txt").read_bytes() == b"Login must be accessible"


def test_upload_with_same_name_overwrites_previous_file(
    client: TestClient, auth_headers: Headers, upload_dir: Path
) -> None:
    for content in (b"first", b"second"):
        response = client.post(
            "/api/requirements", headers=auth_headers(), files={"file": ("notes.txt", content, "text/plain")}
        )
        assert response.status_code == 201

    assert (upload_dir / "notes.txt").read_bytes() == b"second"


def test_backend_health_reports_upstream_response(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    upstream = types.SimpleNamespace(status=200, data=b'{"status":"UP"}')
    monkeypatch.setattr(urllib3.PoolManager, "request", lambda self, method, url, **kwargs: upstream)

    response = client.get("/api/backend-health", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}


def test_backend_health_reports_status_zero_when_upstream_fails(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: object, method: str, url: str, **kwargs: object) -> None:
        raise urllib3.exceptions.HTTPError("connection refused")

    monkeypatch.setattr(urllib3.PoolManager, "request", fail)

    body = client.get("/api/backend-health", headers=auth_headers()).json()

    assert (body["requestedBy"], body["status"]) == ("student", 0)
    assert set(body) == {"requestedBy", "status", "body"}


def test_published_paths_are_preserved(client: TestClient) -> None:
    paths = set(client.get("/openapi.json").json()["paths"])

    assert {"/api/tasks", "/api/summary", "/api/requirements", "/api/backend-health"} <= paths
