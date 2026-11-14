from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DB, CurrentUser
from app.core.security import create_access_token
from app.models.enums import RoleName
from app.schemas.user import LoginRequest, RegisterRequest, Token, UserCreate, UserOut
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _token(user) -> Token:
    return Token(access_token=create_access_token(user.id, user.role.name),
                 user=UserOut.model_validate(user))


@router.post("/register", response_model=UserOut, status_code=201,
             summary="Self-register (always creates a Team Member)")
def register(data: RegisterRequest, db: DB):
    return user_service.create_user(db, UserCreate(**data.model_dump(), role=RoleName.TEAM_MEMBER))


@router.post("/login", response_model=Token, summary="Login (OAuth2 form: username = email or username)")
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    return _token(user_service.authenticate(db, form.username, form.password))


@router.post("/login/json", response_model=Token, summary="Login with a JSON body")
def login_json(data: LoginRequest, db: DB):
    return _token(user_service.authenticate(db, data.identifier, data.password))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
