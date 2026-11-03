import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.constants import (
    ALLOWED_HEALTH_URL_SCHEMES,
    DEFAULT_AUTH_HEALTH_URL,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_DATABASE_PATH,
    DEFAULT_UPLOAD_DIR,
)


@dataclass(frozen=True)
class Settings:
    database_path: str
    upload_dir: Path
    auth_health_url: str
    cors_origins: list[str]


def parse_origins(raw_origins: str) -> list[str]:
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def validate_health_url(url: str) -> str:
    if urlparse(url).scheme not in ALLOWED_HEALTH_URL_SCHEMES:
        raise ValueError("AUTH_HEALTH_URL must use http or https")
    return url


def load_settings(db_path: str | None = None, upload_dir: str | None = None) -> Settings:
    return Settings(
        database_path=db_path or os.getenv("WORKSHOP_DB_PATH", DEFAULT_DATABASE_PATH),
        upload_dir=Path(upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", DEFAULT_UPLOAD_DIR)),
        auth_health_url=validate_health_url(os.getenv("AUTH_HEALTH_URL", DEFAULT_AUTH_HEALTH_URL)),
        cors_origins=parse_origins(os.getenv("WORKSHOP_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)),
    )
