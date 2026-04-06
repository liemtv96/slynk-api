from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import slynk
from app.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Minimal serverless lite backend for temporary file sharing.",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(slynk.router, prefix="/lite", tags=["Lite"])

    @application.get("/")
    def root():
        return {"status": "ok", "service": settings.PROJECT_NAME}

    return application


app = create_app()
