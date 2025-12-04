import os

class Settings:
    def __init__(self) -> None:
        self.PROJECT_NAME: str = os.getenv("SLYNK_PROJECT_NAME", "Slynk API")
        self.DATABASE_URL: str = os.getenv("SLYNK_DATABASE_URL", "sqlite:///./slynk.db")
        self.JWT_SECRET_KEY: str = os.getenv("SLYNK_JWT_SECRET_KEY", "CHANGE_ME_SUPER_SECRET")
        self.JWT_ALGORITHM: str = os.getenv("SLYNK_JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("SLYNK_TOKEN_MINUTES", "1440"))
        self.UPLOAD_DIR: str = os.getenv("SLYNK_UPLOAD_DIR", "./uploads")


settings = Settings()
