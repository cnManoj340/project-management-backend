from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

DB = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    payload = decode_access_token(token)
    try:
        user_id = int(payload.get("sub", ""))
    except ValueError:
        raise UnauthorizedError("Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedError("User no longer exists")
    if not user.is_active:
        raise ForbiddenError("This account has been deactivated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str):
    """Dependency factory: allow only users whose role name is in `roles`."""
    def checker(user: CurrentUser) -> User:
        if user.role.name not in roles:
            raise ForbiddenError("Your role is not allowed to perform this action")
        return user
    return checker


def require_permission(permission: str):
    """Dependency factory: allow only users whose role grants `permission` ('*' = all)."""
    def checker(user: CurrentUser) -> User:
        if not user.has_permission(permission):
            raise ForbiddenError(f"Missing permission: {permission}")
        return user
    return checker


AdminUser = Annotated[User, Depends(require_roles("admin"))]
