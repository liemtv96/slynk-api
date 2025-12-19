from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database_sql import Base, engine
from core.config import settings
from routers import auth, user, shares, reverse, files

# Create all tables on startup (simple for local SQLite usage)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="SQLite-based backend for Slynk file sharing (Direct shares, Reverse shares, Account & Settings).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix=settings.API_PREFIX)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(shares.router, prefix="/shares", tags=["Shares"])
api_router.include_router(reverse.router, prefix="/reverse", tags=["Reverse Shares"])

app.include_router(api_router)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME}
