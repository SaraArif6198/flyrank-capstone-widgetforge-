from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SubmissionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    widget_id: str
    payload: dict[str, Any]
    geo_country: str | None
    geo_city: str | None
    geo_provider: str | None
    created_at: datetime


class DashboardSummary(BaseModel):
    total_submissions: int
    by_widget: list[dict[str, Any]]
    by_country: list[dict[str, Any]]
    submissions_over_time: list[dict[str, Any]]
