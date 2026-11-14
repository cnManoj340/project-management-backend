from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, paginate
from app.models import ActivityLog


def log_activity(
    db: Session, user_id: int | None, entity_type: str, action: str,
    entity_id: int | None = None, *, project_id: int | None = None,
    task_id: int | None = None, details: dict | None = None,
) -> None:
    """Adds a log row to the session; the caller commits (keeps it atomic with the change)."""
    db.add(ActivityLog(
        user_id=user_id, entity_type=entity_type, entity_id=entity_id, action=action,
        project_id=project_id, task_id=task_id, details=details,
    ))


def list_activity(db: Session, params: PageParams, *, project_id: int | None = None,
                  task_id: int | None = None):
    stmt = select(ActivityLog)
    if project_id is not None:
        stmt = stmt.where(ActivityLog.project_id == project_id)
    if task_id is not None:
        stmt = stmt.where(ActivityLog.task_id == task_id)
    return paginate(db, stmt.order_by(ActivityLog.id.desc()), params)
