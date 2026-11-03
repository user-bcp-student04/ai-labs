import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from app.schemas import TaskCreateRequest

CREATE_TASKS_TABLE = (
    "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
    "description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, "
    "created_at TEXT NOT NULL)"
)
COUNT_TASKS = "SELECT COUNT(*) AS total FROM tasks"
INSERT_TASK = (
    "INSERT INTO tasks(title,description,status,owner,priority,created_at) "
    "VALUES (?,?,?,?,?,datetime('now'))"
)
TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"
SELECT_TASKS_BY_OWNER = f"SELECT {TASK_COLUMNS} FROM tasks WHERE owner=? ORDER BY id"
SELECT_TASK_BY_ID = f"SELECT {TASK_COLUMNS} FROM tasks WHERE id=?"

SEED_TASKS = [
    ("Refactor login", "Separar responsabilidades en frontend", "TODO", "student", "HIGH"),
    ("Review API", "Revisar seguridad de endpoints", "IN_PROGRESS", "student", "MEDIUM"),
    ("Trainer notes", "Preparar retrospectiva", "TODO", "trainer", "LOW"),
]


@dataclass(frozen=True)
class TaskRecord:
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str


class TaskRepository:
    """Único lugar con SQL; cada operación usa su propia conexión (apta para hilos)."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path

    def initialize_schema(self) -> None:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(CREATE_TASKS_TABLE)
            if connection.execute(COUNT_TASKS).fetchone()["total"] == 0:
                connection.executemany(INSERT_TASK, SEED_TASKS)

    def list_by_owner(self, owner: str) -> list[TaskRecord]:
        with self._connection() as connection:
            rows = connection.execute(SELECT_TASKS_BY_OWNER, (owner,)).fetchall()
        return [_to_record(row) for row in rows]

    def insert(self, owner: str, request: TaskCreateRequest) -> TaskRecord:
        parameters = (request.title, request.description, request.status.value, owner, request.priority.value)
        with self._connection() as connection:
            cursor = connection.execute(INSERT_TASK, parameters)
            row = connection.execute(SELECT_TASK_BY_ID, (cursor.lastrowid,)).fetchone()
        return _to_record(row)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()


def _to_record(row: sqlite3.Row) -> TaskRecord:
    return TaskRecord(**{column: row[column] for column in row.keys()})
