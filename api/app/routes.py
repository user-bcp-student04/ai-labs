from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from app.schemas import (
    BackendHealthResponse,
    Identity,
    RequirementUploadResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskSummaryResponse,
)
from app.security import legacy_identity
from app.services import BackendHealthService, RequirementUploadService, TaskService

router = APIRouter(prefix="/api")


def get_task_service(request: Request) -> TaskService:
    return request.app.state.task_service


def get_upload_service(request: Request) -> RequirementUploadService:
    return request.app.state.upload_service


def get_health_service(request: Request) -> BackendHealthService:
    return request.app.state.health_service


CurrentIdentity = Annotated[Identity, Depends(legacy_identity)]
Tasks = Annotated[TaskService, Depends(get_task_service)]
Uploads = Annotated[RequirementUploadService, Depends(get_upload_service)]
Health = Annotated[BackendHealthService, Depends(get_health_service)]


@router.get("/tasks")
def list_tasks(
    identity: CurrentIdentity, service: Tasks, owner: str | None = Query(default=None)
) -> list[TaskResponse]:
    return service.list_tasks(identity, owner)


@router.post("/tasks", status_code=201)
def create_task(identity: CurrentIdentity, service: Tasks, payload: TaskCreateRequest) -> TaskResponse:
    return service.create_task(identity, payload)


@router.get("/summary")
def summary(
    identity: CurrentIdentity, service: Tasks, owner: str | None = Query(default=None)
) -> TaskSummaryResponse:
    return service.summarize(identity, owner)


@router.post("/requirements", status_code=201)
async def upload_requirement(
    identity: CurrentIdentity, service: Uploads, file: UploadFile = File(...)
) -> RequirementUploadResponse:
    return await service.store(identity, file)


@router.get("/backend-health")
def backend_health(identity: CurrentIdentity, service: Health) -> BackendHealthResponse:
    return service.check(identity)
