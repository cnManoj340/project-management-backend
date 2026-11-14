from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.user import UserBrief


class ProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def _dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class ProjectCreate(ProjectBase):
    member_ids: list[int] = []


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class MemberAdd(BaseModel):
    user_id: int


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    owner: UserBrief
    members: list[UserBrief]
    total_tasks: int
    completed_tasks: int
    progress: float
    created_at: datetime
    updated_at: datetime


class MemberStats(BaseModel):
    user_id: int
    username: str
    total_tasks: int
    completed_tasks: int


class ProjectStats(BaseModel):
    project_id: int
    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue_tasks: int
    progress: float
    members: list[MemberStats]
