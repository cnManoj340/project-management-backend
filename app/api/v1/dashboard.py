from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.task import DashboardOut
from app.services.dashboard_service import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardOut, summary="Totals, status counts, completion %, recent activity")
def dashboard(db: DB, user: CurrentUser):
    return build_dashboard(db, user)
