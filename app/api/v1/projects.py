from typing import Literal

from fastapi import APIRouter, Depends, Response

from app.api.deps import DB, CurrentUser, require_permission
from app.core.pagination import PageParams, build_page
from app.schemas.common import Page
from app.schemas.project import MemberAdd, ProjectCreate, ProjectOut, ProjectStats, ProjectUpdate
from app.schemas.task import ActivityOut
from app.services import activity_service, project_service as ps

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, db: DB, user=Depends(require_permission("project:create"))):
    return ps.serialize(db, ps.create_project(db, user, data))


@router.get("", response_model=Page[ProjectOut])
def list_projects(db: DB, user: CurrentUser, params: PageParams = Depends(), search: str | None = None,
                  sort_by: Literal["created_at", "name", "start_date", "end_date"] = "created_at",
                  order: Literal["asc", "desc"] = "desc"):
    items, total = ps.list_projects(db, user, params, search, sort_by, order)
    counts = ps.progress_counts(db, [p.id for p in items])
    out = [ps.to_out(p, counts) for p in items]
    return build_page(ProjectOut, out, total, params)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: DB, user: CurrentUser):
    return ps.serialize(db, ps.get_project(db, user, project_id))


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectUpdate, db: DB, user: CurrentUser):
    return ps.serialize(db, ps.update_project(db, user, project_id, data))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: DB, user=Depends(require_permission("project:delete"))):
    ps.delete_project(db, user, project_id)
    return Response(status_code=204)


@router.post("/{project_id}/members", response_model=ProjectOut, status_code=201)
def add_member(project_id: int, data: MemberAdd, db: DB, user: CurrentUser):
    return ps.serialize(db, ps.add_member(db, user, project_id, data.user_id))


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectOut)
def remove_member(project_id: int, user_id: int, db: DB, user: CurrentUser):
    return ps.serialize(db, ps.remove_member(db, user, project_id, user_id))


@router.get("/{project_id}/stats", response_model=ProjectStats, summary="Project-wise task statistics")
def stats(project_id: int, db: DB, user: CurrentUser):
    return ps.project_stats(db, user, project_id)


@router.get("/{project_id}/activity", response_model=Page[ActivityOut])
def project_activity(project_id: int, db: DB, user: CurrentUser, params: PageParams = Depends()):
    ps.get_project(db, user, project_id)
    items, total = activity_service.list_activity(db, params, project_id=project_id)
    return build_page(ActivityOut, items, total, params)
