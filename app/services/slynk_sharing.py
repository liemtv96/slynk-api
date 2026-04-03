from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import HTTPException

from app.api.schemas.slynk import (
    CommunityFileResponse,
    CommunitySessionCompleteResponse,
    CommunitySessionCreateRequest,
    CommunitySessionResponse,
    CommunityShareResponse,
    CommunityUploadPartResponse,
)
from app.config import settings
from app.repositories.slynk_sessions import CommunitySessionRepository
from app.storage.s3 import generate_download_url, generate_upload_url


class CommunitySharingService:
    """Core behavior for creating, activating, and reading share sessions."""

    def __init__(self, repository: CommunitySessionRepository | None = None) -> None:
        self.repository = repository or CommunitySessionRepository()

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def build_share_url(self, token: str) -> str:
        path = f"/share?token={token}"
        if settings.PUBLIC_BASE_URL:
            return f"{settings.PUBLIC_BASE_URL.rstrip('/')}{path}"
        return path

    def normalize_item(self, item: dict) -> CommunityShareResponse:
        expires_at = self._to_datetime(item["expires_at"])
        if expires_at <= self.utcnow():
            raise HTTPException(status_code=410, detail="Share expired")

        return CommunityShareResponse(
            token=item["token"],
            total_size=int(item["total_size"]),
            created_at=self._to_datetime(item["created_at"]),
            expires_at=expires_at,
            share_url=self.build_share_url(item["token"]),
            files=[
                CommunityFileResponse(
                    file_id=file_item["file_id"],
                    filename=file_item["filename"],
                    size=int(file_item["size"]),
                    content_type=file_item.get("content_type"),
                )
                for file_item in item["files"]
            ],
        )

    def get_share_or_404(self, token: str) -> dict:
        item = self.repository.get(token)
        if not item:
            raise HTTPException(status_code=404, detail="Share not found")
        if item.get("status") != "active":
            raise HTTPException(status_code=410, detail="Share expired")
        return item

    def _enforce_daily_ip_limit(self, client_ip: str, created_at: datetime) -> None:
        day_key = created_at.date().isoformat()
        expires_at = datetime.combine(created_at.date() + timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc)
        allowed = self.repository.consume_daily_ip_quota(
            ip_address=client_ip,
            day_key=day_key,
            limit=settings.DAILY_IP_CREATE_LIMIT,
            ttl_epoch=int(expires_at.timestamp()),
            now_iso=created_at.isoformat(),
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit reached for this IP address ({settings.DAILY_IP_CREATE_LIMIT} sessions/day)",
            )

    def create_session(self, payload: CommunitySessionCreateRequest, client_ip: str) -> CommunitySessionResponse:
        if not payload.files:
            raise HTTPException(status_code=400, detail="At least one file is required")

        total_size = sum(file.size for file in payload.files)
        if total_size > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"Session exceeds max total size of {settings.MAX_UPLOAD_BYTES} bytes")

        created_at = self.utcnow()
        self._enforce_daily_ip_limit(client_ip=client_ip, created_at=created_at)
        expires_at = created_at + timedelta(hours=settings.DEFAULT_FILE_TTL_HOURS)
        token = token_urlsafe(12)

        files = []
        response_files: list[CommunityUploadPartResponse] = []
        for requested in payload.files:
            file_id = str(uuid4())
            storage_key = f"{settings.S3_PREFIX}{token}/{file_id}/{requested.filename}"
            files.append(
                {
                    "file_id": file_id,
                    "filename": requested.filename,
                    "size": str(requested.size),
                    "content_type": requested.content_type,
                    "storage_key": storage_key,
                }
            )
            response_files.append(
                CommunityUploadPartResponse(
                    file_id=file_id,
                    filename=requested.filename,
                    size=requested.size,
                    content_type=requested.content_type,
                    upload_url=generate_upload_url(storage_key=storage_key, content_type=requested.content_type),
                )
            )

        item = {
            "token": token,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_epoch": int(expires_at.timestamp()),
            "status": "pending",
            "total_size": str(total_size),
            "files": files,
        }
        self.repository.create(item)

        return CommunitySessionResponse(
            token=token,
            total_size=total_size,
            expires_at=expires_at,
            share_url=self.build_share_url(token),
            files=response_files,
        )

    def complete_session(self, token: str) -> CommunitySessionCompleteResponse:
        item = self.repository.get(token)
        if not item:
            raise HTTPException(status_code=404, detail="Session not found")
        if item.get("status") == "expired":
            raise HTTPException(status_code=410, detail="Session expired")

        self.repository.set_status(token, "active")
        return CommunitySessionCompleteResponse(
            token=token,
            share_url=self.build_share_url(token),
            expires_at=self._to_datetime(item["expires_at"]),
        )

    def get_share(self, token: str) -> CommunityShareResponse:
        return self.normalize_item(self.get_share_or_404(token))

    def get_download_url(self, token: str, file_id: str) -> str:
        item = self.get_share_or_404(token)
        share = self.normalize_item(item)
        file_item = next((current for current in item["files"] if current["file_id"] == file_id), None)
        if not file_item:
            raise HTTPException(status_code=404, detail="File not found")
        return generate_download_url(storage_key=file_item["storage_key"], expires_at=share.expires_at)
