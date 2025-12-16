import uuid
from fastapi import UploadFile
import boto3
from core.config import settings
from datetime import datetime

s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
    file_id = str(uuid.uuid4())
    storage_key = f"{settings.S3_PREFIX}{file_id}/{file.filename}"

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    s3.upload_fileobj(
        file.file,
        settings.S3_BUCKET,
        storage_key,
    )

    return file_id, storage_key, size


def delete_file(storage_key: str):
    s3.delete_object(
        Bucket=settings.S3_BUCKET,
        Key=storage_key,
    )


def generate_download_url(storage_key: str, expires_at=None) -> str:
    ttl = settings.MAX_PRESIGNED_URL_AGE
    if expires_at:
        ttl = min(
            ttl,
            int((expires_at - datetime.utcnow()).total_seconds())
        )

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": storage_key,
        },
        ExpiresIn=ttl,
    )