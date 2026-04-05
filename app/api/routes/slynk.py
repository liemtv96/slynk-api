from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.api.schemas.slynk import (
    CommunityAnalyticsOverviewResponse,
    CommunitySessionCompleteResponse,
    CommunitySessionCreateRequest,
    CommunitySessionResponse,
    CommunityShareResponse,
)
from app.services.slynk_sharing import CommunitySharingService

router = APIRouter()
service = CommunitySharingService()


def _first_present(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _infer_os(user_agent: str, platform_hint: str | None) -> str:
    platform = (platform_hint or "").lower()
    ua = user_agent.lower()

    if "android" in ua:
        return "Android"
    if "iphone" in ua or "ipad" in ua or "ios" in platform:
        return "iOS"
    if "mac" in platform or "mac os x" in ua or "macintosh" in ua:
        return "macOS"
    if "windows" in platform or "windows" in ua:
        return "Windows"
    if "linux" in platform or "linux" in ua:
        return "Linux"
    if "cros" in ua or "chrome os" in platform:
        return "ChromeOS"
    return "Unknown"


def _infer_browser(user_agent: str) -> str:
    ua = user_agent.lower()

    if "edg/" in ua:
        return "Edge"
    if "opr/" in ua or "opera" in ua:
        return "Opera"
    if "chrome/" in ua and "edg/" not in ua and "opr/" not in ua:
        return "Chrome"
    if "firefox/" in ua:
        return "Firefox"
    if "safari/" in ua and "chrome/" not in ua:
        return "Safari"
    return "Unknown"


def _infer_device(user_agent: str, mobile_hint: str | None, platform_hint: str | None) -> tuple[str, str]:
    ua = user_agent.lower()
    mobile = (mobile_hint or "").lower()
    platform = (platform_hint or "").lower()

    if mobile == "?1" or "mobile" in ua or "iphone" in ua or "android" in ua:
        return "mobile", "web_mobile"
    if "ipad" in ua or "tablet" in ua:
        return "tablet", "web_tablet"
    if "smart-tv" in ua or "smarttv" in ua or "tv" in platform:
        return "tv", "web_tv"
    if "bot" in ua or "crawler" in ua or "spider" in ua:
        return "bot", "automated"
    return "desktop", "web_desktop"


def _extract_client_ip(request: Request) -> tuple[str, str]:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip(), "x-forwarded-for"

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip(), "x-real-ip"

    if request.client and request.client.host:
        return request.client.host, "socket"

    return "unknown", "unknown"


def _build_client_context(request: Request) -> dict:
    client_ip, ip_source = _extract_client_ip(request)
    headers = request.headers
    user_agent = headers.get("user-agent")
    platform_hint = _first_present(headers.get("sec-ch-ua-platform"), headers.get("x-platform"))
    mobile_hint = headers.get("sec-ch-ua-mobile")
    os_name = _infer_os(user_agent or "", platform_hint)
    browser_name = _infer_browser(user_agent or "")
    device_type, client_type = _infer_device(user_agent or "", mobile_hint, platform_hint)
    return {
        "client_ip": client_ip,
        "ip_source": ip_source,
        "forwarded_for": headers.get("x-forwarded-for"),
        "real_ip": headers.get("x-real-ip"),
        "user_agent": user_agent,
        "referer": headers.get("referer"),
        "origin": headers.get("origin"),
        "request_id": headers.get("x-request-id"),
        "browser": browser_name,
        "os": os_name,
        "device_type": device_type,
        "client_type": client_type,
        "platform_hint": platform_hint,
        "mobile_hint": mobile_hint,
    }


@router.post("/sessions", response_model=CommunitySessionResponse, summary="Create upload session")
def create_session(payload: CommunitySessionCreateRequest, request: Request):
    client_context = _build_client_context(request)
    return service.create_session(payload, client_context=client_context)


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


@router.get("/analytics/overview", response_model=CommunityAnalyticsOverviewResponse, summary="Get analytics overview")
def get_analytics_overview(limit: int = Query(default=100, ge=1, le=500)):
    return service.get_analytics_overview(limit=limit)
