from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.public import PublicWidgetConfig, SubmissionRequest, SubmissionResponse
from app.services.submission import accept_submission, get_active_widget

router = APIRouter(tags=["public"])


@router.get("/public/v1/widgets/{public_id}/config", response_model=PublicWidgetConfig)
def public_config(public_id: str, request: Request, db: Session = Depends(get_db)):
    widget = get_active_widget(db, public_id)
    etag = f'"widget-{widget.public_id}-{widget.config_version}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    response = PublicWidgetConfig(id=widget.public_id, widget_type=widget.widget_type, title=widget.title, description=widget.description, form_fields=widget.form_fields, button_text=widget.button_text)
    return Response(content=response.model_dump_json(), media_type="application/json", headers={"Cache-Control": "public, max-age=300, must-revalidate", "ETag": etag})


@router.post("/public/v1/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit(public_request: SubmissionRequest, request: Request, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=64), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    submission, replayed = accept_submission(db, public_id=public_request.widget_id, fields=public_request.fields, honeypot=public_request.website, idempotency_key=idempotency_key, ip=ip, origin=request.headers.get("origin"))
    if submission is None:
        return SubmissionResponse(id="", status="accepted")
    return SubmissionResponse(id=submission.id, replayed=replayed)
