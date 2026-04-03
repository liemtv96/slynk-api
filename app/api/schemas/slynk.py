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

