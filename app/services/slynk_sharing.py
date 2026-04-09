from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import HTTPException

from app.api.schemas.slynk import (
    CommunityAnalyticsOverviewResponse,
    CommunityAnalyticsSessionResponse,
    CommunityFileResponse,
    CommunitySessionAnalyticsDashboardResponse,
    CommunitySessionCompleteResponse,
    CommunitySessionCreateRequest,
    CommunitySessionResponse,
    CommunityShareResponse,
    CommunityUploadPartResponse,
)
from app.config import settings
from app.repositories.slynk_sessions import CommunitySessionRepository
from app.repositories.slynk_statistics import CommunityStatisticsRepository
from app.storage.s3 import generate_download_url, generate_upload_url


class CommunitySharingService:
    """Core behavior for creating, activating, and reading share sessions."""

    def __init__(
        self,
        repository: CommunitySessionRepository | None = None,
        statistics: CommunityStatisticsRepository | None = None,
    ) -> None:
        self.repository = repository or CommunitySessionRepository()
        self.statistics = statistics or CommunityStatisticsRepository()

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

    def create_session(self, payload: CommunitySessionCreateRequest, client_context: dict) -> CommunitySessionResponse:
        if not payload.files:
            raise HTTPException(status_code=400, detail="At least one file is required")

        total_size = sum(file.size for file in payload.files)
        if total_size > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"Session exceeds max total size of {settings.MAX_UPLOAD_BYTES} bytes")

        created_at = self.utcnow()
        self._enforce_daily_ip_limit(client_ip=client_context["client_ip"], created_at=created_at)
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
            "client_ip": client_context["client_ip"],
            "analytics": {
                "client_ip": client_context["client_ip"],
                "ip_source": client_context.get("ip_source"),
                "forwarded_for": client_context.get("forwarded_for"),
                "real_ip": client_context.get("real_ip"),
                "user_agent": client_context.get("user_agent"),
                "browser": client_context.get("browser"),
                "os": client_context.get("os"),
                "device_type": client_context.get("device_type"),
                "client_type": client_context.get("client_type"),
                "platform_hint": client_context.get("platform_hint"),
                "mobile_hint": client_context.get("mobile_hint"),
                "referer": client_context.get("referer"),
                "origin": client_context.get("origin"),
                "request_id": client_context.get("request_id"),
                "created_date": created_at.date().isoformat(),
            },
            "files": files,
        }
        self.repository.create(item)
        self.statistics.increment_global(
            session_delta=1,
            bytes_delta=total_size,
            files_delta=len(files),
            now_iso=created_at.isoformat(),
        )
        self.statistics.upsert_session_snapshot(
            token=token,
            created_at=item["created_at"],
            expires_at=item["expires_at"],
            status=item["status"],
            total_size=total_size,
            share_url=self.build_share_url(token),
            analytics=item["analytics"],
            now_iso=created_at.isoformat(),
        )

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
        self.statistics.update_session_status(
            token=token,
            status="active",
            now_iso=self.utcnow().isoformat(),
        )
        self.statistics.increment_global(
            completed_delta=1,
            now_iso=self.utcnow().isoformat(),
        )
        return CommunitySessionCompleteResponse(
            token=token,
            share_url=self.build_share_url(token),
            expires_at=self._to_datetime(item["expires_at"]),
        )

    def get_share(self, token: str) -> CommunityShareResponse:
        item = self.get_share_or_404(token)
        analytics = item.get("analytics", {})
        now_iso = self.utcnow().isoformat()
        self.statistics.increment_global(visit_delta=1, now_iso=now_iso)
        if analytics.get("country"):
            self.statistics.increment_country(country=analytics["country"], delta=1, now_iso=now_iso)
        return self.normalize_item(item)

    def get_download_url(self, token: str, file_id: str) -> str:
        item = self.get_share_or_404(token)
        share = self.normalize_item(item)
        file_item = next((current for current in item["files"] if current["file_id"] == file_id), None)
        if not file_item:
            raise HTTPException(status_code=404, detail="File not found")
        self.statistics.increment_global(
            download_delta=1,
            bytes_delta=int(file_item["size"]),
            now_iso=self.utcnow().isoformat(),
        )
        return generate_download_url(storage_key=file_item["storage_key"], expires_at=share.expires_at)

    def get_analytics_overview(self, limit: int = 100) -> CommunityAnalyticsOverviewResponse:
        items = self.statistics.list_session_snapshots()
        ordered_items = sorted(items, key=lambda item: item.get("created_at", ""), reverse=True)
        recent_items = ordered_items[:limit]

        device_breakdown: dict[str, int] = {}
        os_breakdown: dict[str, int] = {}
        browser_breakdown: dict[str, int] = {}
        country_breakdown = self.statistics.list_country_counts()
        derived_country_breakdown: dict[str, int] = {}
        global_stats = self.statistics.get_global()

        pending_sessions = 0
        active_sessions = 0
        expired_sessions = 0

        for item in ordered_items:
            status = item.get("status", "unknown")
            if status == "pending":
                pending_sessions += 1
            elif status == "active":
                active_sessions += 1
            elif status in {"expired", "deleted", "queued_delete"}:
                expired_sessions += 1

            analytics = item.get("analytics", {})
            device_breakdown[analytics.get("device_type") or "unknown"] = (
                device_breakdown.get(analytics.get("device_type") or "unknown", 0) + 1
            )
            os_breakdown[analytics.get("os") or "Unknown"] = os_breakdown.get(analytics.get("os") or "Unknown", 0) + 1
            browser_breakdown[analytics.get("browser") or "Unknown"] = (
                browser_breakdown.get(analytics.get("browser") or "Unknown", 0) + 1
            )
            if analytics.get("country"):
                country = str(analytics["country"]).strip()
                if country:
                    derived_country_breakdown[country] = derived_country_breakdown.get(country, 0) + 1

        if derived_country_breakdown:
            merged_country_breakdown = dict(derived_country_breakdown)
            for country, count in country_breakdown.items():
                merged_country_breakdown[country] = max(merged_country_breakdown.get(country, 0), count)
            country_breakdown = merged_country_breakdown

        recent_sessions = [
            CommunityAnalyticsSessionResponse(
                token=item["token"],
                created_at=self._to_datetime(item["created_at"]),
                expires_at=self._to_datetime(item["expires_at"]),
                status=item.get("status", "unknown"),
                total_size=int(item["total_size"]),
                share_url=self.build_share_url(item["token"]),
                analytics=CommunitySessionAnalyticsDashboardResponse(
                    browser=item.get("analytics", {}).get("browser"),
                    os=item.get("analytics", {}).get("os"),
                    device_type=item.get("analytics", {}).get("device_type"),
                    client_type=item.get("analytics", {}).get("client_type"),
                    created_date=item.get("analytics", {}).get("created_date"),
                    country=item.get("analytics", {}).get("country"),
                    region=item.get("analytics", {}).get("region"),
                    city=item.get("analytics", {}).get("city"),
                    latitude=item.get("analytics", {}).get("latitude"),
                    longitude=item.get("analytics", {}).get("longitude"),
                ),
            )
            for item in recent_items
        ]

        return CommunityAnalyticsOverviewResponse(
            total_sessions=int(global_stats.get("total_sessions", len(ordered_items))),
            pending_sessions=pending_sessions,
            active_sessions=active_sessions,
            expired_sessions=expired_sessions,
            total_visits=int(global_stats.get("total_visits", 0)),
            total_downloads=int(global_stats.get("total_downloads", 0)),
            total_bytes_handled=int(global_stats.get("total_bytes_handled", 0)),
            total_files_handled=int(global_stats.get("total_files_handled", 0)),
            device_breakdown=device_breakdown,
            os_breakdown=os_breakdown,
            browser_breakdown=browser_breakdown,
            country_breakdown=country_breakdown,
            recent_sessions=recent_sessions,
        )
