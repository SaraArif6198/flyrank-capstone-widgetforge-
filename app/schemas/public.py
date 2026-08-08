from typing import Any
from pydantic import BaseModel, Field


class SubmissionRequest(BaseModel):
    widget_id: str = Field(min_length=36, max_length=36)
    fields: dict[str, Any] = Field(min_length=1, max_length=8)
    website: str = Field(default="", max_length=200)


class SubmissionResponse(BaseModel):
    id: str
    status: str = "accepted"
    replayed: bool = False


class PublicWidgetConfig(BaseModel):
    id: str
    widget_type: str
    title: str
    description: str | None
    form_fields: list[dict]
    button_text: str
