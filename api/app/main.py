from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_settings
from app.constants import CORS_ALLOWED_HEADERS, CORS_ALLOWED_METHODS
from app.repository import TaskRepository
from app.routes import router
from app.services import BackendHealthService, RequirementUploadService, TaskService


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    settings = load_settings(db_path, upload_dir)
    repository = TaskRepository(settings.database_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        repository.initialize_schema()
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title="Workshop Requirements API", version="0.1.0", lifespan=lifespan)
    app.state.task_service = TaskService(repository)
    app.state.upload_service = RequirementUploadService(settings.upload_dir)
    app.state.health_service = BackendHealthService(settings.auth_health_url, urllib3.PoolManager())
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
    )
    app.include_router(router)
    return app


app = create_app()
