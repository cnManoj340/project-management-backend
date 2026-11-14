import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import api_router
from app.core.config import settings
from app.core.docs_theme import DOCS_CSS, SWAGGER_PARAMS
from app.core.logging import setup_logging
from app.db.init_db import seed_admin, seed_roles
from app.db.session import SessionLocal
from app.exceptions import register_exception_handlers

setup_logging()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with SessionLocal() as db:
            seed_roles(db)
            seed_admin(db)
    except SQLAlchemyError:
        logger.exception("Database not ready. Did you run `alembic upgrade head`?")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="REST API for project, task and team management with JWT auth and RBAC.",
        lifespan=lifespan,
        docs_url=None,  # replaced by the custom themed page below
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, ms)
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    @app.get("/docs", include_in_schema=False)
    def custom_docs():
        page = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.PROJECT_NAME} - API Docs",
            swagger_ui_parameters=SWAGGER_PARAMS,
        ).body.decode("utf-8")
        return HTMLResponse(page.replace("</head>", f"<style>{DOCS_CSS}</style></head>"))

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/docs")

    return app


app = create_app()
