from datetime import datetime

from pydantic import BaseModel, Field


class CommunityFileRequest(BaseModel):
    filename: str
    size: int = Field(gt=0)
    content_type: str | None = None


class CommunitySessionCreateRequest(BaseModel):
    files: list[CommunityFileRequest]


class CommunityUploadPartResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    content_type: str | None = None
    upload_url: str


class CommunitySessionResponse(BaseModel):
    token: str
    total_size: int
    expires_at: datetime
    share_url: str
    files: list[CommunityUploadPartResponse]


class CommunitySessionCompleteResponse(BaseModel):
    token: str
    share_url: str
    expires_at: datetime


class CommunityFileResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    content_type: str | None = None


class CommunityShareResponse(BaseModel):
    token: str
    total_size: int
    created_at: datetime
    expires_at: datetime
    share_url: str
    files: list[CommunityFileResponse]


class CommunitySessionAnalyticsDashboardResponse(BaseModel):
    browser: str | None = None
    os: str | None = None
    device_type: str | None = None
    client_type: str | None = None
    created_date: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CommunityAnalyticsSessionResponse(BaseModel):
    token: str
    created_at: datetime
    expires_at: datetime
    status: str
    total_size: int
    share_url: str
    analytics: CommunitySessionAnalyticsDashboardResponse


class CommunityAnalyticsOverviewResponse(BaseModel):
    total_sessions: int
    pending_sessions: int
    active_sessions: int
    expired_sessions: int
    total_visits: int
    total_downloads: int
    total_bytes_handled: int
    total_files_handled: int
    device_breakdown: dict[str, int]
    os_breakdown: dict[str, int]
    browser_breakdown: dict[str, int]
    country_breakdown: dict[str, int]
    recent_sessions: list[CommunityAnalyticsSessionResponse]
