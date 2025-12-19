import os

class Settings:
    """Settings for Slynk backend
    Supports:
    - DB_ENGINE: sqlite | mysql | postgres | mongo | dynamodb
    - STORAGE_ENGINE: local | s3
    """

    def __init__(self) -> None:
        # AWS
        self.AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-1")
        self.AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "xxxx")
        self.AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "xxxx")

        # General
        self.PROJECT_NAME: str = os.getenv("SLYNK_PROJECT_NAME", "Slynk API")
        self.ENV: str = os.getenv("SLYNK_ENV", "development")
        self.API_PREFIX: str = os.getenv("SLYNK_API_PREFIX", "/api/v1")

        # Database engines
        self.DB_ENGINE: str = os.getenv("SLYNK_DB_ENGINE", "sqlite").lower()
        self.DATABASE_URL: str = os.getenv("SLYNK_DATABASE_URL", "sqlite:///./slynk.db")

        # Mongo
        self.MONGO_URI: str = os.getenv("SLYNK_MONGO_URI", "mongodb://localhost:27017")
        self.MONGO_DB: str = os.getenv("SLYNK_MONGO_DB", "slynk")

        # DynamoDB
        self.DYNAMO_PREFIX: str = os.getenv("SLYNK_DYNAMO_PREFIX", "slynk_")

        # Storage
        self.STORAGE_ENGINE: str = os.getenv("SLYNK_STORAGE_ENGINE", "local").lower()
        self.UPLOAD_DIR: str = os.getenv("SLYNK_UPLOAD_DIR", "./uploads")

        # S3
        self.S3_ENDPOINT_URL: str = os.getenv("SLYNK_S3_ENDPOINT_URL", "")
        self.S3_BUCKET: str = os.getenv("SLYNK_S3_BUCKET", "")
        self.S3_PREFIX: str = os.getenv("SLYNK_S3_PREFIX", "uploads/")
        self.PUBLIC_BASE_URL: str = os.getenv("SLYNK_PUBLIC_BASE_URL", "")
        self.MAX_PRESIGNED_URL_AGE: int = int(os.getenv("SLYNK_MAX_PRESIGNED_URL_AGE", "86400"))

        # Security / JWT
        self.JWT_SECRET_KEY: str = os.getenv("SLYNK_JWT_SECRET_KEY", "CHANGE_ME_SUPER_SECRET")
        self.JWT_ALGORITHM: str = os.getenv("SLYNK_JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("SLYNK_TOKEN_MINUTES", "1440"))


settings = Settings()
