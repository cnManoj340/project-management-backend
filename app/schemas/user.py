import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleName


def _check_password(v: str) -> str:
    if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValueError("Password must contain at least one letter and one digit")
    return v


Password = Annotated[str, Field(min_length=8, max_length=72), AfterValidator(_check_password)]
Username = Annotated[str, Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")]
FullName = Annotated[str, Field(min_length=1, max_length=120)]


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None = None
    permissions: list[str]


class RolePermissionsUpdate(BaseModel):
    permissions: list[str]


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    email: str


class UserOut(UserBrief):
    is_active: bool
    role: RoleOut
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    username: Username
    full_name: FullName
    password: Password


class UserCreate(RegisterRequest):
    role: RoleName = RoleName.TEAM_MEMBER
    is_active: bool = True


class UserUpdate(BaseModel):
    """Admin update of any user."""
    email: EmailStr | None = None
    username: Username | None = None
    full_name: FullName | None = None
    password: Password | None = None


class ProfileUpdate(BaseModel):
    """Self-service profile update."""
    email: EmailStr | None = None
    full_name: FullName | None = None
    current_password: str | None = None
    new_password: Password | None = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: RoleName


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    identifier: str = Field(description="Email or username")
    password: str
