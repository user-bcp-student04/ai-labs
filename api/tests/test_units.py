"""Pruebas unitarias de las capas nuevas (H-API-01, 03, 04, 06, 07, 11)."""

import asyncio
import io
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from pydantic import ValidationError

from app.config import load_settings, parse_origins, validate_health_url
from app.constants import MAX_FILENAME_LENGTH, TaskPriority, TaskStatus
from app.repository import TaskRecord, TaskRepository
from app.schemas import Identity, TaskCreateRequest
from app.security import parse_legacy_token
from app.services import (
    TaskService,
    is_high_priority_open,
    read_with_limit,
    resolve_owner,
    sanitize_filename,
    validate_extension,
)
from conftest import build_token

STUDENT = Identity(username="student", role="STUDENT")
INJECTION_ATTEMPT = "x' OR '1'='1"


@pytest.fixture
def repository(tmp_path: Path) -> TaskRepository:
    task_repository = TaskRepository(str(tmp_path / "nested" / "workshop.db"))
    task_repository.initialize_schema()
    return task_repository


def record(status: str, priority: str) -> TaskRecord:
    return TaskRecord(1, "t", "d", status, "student", priority, "2026-01-01")


# H-API-01
def test_repository_treats_quotes_as_literal_data(repository: TaskRepository) -> None:
    request = TaskCreateRequest(title=INJECTION_ATTEMPT, description="it's")

    saved = repository.insert(INJECTION_ATTEMPT, request)

    assert (saved.title, saved.owner) == (INJECTION_ATTEMPT, INJECTION_ATTEMPT)
    assert [task.id for task in repository.list_by_owner(INJECTION_ATTEMPT)] == [saved.id]
    assert repository.list_by_owner("x' OR '1'='2") == []


def test_repository_seed_is_not_duplicated(repository: TaskRepository) -> None:
    repository.initialize_schema()

    assert len(repository.list_by_owner("student")) == 2
    assert len(repository.list_by_owner("trainer")) == 1


# H-API-03
def test_resolve_owner_defaults_to_identity() -> None:
    assert resolve_owner(STUDENT, None) == "student"
    assert resolve_owner(STUDENT, "") == "student"
    assert resolve_owner(STUDENT, "student") == "student"


def test_resolve_owner_rejects_other_owner() -> None:
    with pytest.raises(HTTPException) as error:
        resolve_owner(STUDENT, "trainer")

    assert error.value.status_code == 403


# H-API-07
@pytest.mark.parametrize(
    ("status", "priority", "expected"),
    [
        (TaskStatus.TODO, TaskPriority.HIGH, True),
        (TaskStatus.IN_PROGRESS, TaskPriority.HIGH, True),
        (TaskStatus.DONE, TaskPriority.HIGH, False),
        (TaskStatus.ARCHIVED, TaskPriority.HIGH, False),
        (TaskStatus.TODO, TaskPriority.MEDIUM, False),
        ("LEGACY", "HIGH", True),
    ],
)
def test_is_high_priority_open(status: str, priority: str, expected: bool) -> None:
    assert is_high_priority_open(record(status, priority)) is expected


def test_service_summary_matches_repository_data(repository: TaskRepository) -> None:
    service = TaskService(repository)
    service.create_task(STUDENT, TaskCreateRequest(title="x", status=TaskStatus.DONE, priority=TaskPriority.HIGH))

    summary = service.summarize(STUDENT, None)

    assert summary.model_dump(by_alias=True) == {
        "owner": "student",
        "total": 3,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1, "DONE": 1},
        "highPriorityOpen": 1,
    }


def test_task_request_defaults_and_validation() -> None:
    request = TaskCreateRequest(title="t")

    assert (request.status, request.priority, request.description) == (TaskStatus.TODO, TaskPriority.MEDIUM, "")
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="t", status="BOGUS")


# H-API-04
@pytest.mark.parametrize(
    ("raw_name", "expected"),
    [
        ("requirements.txt", "requirements.txt"),
        ("../../etc/passwd.txt", "passwd.txt"),
        ("C:\\Users\\me\\notes.md", "notes.md"),
        ("..hidden.txt", "hidden.txt"),
        ("a b&c.pdf", "a_b_c.pdf"),
    ],
)
def test_sanitize_filename(raw_name: str, expected: str) -> None:
    assert sanitize_filename(raw_name) == expected


@pytest.mark.parametrize("raw_name", [None, "", ".", "..", "x" * (MAX_FILENAME_LENGTH + 1)])
def test_sanitize_filename_rejects_invalid(raw_name: str | None) -> None:
    with pytest.raises(HTTPException) as error:
        sanitize_filename(raw_name)

    assert error.value.status_code == 400


@pytest.mark.parametrize("file_name", ["a.TXT", "b.md", "c.pdf"])
def test_validate_extension_accepts_allowed(file_name: str) -> None:
    validate_extension(file_name)


@pytest.mark.parametrize("file_name", ["a.exe", "b", "c.txt.sh", "d.html"])
def test_validate_extension_rejects_others(file_name: str) -> None:
    with pytest.raises(HTTPException) as error:
        validate_extension(file_name)

    assert error.value.status_code == 415


def test_read_with_limit_stops_after_limit() -> None:
    upload = UploadFile(file=io.BytesIO(b"x" * 10), filename="a.txt")

    assert asyncio.run(read_with_limit(upload, 10)) == b"x" * 10
    with pytest.raises(HTTPException) as error:
        asyncio.run(read_with_limit(UploadFile(file=io.BytesIO(b"x" * 11), filename="a.txt"), 10))

    assert error.value.status_code == 413


# H-API-09, H-API-11
def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ("WORKSHOP_DB_PATH", "WORKSHOP_UPLOAD_DIR", "AUTH_HEALTH_URL", "WORKSHOP_CORS_ORIGINS"):
        monkeypatch.delenv(variable, raising=False)

    settings = load_settings()

    assert settings.database_path == "./data/workshop.db"
    assert settings.auth_health_url == "http://localhost:8080/q/health"
    assert settings.cors_origins == ["http://localhost:4200", "http://127.0.0.1:4200"]


def test_parse_origins_ignores_blanks() -> None:
    assert parse_origins(" https://a.test , ,https://b.test") == ["https://a.test", "https://b.test"]


@pytest.mark.parametrize("url", ["ftp://host/health", "file:///etc/passwd", "localhost:8080"])
def test_health_url_requires_http_scheme(url: str) -> None:
    with pytest.raises(ValueError):
        validate_health_url(url)


# H-API-02 (formato legado, pendiente de acuerdo con auth)
def test_parse_legacy_token_rejects_wrong_shape() -> None:
    with pytest.raises(ValueError):
        parse_legacy_token(build_token().replace("=", ""), now=0)
    assert parse_legacy_token(build_token("ana", "TRAINER"), now=0).username == "ana"
