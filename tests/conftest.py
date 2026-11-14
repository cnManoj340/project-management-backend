import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.init_db import seed_admin, seed_roles
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
API = settings.API_V1_PREFIX


def _override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        seed_roles(db)
        seed_admin(db)
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)  # not used as a context manager -> startup seeding is skipped
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def login(client, identifier, password):
    r = client.post(f"{API}/auth/login/json", json={"identifier": identifier, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin(client):
    return login(client, settings.FIRST_ADMIN_EMAIL, settings.FIRST_ADMIN_PASSWORD)


def make_user(client, admin_headers, username, role):
    r = client.post(f"{API}/users", headers=admin_headers, json={
        "email": f"{username}@mail.com", "username": username, "full_name": username.title(),
        "password": "Passw0rd123", "role": role})
    assert r.status_code == 201, r.text
    return r.json()["id"], login(client, username, "Passw0rd123")


@pytest.fixture()
def pm(client, admin):
    return make_user(client, admin, "manager", "project_manager")


@pytest.fixture()
def member(client, admin):
    return make_user(client, admin, "member", "team_member")


@pytest.fixture()
def project(client, pm, member):
    pm_id, pm_h = pm
    member_id, _ = member
    r = client.post(f"{API}/projects", headers=pm_h,
                    json={"name": "Website Revamp", "member_ids": [member_id]})
    assert r.status_code == 201, r.text
    return r.json()
