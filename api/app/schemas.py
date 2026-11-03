from pydantic import BaseModel, ConfigDict, Field

from app.constants import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, TaskPriority, TaskStatus


class AliasedModel(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, from_attributes=True)


class Identity(BaseModel):
    username: str
    role: str


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskResponse(AliasedModel):
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str = Field(alias="createdAt")


class TaskSummaryResponse(AliasedModel):
    owner: str
    total: int
    by_status: dict[str, int] = Field(alias="byStatus")
    high_priority_open: int = Field(alias="highPriorityOpen")


class RequirementUploadResponse(AliasedModel):
    owner: str
    file_name: str = Field(alias="fileName")
    stored_at: str = Field(alias="storedAt")
    size: int


class BackendHealthResponse(AliasedModel):
    requested_by: str = Field(alias="requestedBy")
    status: int
    body: str
