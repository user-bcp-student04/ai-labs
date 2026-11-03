import logging
import re
from collections import Counter
from pathlib import Path, PurePosixPath

import urllib3
from fastapi import HTTPException, UploadFile

from app.constants import (
    ALLOWED_UPLOAD_EXTENSIONS,
    CLOSED_STATUSES,
    FILE_TOO_LARGE_DETAIL,
    FORBIDDEN_OWNER_DETAIL,
    HEALTH_BODY_MAX_CHARS,
    HEALTH_TIMEOUT_SECONDS,
    HEALTH_UNAVAILABLE_BODY,
    HEALTH_UNAVAILABLE_STATUS,
    INVALID_FILENAME_DETAIL,
    MAX_FILENAME_LENGTH,
    MAX_UPLOAD_BYTES,
    UNSUPPORTED_EXTENSION_DETAIL,
    UPLOAD_CHUNK_BYTES,
    TaskPriority,
)
from app.repository import TaskRecord, TaskRepository
from app.schemas import (
    BackendHealthResponse,
    Identity,
    RequirementUploadResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskSummaryResponse,
)

logger = logging.getLogger(__name__)

UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def resolve_owner(identity: Identity, requested_owner: str | None) -> str:
    if not requested_owner or requested_owner == identity.username:
        return identity.username
    raise HTTPException(status_code=403, detail=FORBIDDEN_OWNER_DETAIL)


def is_high_priority_open(task: TaskRecord) -> bool:
    return task.priority == TaskPriority.HIGH and task.status not in CLOSED_STATUSES


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(self, identity: Identity, requested_owner: str | None) -> list[TaskResponse]:
        owner = resolve_owner(identity, requested_owner)
        return [TaskResponse.model_validate(task) for task in self._repository.list_by_owner(owner)]

    def create_task(self, identity: Identity, request: TaskCreateRequest) -> TaskResponse:
        return TaskResponse.model_validate(self._repository.insert(identity.username, request))

    def summarize(self, identity: Identity, requested_owner: str | None) -> TaskSummaryResponse:
        owner = resolve_owner(identity, requested_owner)
        tasks = self._repository.list_by_owner(owner)
        return TaskSummaryResponse(
            owner=owner,
            total=len(tasks),
            by_status=dict(Counter(task.status for task in tasks)),
            high_priority_open=sum(1 for task in tasks if is_high_priority_open(task)),
        )


def sanitize_filename(raw_name: str | None) -> str:
    base_name = PurePosixPath((raw_name or "").replace("\\", "/")).name.lstrip(".")
    safe_name = UNSAFE_FILENAME_CHARS.sub("_", base_name)
    if not safe_name or len(safe_name) > MAX_FILENAME_LENGTH:
        raise HTTPException(status_code=400, detail=INVALID_FILENAME_DETAIL)
    return safe_name


def validate_extension(file_name: str) -> None:
    if PurePosixPath(file_name).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=415, detail=UNSUPPORTED_EXTENSION_DETAIL)


async def read_with_limit(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail=FILE_TOO_LARGE_DETAIL)
        chunks.append(chunk)
    return b"".join(chunks)


class RequirementUploadService:
    def __init__(self, upload_dir: Path) -> None:
        self._upload_dir = upload_dir

    async def store(self, identity: Identity, upload: UploadFile) -> RequirementUploadResponse:
        file_name = sanitize_filename(upload.filename)
        validate_extension(file_name)
        content = await read_with_limit(upload, MAX_UPLOAD_BYTES)
        (self._upload_dir / file_name).write_bytes(content)
        return RequirementUploadResponse(
            owner=identity.username, file_name=file_name, stored_at=file_name, size=len(content)
        )


class BackendHealthService:
    def __init__(self, health_url: str, http_pool: urllib3.PoolManager) -> None:
        self._health_url = health_url
        self._http_pool = http_pool

    def check(self, identity: Identity) -> BackendHealthResponse:
        try:
            response = self._http_pool.request("GET", self._health_url, timeout=HEALTH_TIMEOUT_SECONDS)
        except (urllib3.exceptions.HTTPError, OSError) as error:
            logger.warning("Backend health check failed: %s", error)
            return self._build_response(identity, HEALTH_UNAVAILABLE_STATUS, HEALTH_UNAVAILABLE_BODY)
        body = response.data.decode("utf-8", errors="replace")[:HEALTH_BODY_MAX_CHARS]
        return self._build_response(identity, response.status, body)

    @staticmethod
    def _build_response(identity: Identity, status: int, body: str) -> BackendHealthResponse:
        return BackendHealthResponse(requested_by=identity.username, status=status, body=body)
