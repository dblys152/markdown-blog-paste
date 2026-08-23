import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from md2blog.modules.identity.presentation.router import router as identity_router
from md2blog.modules.workspace.presentation.router import router as workspace_router
from md2blog.modules.workspace.presentation.trash_router import router as workspace_trash_router
from md2blog.presentation.health import router as health_router
from md2blog.settings import Settings, get_settings
from md2blog.shared.presentation.exception_handlers import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(identity_router)
    app.include_router(workspace_router)
    app.include_router(workspace_trash_router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("md2blog.main:app", host="0.0.0.0", port=8000, reload=True)
