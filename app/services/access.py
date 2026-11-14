"""Object-level access rules shared by the services."""
from sqlalchemy import select

from app.core.permissions import ADMIN, PROJECT_MANAGER
from app.exceptions import ForbiddenError
from app.models import Project, ProjectMember, User


def is_admin(user: User) -> bool:
    return user.role.name == ADMIN


def is_member(user: User, project: Project) -> bool:
    return any(m.user_id == user.id for m in project.members)


def can_view_project(user: User, project: Project) -> bool:
    return is_admin(user) or is_member(user, project)


def can_manage_project(user: User, project: Project) -> bool:
    """Admin, or the project manager that owns the project."""
    return is_admin(user) or (user.role.name == PROJECT_MANAGER and project.owner_id == user.id)


def can_manage_tasks(user: User, project: Project) -> bool:
    """Admin, or a project manager who is a member of the project."""
    return is_admin(user) or (user.role.name == PROJECT_MANAGER and is_member(user, project))


def ensure_can_view(user: User, project: Project) -> None:
    if not can_view_project(user, project):
        raise ForbiddenError("You are not a member of this project")


def visible_project_ids(user: User):
    """Subquery of project ids the user may see, or None when unrestricted (admin)."""
    if is_admin(user):
        return None
    return select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
