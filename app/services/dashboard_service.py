from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ActivityLog, Project, Task, User
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import ActivityOut, DashboardOut
from app.services import access


def build_dashboard(db: Session, user: User) -> DashboardOut:
    visible = access.visible_project_ids(user)
    task_scope = [] if visible is None else [Task.project_id.in_(visible)]
    project_q = select(func.count(Project.id))
    if visible is not None:
        project_q = project_q.where(Project.id.in_(visible))

    counts = {s.value: 0 for s in TaskStatus}
    for st, n in db.execute(select(Task.status, func.count()).where(*task_scope)
                            .group_by(Task.status)).all():
        counts[st] = n
    by_priority = {p.value: 0 for p in TaskPriority}
    for pr, n in db.execute(select(Task.priority, func.count()).where(*task_scope)
                            .group_by(Task.priority)).all():
        by_priority[pr] = n
    total = sum(counts.values())
    done = TaskStatus.COMPLETED.value
    overdue = db.scalar(select(func.count()).where(
        *task_scope, Task.due_date < date.today(), Task.status != done)) or 0
    mine = db.scalar(select(func.count()).where(
        Task.assignee_id == user.id, Task.status != done)) or 0

    log_q = select(ActivityLog).order_by(ActivityLog.id.desc()).limit(10)
    if visible is not None:
        log_q = log_q.where(ActivityLog.project_id.in_(visible))
    logs = db.scalars(log_q).unique().all()

    return DashboardOut(
        total_projects=db.scalar(project_q) or 0,
        total_tasks=total,
        completed_tasks=counts[done],
        pending_tasks=counts[TaskStatus.TODO.value],
        in_progress_tasks=counts[TaskStatus.IN_PROGRESS.value],
        review_tasks=counts[TaskStatus.REVIEW.value],
        overdue_tasks=overdue,
        completion_percentage=round(counts[done] / total * 100, 2) if total else 0.0,
        tasks_by_priority=by_priority,
        my_open_tasks=mine,
        recent_activities=[ActivityOut.model_validate(l) for l in logs],
    )
