import uuid
from datetime import datetime, timezone

import boto3
from fastapi import UploadFile

from app.config import settings


s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def save_upload_file(file: UploadFile, max_bytes: int | None = None) -> tuple[str, str, int]:
    file_id = str(uuid.uuid4())
    storage_key = f"{settings.S3_PREFIX}{file_id}/{file.filename}"

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if max_bytes and size > max_bytes:
        raise ValueError(f"File exceeds max upload size of {max_bytes} bytes")

    s3.upload_fileobj(file.file, settings.S3_BUCKET, storage_key)
    return file_id, storage_key, size


def generate_upload_url(storage_key: str, content_type: str | None = None, expires_in: int = 3600) -> str:
    params = {"Bucket": settings.S3_BUCKET, "Key": storage_key}
    if content_type:
        params["ContentType"] = content_type

    return s3.generate_presigned_url("put_object", Params=params, ExpiresIn=expires_in)


def delete_file(storage_key: str) -> None:
    s3.delete_object(Bucket=settings.S3_BUCKET, Key=storage_key)


def generate_download_url(storage_key: str, expires_at: datetime | None = None) -> str:
    ttl = settings.MAX_PRESIGNED_URL_AGE
    if expires_at:
        expires_at_utc = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
        ttl = min(ttl, int((expires_at_utc - datetime.now(timezone.utc)).total_seconds()))

    ttl = max(1, ttl)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": storage_key},
        ExpiresIn=ttl,
    )

