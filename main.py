from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import Base, engine
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

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(user.router, prefix="/api/v1/user", tags=["User"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(shares.router, prefix="/api/v1/shares", tags=["Shares"])
app.include_router(reverse.router, prefix="/api/v1/reverse", tags=["Reverse Shares"])


@app.get("/")
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME}
