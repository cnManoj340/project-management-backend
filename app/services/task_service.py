import enum
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.pagination import PageParams, paginate
from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models import Project, Task, TaskComment, User
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import CommentCreate, TaskCreate, TaskUpdate
from app.services import access
from app.services.activity_service import log_activity
from app.services.project_service import get_project_or_404

TASK_LOAD = (joinedload(Task.assignee), joinedload(Task.created_by))


def _val(v):
    if isinstance(v, enum.Enum):
        return v.value
    if isinstance(v, date):
        return v.isoformat()
    return v


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundError("Task not found")
    return task


def get_task(db: Session, actor: User, task_id: int) -> Task:
    task = get_task_or_404(db, task_id)
    access.ensure_can_view(actor, task.project)
    return task


def _validate_assignee(db: Session, project: Project, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    user = db.get(User, assignee_id)
    if not user:
        raise NotFoundError("Assignee not found")
    if not user.is_active:
        raise BadRequestError("Cannot assign a task to a deactivated user")
    if not any(m.user_id == assignee_id for m in project.members):
        raise BadRequestError("Assignee must be a member of the project")


def _validate_deadline(project: Project, due: date | None) -> None:
    if due is None:
        return
    if due < date.today():
        raise BadRequestError("Deadline cannot be in the past")
    if project.start_date and due < project.start_date:
        raise BadRequestError("Deadline cannot be before the project start date")
    if project.end_date and due > project.end_date:
        raise BadRequestError("Deadline cannot be after the project end date")


def create_task(db: Session, actor: User, data: TaskCreate) -> Task:
    project = get_project_or_404(db, data.project_id)
    if not access.can_manage_tasks(actor, project):
        raise ForbiddenError("Only an admin or a project manager of this project can create tasks")
    _validate_assignee(db, project, data.assignee_id)
    _validate_deadline(project, data.due_date)
    task = Task(
        title=data.title, description=data.description, project_id=project.id,
        assignee_id=data.assignee_id, priority=data.priority.value, status=data.status.value,
        due_date=data.due_date, created_by_id=actor.id, updated_by_id=actor.id,
    )
    db.add(task)
    db.flush()
    log_activity(db, actor.id, "task", "created", task.id, project_id=project.id, task_id=task.id,
                 details={"title": task.title, "assignee_id": task.assignee_id})
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, actor: User, task_id: int, data: TaskUpdate) -> Task:
    task = get_task_or_404(db, task_id)
    project = task.project
    access.ensure_can_view(actor, project)
    changes = data.model_dump(exclude_unset=True)
    for required in ("title", "status", "priority"):
        if required in changes and changes[required] is None:
            raise BadRequestError(f"{required} cannot be null")

    full_access = access.can_manage_tasks(actor, project) and actor.has_permission("task:update")
    status_only = (task.assignee_id == actor.id and actor.has_permission("task:update_status")
                   and set(changes) <= {"status"})
    if not (full_access or status_only):
        raise ForbiddenError(
            "You can only change the status of tasks assigned to you; "
            "other edits need a project manager or admin")

    if "assignee_id" in changes and changes["assignee_id"] != task.assignee_id:
        _validate_assignee(db, project, changes["assignee_id"])
    if "due_date" in changes and changes["due_date"] != task.due_date:
        _validate_deadline(project, changes["due_date"])

    diff = {}
    for field, raw in changes.items():
        old_v, new_v = _val(getattr(task, field)), _val(raw)
        if old_v != new_v:
            diff[field] = [old_v, new_v]
            setattr(task, field, raw if field == "due_date" else new_v)
    if not diff:
        return task
    task.updated_by_id = actor.id
    action = "status_changed" if set(diff) == {"status"} else "updated"
    log_activity(db, actor.id, "task", action, task.id, project_id=project.id, task_id=task.id,
                 details=diff)
    if "assignee_id" in diff:
        log_activity(db, actor.id, "task", "assigned", task.id, project_id=project.id,
                     task_id=task.id, details={"assignee_id": diff["assignee_id"][1]})
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, actor: User, task_id: int) -> None:
    task = get_task_or_404(db, task_id)
    if not access.can_manage_tasks(actor, task.project):
        raise ForbiddenError("Only an admin or a project manager of this project can delete tasks")
    log_activity(db, actor.id, "task", "deleted", task.id, project_id=task.project_id,
                 details={"title": task.title})
    db.delete(task)
    db.commit()


def list_tasks(db: Session, actor: User, params: PageParams, *, project_id: int | None = None,
               status: TaskStatus | None = None, priority: TaskPriority | None = None,
               assignee_id: int | None = None, search: str | None = None,
               overdue: bool | None = None, sort_by: str = "created_at", order: str = "desc"):
    stmt = select(Task)
    visible = access.visible_project_ids(actor)
    if visible is not None:
        stmt = stmt.where(Task.project_id.in_(visible))
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if status:
        stmt = stmt.where(Task.status == status.value)
    if priority:
        stmt = stmt.where(Task.priority == priority.value)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
    if overdue:
        stmt = stmt.where(Task.due_date < date.today(), Task.status != TaskStatus.COMPLETED.value)
    col = getattr(Task, sort_by)
    ordering = col.desc() if order == "desc" else col.asc()
    if sort_by == "due_date":
        ordering = ordering.nulls_last()
    return paginate(db, stmt.order_by(ordering, Task.id.desc()), params, options=TASK_LOAD)


# ---- comments -------------------------------------------------------------

def add_comment(db: Session, actor: User, task_id: int, data: CommentCreate) -> TaskComment:
    task = get_task(db, actor, task_id)
    if not actor.has_permission("comment:create"):
        raise ForbiddenError("You do not have permission to comment")
    comment = TaskComment(task_id=task.id, user_id=actor.id, content=data.content)
    db.add(comment)
    db.flush()
    log_activity(db, actor.id, "comment", "added", comment.id, project_id=task.project_id,
                 task_id=task.id)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, actor: User, task_id: int, params: PageParams):
    task = get_task(db, actor, task_id)
    stmt = select(TaskComment).where(TaskComment.task_id == task.id).order_by(TaskComment.id)
    return paginate(db, stmt, params)


def delete_comment(db: Session, actor: User, task_id: int, comment_id: int) -> None:
    task = get_task(db, actor, task_id)
    comment = db.get(TaskComment, comment_id)
    if not comment or comment.task_id != task.id:
        raise NotFoundError("Comment not found")
    if comment.user_id != actor.id and not access.is_admin(actor):
        raise ForbiddenError("You can only delete your own comments")
    log_activity(db, actor.id, "comment", "deleted", comment.id, project_id=task.project_id,
                 task_id=task.id)
    db.delete(comment)
    db.commit()
