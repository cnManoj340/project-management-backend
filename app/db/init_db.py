"""Seed default roles and the first admin account."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import ADMIN, DEFAULT_ROLES
from app.core.security import hash_password
from app.models import Role, User

logger = logging.getLogger(__name__)


def seed_roles(db: Session) -> None:
    for name, cfg in DEFAULT_ROLES.items():
        if not db.scalar(select(Role).where(Role.name == name)):
            db.add(Role(name=name, description=cfg["description"], permissions=cfg["permissions"]))
    db.commit()


def seed_admin(db: Session) -> None:
    if db.scalar(select(User).where(User.email == settings.FIRST_ADMIN_EMAIL.lower())):
        return
    role = db.scalar(select(Role).where(Role.name == ADMIN))
    db.add(User(
        email=settings.FIRST_ADMIN_EMAIL.lower(),
        username=settings.FIRST_ADMIN_USERNAME,
        full_name="System Administrator",
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        role_id=role.id,
    ))
    db.commit()
    logger.info("Created first admin user %s", settings.FIRST_ADMIN_EMAIL)
