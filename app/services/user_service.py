from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, paginate
from app.core.permissions import ADMIN
from app.core.security import hash_password, verify_password
from app.exceptions import (BadRequestError, ConflictError, ForbiddenError, NotFoundError,
                            UnauthorizedError)
from app.models import Role, User
from app.models.enums import RoleName
from app.schemas.user import ProfileUpdate, UserCreate, UserUpdate
from app.services.activity_service import log_activity


def get_role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if not role:
        raise NotFoundError(f"Role '{name}' does not exist")
    return role


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


def _ensure_unique(db: Session, email: str | None, username: str | None, exclude_id: int | None = None):
    if email:
        q = select(User).where(User.email == email.lower())
        if exclude_id:
            q = q.where(User.id != exclude_id)
        if db.scalar(q):
            raise ConflictError("Email is already registered")
    if username:
        q = select(User).where(User.username == username)
        if exclude_id:
            q = q.where(User.id != exclude_id)
        if db.scalar(q):
            raise ConflictError("Username is already taken")


def create_user(db: Session, data: UserCreate, actor: User | None = None) -> User:
    _ensure_unique(db, data.email, data.username)
    role = get_role(db, data.role.value)
    user = User(
        email=data.email.lower(), username=data.username, full_name=data.full_name,
        hashed_password=hash_password(data.password), role_id=role.id, is_active=data.is_active,
    )
    db.add(user)
    db.flush()
    log_activity(db, actor.id if actor else user.id, "user", "created", user.id,
                 details={"username": user.username, "role": role.name})
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, identifier: str, password: str) -> User:
    user = db.scalar(select(User).where(
        or_(User.email == identifier.lower(), User.username == identifier)))
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email/username or password")
    if not user.is_active:
        raise ForbiddenError("This account has been deactivated")
    return user


def list_users(db: Session, params: PageParams, search: str | None, role: RoleName | None,
               is_active: bool | None):
    stmt = select(User)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(User.username.ilike(like), User.email.ilike(like),
                              User.full_name.ilike(like)))
    if role:
        stmt = stmt.join(Role, User.role_id == Role.id).where(Role.name == role.value)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    return paginate(db, stmt.order_by(User.id), params)


def update_user(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = get_user_or_404(db, user_id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    _ensure_unique(db, changes.get("email"), changes.get("username"), exclude_id=user.id)
    if "password" in changes:
        user.hashed_password = hash_password(changes.pop("password"))
    if "email" in changes:
        changes["email"] = changes["email"].lower()
    for k, v in changes.items():
        setattr(user, k, v)
    log_activity(db, actor.id, "user", "updated", user.id, details={"fields": list(changes)})
    db.commit()
    db.refresh(user)
    return user


def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    _ensure_unique(db, changes.get("email"), None, exclude_id=user.id)
    if "new_password" in changes:
        if not data.current_password or not verify_password(data.current_password, user.hashed_password):
            raise BadRequestError("Current password is incorrect")
        user.hashed_password = hash_password(changes.pop("new_password"))
    changes.pop("current_password", None)
    if "email" in changes:
        user.email = changes["email"].lower()
    if "full_name" in changes:
        user.full_name = changes["full_name"]
    log_activity(db, user.id, "user", "profile_updated", user.id)
    db.commit()
    db.refresh(user)
    return user


def set_status(db: Session, actor: User, user_id: int, is_active: bool) -> User:
    user = get_user_or_404(db, user_id)
    if user.id == actor.id and not is_active:
        raise BadRequestError("You cannot deactivate your own account")
    user.is_active = is_active
    log_activity(db, actor.id, "user", "activated" if is_active else "deactivated", user.id)
    db.commit()
    db.refresh(user)
    return user


def set_role(db: Session, actor: User, user_id: int, role_name: RoleName) -> User:
    user = get_user_or_404(db, user_id)
    if user.id == actor.id and role_name.value != ADMIN:
        raise BadRequestError("You cannot remove your own admin role")
    old = user.role.name
    user.role_id = get_role(db, role_name.value).id
    log_activity(db, actor.id, "user", "role_changed", user.id,
                 details={"from": old, "to": role_name.value})
    db.commit()
    db.refresh(user)
    return user


def update_role_permissions(db: Session, actor: User, role_id: int, permissions: list[str]) -> Role:
    role = db.get(Role, role_id)
    if not role:
        raise NotFoundError("Role not found")
    if role.name == ADMIN:
        raise BadRequestError("The admin role's permissions cannot be changed")
    role.permissions = sorted(set(permissions))
    log_activity(db, actor.id, "role", "permissions_updated", role.id,
                 details={"role": role.name, "permissions": role.permissions})
    db.commit()
    db.refresh(role)
    return role
