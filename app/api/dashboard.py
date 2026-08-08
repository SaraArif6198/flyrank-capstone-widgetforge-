from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, get_current_user
from app.db.models import Submission, Widget
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummary, SubmissionListItem

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/submissions", response_model=list[SubmissionListItem])
def list_submissions(
    widget_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = select(Submission).where(Submission.tenant_id == user.tenant_id)
    if widget_id:
        statement = statement.where(Submission.widget_id == widget_id)
    return list(db.scalars(statement.order_by(Submission.created_at.desc()).limit(limit)))


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Submission).where(Submission.tenant_id == user.tenant_id)) or 0
    by_widget_rows = db.execute(
        select(Widget.id, Widget.title, func.count(Submission.id).label("count"))
        .outerjoin(Submission, Submission.widget_id == Widget.id)
        .where(Widget.tenant_id == user.tenant_id)
        .group_by(Widget.id, Widget.title)
        .order_by(func.count(Submission.id).desc())
    ).all()
    by_country_rows = db.execute(
        select(Submission.geo_country, func.count(Submission.id).label("count"))
        .where(Submission.tenant_id == user.tenant_id)
        .group_by(Submission.geo_country)
        .order_by(func.count(Submission.id).desc())
    ).all()
    return DashboardSummary(
        total_submissions=total,
        by_widget=[{"widget_id": row.id, "title": row.title, "count": row.count} for row in by_widget_rows],
        by_country=[{"country": row.geo_country or "Unknown", "count": row.count} for row in by_country_rows],
    )
