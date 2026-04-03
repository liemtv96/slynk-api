import os


class Settings:
    """Configuration values loaded from environment variables."""

    def __init__(self) -> None:
        # AWS
        self.AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-1")
        self.AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "xxxx")
        self.AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "xxxx")

        # General
        self.PROJECT_NAME: str = os.getenv("SLYNK_PROJECT_NAME", "Slynk Community API")
        self.ENV: str = os.getenv("SLYNK_ENV", "development")
        self.API_PREFIX: str = os.getenv("SLYNK_API_PREFIX", "/api/v1")
        self.CORS_ORIGINS: list[str] = [
            origin.strip()
            for origin in os.getenv("SLYNK_CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]

        # DynamoDB
        self.DYNAMO_PREFIX: str = os.getenv("SLYNK_DYNAMO_PREFIX", "slynk_")
        self.DYNAMO_COMMUNITY_TABLE: str = os.getenv("SLYNK_DYNAMO_COMMUNITY_TABLE", f"{self.DYNAMO_PREFIX}community_files")

        # S3
        self.S3_ENDPOINT_URL: str = os.getenv("SLYNK_S3_ENDPOINT_URL", "")
        self.S3_BUCKET: str = os.getenv("SLYNK_S3_BUCKET", "")
        self.S3_PREFIX: str = os.getenv("SLYNK_S3_PREFIX", "uploads/")
        self.PUBLIC_BASE_URL: str = os.getenv("SLYNK_PUBLIC_BASE_URL", "")
        self.MAX_PRESIGNED_URL_AGE: int = int(os.getenv("SLYNK_MAX_PRESIGNED_URL_AGE", "3600"))
        self.DEFAULT_FILE_TTL_HOURS: int = int(os.getenv("SLYNK_DEFAULT_FILE_TTL_HOURS", "8"))
        self.MAX_UPLOAD_BYTES: int = int(os.getenv("SLYNK_MAX_UPLOAD_BYTES", str(3 * 1024 * 1024 * 1024)))
        self.DAILY_IP_CREATE_LIMIT: int = int(os.getenv("SLYNK_DAILY_IP_CREATE_LIMIT", "5"))

        # SQS
        self.SQS_DELETE_QUEUE_URL: str = os.getenv("SLYNK_SQS_DELETE_QUEUE_URL", "")


settings = Settings()
