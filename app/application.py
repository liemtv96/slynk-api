from secrets import compare_digest

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import slynk
from app.config import settings

ORIGIN_SECRET_HEADER = "x-slynk-origin-secret"


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

    @application.middleware("http")
    async def require_cloudfront_origin_secret(request: Request, call_next):
        if not request.url.path.startswith("/lite"):
            return await call_next(request)

        expected_secret = settings.CLOUDFRONT_ORIGIN_SECRET
        if not expected_secret:
            return await call_next(request)

        provided_secret = request.headers.get(ORIGIN_SECRET_HEADER, "")
        if not compare_digest(provided_secret, expected_secret):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        return await call_next(request)

    application.include_router(slynk.router, prefix="/lite", tags=["Lite"])

    @application.get("/")
    def root():
        return {"status": "ok", "service": settings.PROJECT_NAME}

    return application


app = create_app()
