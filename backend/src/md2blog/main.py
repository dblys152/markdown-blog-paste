import uvicorn
from fastapi import FastAPI

from md2blog.modules.identity.presentation.router import router as identity_router
from md2blog.presentation.health import router as health_router
from md2blog.settings import get_settings
from md2blog.shared.presentation.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(identity_router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("md2blog.main:app", host="0.0.0.0", port=8000, reload=True)
