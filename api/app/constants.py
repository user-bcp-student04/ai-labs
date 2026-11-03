from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


CLOSED_STATUSES = frozenset({TaskStatus.DONE, TaskStatus.ARCHIVED})

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000

BEARER_PREFIX = "Bearer "
INVALID_TOKEN_DETAIL = "Invalid or expired token"
FORBIDDEN_OWNER_DETAIL = "Access to another owner's data is not allowed"

DEFAULT_DATABASE_PATH = "./data/workshop.db"
DEFAULT_UPLOAD_DIR = "./uploads"
DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"
DEFAULT_CORS_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
ALLOWED_HEALTH_URL_SCHEMES = frozenset({"http", "https"})
CORS_ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOWED_HEADERS = ["Authorization", "Content-Type"]

HEALTH_TIMEOUT_SECONDS = 3.0
HEALTH_BODY_MAX_CHARS = 1000
HEALTH_UNAVAILABLE_BODY = "Backend unavailable"
HEALTH_UNAVAILABLE_STATUS = 0

ALLOWED_UPLOAD_EXTENSIONS = frozenset({".txt", ".md", ".pdf"})
MAX_UPLOAD_BYTES = 1024 * 1024
UPLOAD_CHUNK_BYTES = 64 * 1024
MAX_FILENAME_LENGTH = 100
INVALID_FILENAME_DETAIL = "Invalid file name"
UNSUPPORTED_EXTENSION_DETAIL = "File extension not allowed"
FILE_TOO_LARGE_DETAIL = "File exceeds the maximum allowed size"
