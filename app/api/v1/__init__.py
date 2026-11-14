from fastapi import APIRouter

from app.api.v1 import auth, dashboard, projects, tasks, users

api_router = APIRouter()
for module in (auth, users, projects, tasks, dashboard):
    api_router.include_router(module.router)
