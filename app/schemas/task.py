from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.user import UserBrief


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    project_id: int
    assignee_id: int | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: date | None = None


class TaskUpdate(BaseModel):
    """All fields optional (PATCH). Send assignee_id/due_date as null to clear them."""
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    assignee_id: int | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: date | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    project_id: int
    assignee_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
    assignee: UserBrief | None
    created_by: UserBrief | None
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: int
    content: str
    user: UserBrief | None
    created_at: datetime


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user: UserBrief | None
    project_id: int | None
    task_id: int | None
    entity_type: str
    entity_id: int | None
    action: str
    details: dict | None
    created_at: datetime


class DashboardOut(BaseModel):
    total_projects: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int  # status = todo
    in_progress_tasks: int
    review_tasks: int
    overdue_tasks: int
    completion_percentage: float
    tasks_by_priority: dict[str, int]
    my_open_tasks: int
    recent_activities: list[ActivityOut]
