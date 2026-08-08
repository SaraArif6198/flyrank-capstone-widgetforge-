from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, dashboard, public, widgets
from app.core.config import get_settings


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema changes are applied by the dedicated Alembic migration service.
    yield


app = FastAPI(title="WidgetForge API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().widget_origins, allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Idempotency-Key"])
app.include_router(auth.router)
app.include_router(widgets.router)
app.include_router(public.router)
app.include_router(dashboard.router)


@app.middleware("http")
async def limit_public_submission_size(request: Request, call_next):
    if request.url.path == "/public/v1/submissions":
        length = request.headers.get("content-length")
        if length and int(length) > get_settings().max_submission_bytes:
            return error_response(413, "payload_too_large", "Request body is too large")
    response = await call_next(request)
    if request.url.path == "/widget.v1.js":
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(item) for item in error["loc"] if item != "body"), "message": error["msg"]} for error in exc.errors()]
    return error_response(422, "validation_error", "Request validation failed", details)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    codes = {401: "unauthorized", 404: "not_found", 413: "payload_too_large", 422: "validation_error", 429: "rate_limited"}
    response = error_response(exc.status_code, codes.get(exc.status_code, "request_error"), str(exc.detail))
    if exc.headers:
        response.headers.update(exc.headers)
    return response


@app.exception_handler(404)
async def route_not_found(_: Request, __):
    return error_response(404, "not_found", "Route not found")


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok", "service": "widgetforge", "phase": "owner-path"}


app.mount("/", StaticFiles(directory="app/static", html=False), name="static")
