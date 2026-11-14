from sqlalchemy import case, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, paginate
from app.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models import Project, ProjectMember, Task, User
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.project import (MemberStats, ProjectCreate, ProjectOut, ProjectStats,
                                 ProjectUpdate)
from app.schemas.user import UserBrief
from app.services import access
from app.services.activity_service import log_activity

DONE = TaskStatus.COMPLETED.value


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    return project


def _active_users(db: Session, ids: set[int]) -> list[User]:
    users = db.scalars(select(User).where(User.id.in_(ids))).all() if ids else []
    missing = ids - {u.id for u in users}
    if missing:
        raise NotFoundError(f"User(s) not found: {sorted(missing)}")
    inactive = [u.id for u in users if not u.is_active]
    if inactive:
        raise BadRequestError(f"Cannot add deactivated user(s): {inactive}")
    return list(users)


def progress_counts(db: Session, project_ids: list[int]) -> dict[int, tuple[int, int]]:
    if not project_ids:
        return {}
    rows = db.execute(
        select(Task.project_id, func.count(Task.id), func.sum(case((Task.status == DONE, 1), else_=0)))
        .where(Task.project_id.in_(project_ids)).group_by(Task.project_id)
    ).all()
    return {pid: (total, int(done or 0)) for pid, total, done in rows}


def to_out(project: Project, counts: dict[int, tuple[int, int]]) -> ProjectOut:
    total, done = counts.get(project.id, (0, 0))
    return ProjectOut(
        id=project.id, name=project.name, description=project.description,
        start_date=project.start_date, end_date=project.end_date,
        owner=UserBrief.model_validate(project.owner),
        members=[UserBrief.model_validate(m.user) for m in project.members],
        total_tasks=total, completed_tasks=done,
        progress=round(done / total * 100, 2) if total else 0.0,
        created_at=project.created_at, updated_at=project.updated_at,
    )


def serialize(db: Session, project: Project) -> ProjectOut:
    return to_out(project, progress_counts(db, [project.id]))


def create_project(db: Session, actor: User, data: ProjectCreate) -> Project:
    users = _active_users(db, set(data.member_ids) | {actor.id})
    project = Project(name=data.name, description=data.description, start_date=data.start_date,
                      end_date=data.end_date, owner_id=actor.id)
    project.members = [ProjectMember(user_id=u.id) for u in users]
    db.add(project)
    db.flush()
    log_activity(db, actor.id, "project", "created", project.id, project_id=project.id,
                 details={"name": project.name})
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, actor: User, project_id: int) -> Project:
    project = get_project_or_404(db, project_id)
    access.ensure_can_view(actor, project)
    return project


def list_projects(db: Session, actor: User, params: PageParams, search: str | None,
                  sort_by: str, order: str):
    stmt = select(Project)
    visible = access.visible_project_ids(actor)
    if visible is not None:
        stmt = stmt.where(Project.id.in_(visible))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Project.name.ilike(like), Project.description.ilike(like)))
    col = getattr(Project, sort_by)
    stmt = stmt.order_by(col.desc() if order == "desc" else col.asc(), Project.id)
    return paginate(db, stmt, params)


def update_project(db: Session, actor: User, project_id: int, data: ProjectUpdate) -> Project:
    project = get_project_or_404(db, project_id)
    if not access.can_manage_project(actor, project):
        raise ForbiddenError("Only an admin or the owning project manager can edit this project")
    changes = data.model_dump(exclude_unset=True)
    if changes.get("name", "x") is None:
        raise BadRequestError("name cannot be null")
    start = changes.get("start_date", project.start_date)
    end = changes.get("end_date", project.end_date)
    if start and end and end < start:
        raise BadRequestError("end_date cannot be before start_date")
    diff = {}
    for k, v in changes.items():
        old = getattr(project, k)
        if old != v:
            diff[k] = [str(old) if old is not None else None, str(v) if v is not None else None]
            setattr(project, k, v)
    if diff:
        log_activity(db, actor.id, "project", "updated", project.id, project_id=project.id,
                     details=diff)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, actor: User, project_id: int) -> None:
    project = get_project_or_404(db, project_id)
    if not access.can_manage_project(actor, project):
        raise ForbiddenError("Only an admin or the owning project manager can delete this project")
    log_activity(db, actor.id, "project", "deleted", project.id,
                 details={"name": project.name})
    db.delete(project)
    db.commit()


def add_member(db: Session, actor: User, project_id: int, user_id: int) -> Project:
    project = get_project_or_404(db, project_id)
    if not access.can_manage_project(actor, project):
        raise ForbiddenError("Only an admin or the owning project manager can manage members")
    if any(m.user_id == user_id for m in project.members):
        raise ConflictError("User is already a member of this project")
    _active_users(db, {user_id})
    project.members.append(ProjectMember(user_id=user_id))
    log_activity(db, actor.id, "project", "member_added", project.id, project_id=project.id,
                 details={"user_id": user_id})
    db.commit()
    db.refresh(project)
    return project


def remove_member(db: Session, actor: User, project_id: int, user_id: int) -> Project:
    project = get_project_or_404(db, project_id)
    if not access.can_manage_project(actor, project):
        raise ForbiddenError("Only an admin or the owning project manager can manage members")
    if user_id == project.owner_id:
        raise BadRequestError("The project owner cannot be removed")
    member = next((m for m in project.members if m.user_id == user_id), None)
    if not member:
        raise NotFoundError("User is not a member of this project")
    project.members.remove(member)
    # Their tasks in this project become unassigned
    db.execute(update(Task).where(Task.project_id == project.id, Task.assignee_id == user_id)
               .values(assignee_id=None))
    log_activity(db, actor.id, "project", "member_removed", project.id, project_id=project.id,
                 details={"user_id": user_id})
    db.commit()
    db.refresh(project)
    return project


def project_stats(db: Session, actor: User, project_id: int) -> ProjectStats:
    from datetime import date

    project = get_project(db, actor, project_id)
    by_status = {s.value: 0 for s in TaskStatus}
    for status_, n in db.execute(select(Task.status, func.count()).where(
            Task.project_id == project.id).group_by(Task.status)).all():
        by_status[status_] = n
    by_priority = {p.value: 0 for p in TaskPriority}
    for prio, n in db.execute(select(Task.priority, func.count()).where(
            Task.project_id == project.id).group_by(Task.priority)).all():
        by_priority[prio] = n
    total = sum(by_status.values())
    overdue = db.scalar(select(func.count()).where(
        Task.project_id == project.id, Task.due_date < date.today(), Task.status != DONE)) or 0

    per_user: dict[int, list[int]] = {}
    for uid, status_, n in db.execute(select(Task.assignee_id, Task.status, func.count()).where(
            Task.project_id == project.id, Task.assignee_id.is_not(None))
            .group_by(Task.assignee_id, Task.status)).all():
        row = per_user.setdefault(uid, [0, 0])
        row[0] += n
        if status_ == DONE:
            row[1] += n
    members = [
        MemberStats(user_id=m.user_id, username=m.user.username,
                    total_tasks=per_user.get(m.user_id, [0, 0])[0],
                    completed_tasks=per_user.get(m.user_id, [0, 0])[1])
        for m in project.members
    ]
    return ProjectStats(
        project_id=project.id, total_tasks=total, by_status=by_status, by_priority=by_priority,
        overdue_tasks=overdue, members=members,
        progress=round(by_status[DONE] / total * 100, 2) if total else 0.0,
    )
