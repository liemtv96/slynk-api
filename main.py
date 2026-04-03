from app.application import app
from app.config import Settings


def root():
    return {"status": "ok", "service": Settings().PROJECT_NAME}
