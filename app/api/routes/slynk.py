from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.api.schemas.slynk import (
    CommunitySessionCompleteResponse,
    CommunitySessionCreateRequest,
    CommunitySessionResponse,
    CommunityShareResponse,
)
from app.services.slynk_sharing import CommunitySharingService

router = APIRouter()
service = CommunitySharingService()


def _extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


@router.post("/sessions", response_model=CommunitySessionResponse, summary="Create upload session")
def create_session(payload: CommunitySessionCreateRequest, request: Request):
    client_ip = _extract_client_ip(request)
    return service.create_session(payload, client_ip=client_ip)


@router.post("/sessions/{token}/complete", response_model=CommunitySessionCompleteResponse, summary="Complete upload session")
def complete_session(token: str):
    return service.complete_session(token)


@router.get("/shares/{token}", response_model=CommunityShareResponse, summary="Get public share metadata")
def get_share(token: str):
    return service.get_share(token)


@router.get("/shares/{token}/files/{file_id}/download", summary="Get public file download url")
def get_download(token: str, file_id: str, format: str | None = Query(default=None)):
    url = service.get_download_url(token=token, file_id=file_id)
    if format == "json":
        return {"url": url}
    return RedirectResponse(url=url, status_code=307)
