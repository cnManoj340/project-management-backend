from typing import Literal

from fastapi import APIRouter, Depends, Response

from app.api.deps import DB, CurrentUser, require_permission
from app.core.pagination import PageParams, build_page
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.common import Page
from app.schemas.task import (ActivityOut, CommentCreate, CommentOut, TaskCreate, TaskOut,
                              TaskStatusUpdate, TaskUpdate)
from app.services import activity_service, task_service as ts

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskOut, status_code=201)
def create_task(data: TaskCreate, db: DB, user=Depends(require_permission("task:create"))):
    return ts.create_task(db, user, data)


@router.get("", response_model=Page[TaskOut], summary="List / search / filter / sort tasks")
def list_tasks(db: DB, user: CurrentUser, params: PageParams = Depends(),
               project_id: int | None = None, status: TaskStatus | None = None,
               priority: TaskPriority | None = None, assignee_id: int | None = None,
               search: str | None = None, overdue: bool | None = None,
               sort_by: Literal["created_at", "due_date"] = "created_at",
               order: Literal["asc", "desc"] = "desc"):
    items, total = ts.list_tasks(db, user, params, project_id=project_id, status=status,
                                 priority=priority, assignee_id=assignee_id, search=search,
                                 overdue=overdue, sort_by=sort_by, order=order)
    return build_page(TaskOut, items, total, params)


@router.get("/me", response_model=Page[TaskOut], summary="Tasks assigned to the logged-in user")
def my_tasks(db: DB, user: CurrentUser, params: PageParams = Depends(),
             status: TaskStatus | None = None, priority: TaskPriority | None = None,
             search: str | None = None,
             sort_by: Literal["created_at", "due_date"] = "due_date",
             order: Literal["asc", "desc"] = "asc"):
    items, total = ts.list_tasks(db, user, params, assignee_id=user.id, status=status,
                                 priority=priority, search=search, sort_by=sort_by, order=order)
    return build_page(TaskOut, items, total, params)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: DB, user: CurrentUser):
    return ts.get_task(db, user, task_id)


@router.patch("/{task_id}", response_model=TaskOut, summary="Update task (status, priority, assignee, ...)")
def update_task(task_id: int, data: TaskUpdate, db: DB, user: CurrentUser):
    return ts.update_task(db, user, task_id, data)


@router.patch("/{task_id}/status", response_model=TaskOut, summary="Shortcut: update only the status")
def update_status(task_id: int, data: TaskStatusUpdate, db: DB, user: CurrentUser):
    return ts.update_task(db, user, task_id, TaskUpdate(status=data.status))


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: DB, user=Depends(require_permission("task:delete"))):
    ts.delete_task(db, user, task_id)
    return Response(status_code=204)


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(task_id: int, data: CommentCreate, db: DB, user: CurrentUser):
    return ts.add_comment(db, user, task_id, data)


@router.get("/{task_id}/comments", response_model=Page[CommentOut])
def list_comments(task_id: int, db: DB, user: CurrentUser, params: PageParams = Depends()):
    items, total = ts.list_comments(db, user, task_id, params)
    return build_page(CommentOut, items, total, params)


@router.delete("/{task_id}/comments/{comment_id}", status_code=204)
def delete_comment(task_id: int, comment_id: int, db: DB, user: CurrentUser):
    ts.delete_comment(db, user, task_id, comment_id)
    return Response(status_code=204)


@router.get("/{task_id}/activity", response_model=Page[ActivityOut], summary="Task history")
def task_activity(task_id: int, db: DB, user: CurrentUser, params: PageParams = Depends()):
    ts.get_task(db, user, task_id)
    items, total = activity_service.list_activity(db, params, task_id=task_id)
    return build_page(ActivityOut, items, total, params)
