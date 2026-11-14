from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import DB, AdminUser, CurrentUser, require_permission
from app.core.pagination import PageParams, build_page
from app.models import Role
from app.models.enums import RoleName
from app.schemas.common import Page
from app.schemas.user import (ProfileUpdate, RoleOut, RolePermissionsUpdate, UserCreate, UserOut,
                              UserRoleUpdate, UserStatusUpdate, UserUpdate)
from app.services import user_service

router = APIRouter(tags=["Users & Roles"])


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: DB, _: CurrentUser):
    return db.scalars(select(Role).order_by(Role.id)).all()


@router.patch("/roles/{role_id}/permissions", response_model=RoleOut, summary="Admin: edit role permissions")
def update_permissions(role_id: int, data: RolePermissionsUpdate, db: DB, admin: AdminUser):
    return user_service.update_role_permissions(db, admin, role_id, data.permissions)


@router.post("/users", response_model=UserOut, status_code=201, summary="Admin: create a user with any role")
def create_user(data: UserCreate, db: DB, admin: AdminUser):
    return user_service.create_user(db, data, actor=admin)


@router.get("/users", response_model=Page[UserOut], summary="List users (Admin / Project Manager)")
def list_users(db: DB, _=Depends(require_permission("user:read")), params: PageParams = Depends(),
               search: str | None = None, role: RoleName | None = None,
               is_active: bool | None = None):
    items, total = user_service.list_users(db, params, search, role, is_active)
    return build_page(UserOut, items, total, params)


@router.get("/users/me", response_model=UserOut)
def get_me(user: CurrentUser):
    return user


@router.patch("/users/me", response_model=UserOut, summary="Update my own profile / password")
def update_me(data: ProfileUpdate, db: DB, user: CurrentUser):
    return user_service.update_profile(db, user, data)


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: DB, _=Depends(require_permission("user:read"))):
    return user_service.get_user_or_404(db, user_id)


@router.patch("/users/{user_id}", response_model=UserOut, summary="Admin: update any user")
def update_user(user_id: int, data: UserUpdate, db: DB, admin: AdminUser):
    return user_service.update_user(db, admin, user_id, data)


@router.patch("/users/{user_id}/status", response_model=UserOut, summary="Admin: activate / deactivate")
def set_status(user_id: int, data: UserStatusUpdate, db: DB, admin: AdminUser):
    return user_service.set_status(db, admin, user_id, data.is_active)


@router.patch("/users/{user_id}/role", response_model=UserOut, summary="Admin: assign role")
def set_role(user_id: int, data: UserRoleUpdate, db: DB, admin: AdminUser):
    return user_service.set_role(db, admin, user_id, data.role)
