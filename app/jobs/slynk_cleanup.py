import json
from datetime import datetime, timedelta, timezone

from app.aws.sqs import enqueue_delete_job
from app.config import settings
from app.repositories.slynk_sessions import CommunitySessionRepository
from app.repositories.slynk_statistics import CommunityStatisticsRepository
from app.services.ip_geolocation import GeoLookupError, IpGeolocationService
from app.storage import delete_file


def enqueue_expired_sessions_handler(event, context):
    repository = CommunitySessionRepository()
    statistics = CommunityStatisticsRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    stale_pending_cutoff_iso = (
        datetime.now(timezone.utc) - timedelta(hours=settings.PENDING_SESSION_STALE_HOURS)
    ).isoformat()
    items = repository.scan_expired_active(now_iso)
    items.extend(repository.scan_stale_pending(stale_pending_cutoff_iso))

    seen_tokens: set[str] = set()
    deduped_items: list[dict] = []
    for item in items:
        token = item["token"]
        if token in seen_tokens:
            continue
        seen_tokens.add(token)
        deduped_items.append(item)

    for item in deduped_items:
        repository.set_status(item["token"], "queued_delete")
        statistics.update_session_status(token=item["token"], status="queued_delete", now_iso=now_iso)
        enqueue_delete_job(
            {
                "token": item["token"],
                "storage_keys": [file_item["storage_key"] for file_item in item.get("files", [])],
            }
        )

    return {"enqueued": len(deduped_items)}


def process_delete_queue_handler(event, context):
    repository = CommunitySessionRepository()
    statistics = CommunityStatisticsRepository()
    processed = 0

    for record in event.get("Records", []):
        payload = json.loads(record["body"])
        for storage_key in payload.get("storage_keys", []):
            delete_file(storage_key)
        statistics.update_session_status(
            token=payload["token"],
            status="deleted",
            now_iso=datetime.now(timezone.utc).isoformat(),
        )
        repository.delete(payload["token"])
        processed += 1

    return {"processed": processed}


def enrich_session_geolocation_handler(event, context):
    if not settings.GEO_ENRICH_ENABLED:
        return {"enabled": False, "processed": 0, "enriched": 0, "skipped": 0, "failed": 0}

    repository = CommunitySessionRepository()
    statistics = CommunityStatisticsRepository()
    geolocation = IpGeolocationService()
    now_iso = datetime.now(timezone.utc).isoformat()

    items = repository.list_geo_enrichment_candidates(limit=settings.GEO_ENRICH_BATCH_SIZE)

    enriched = 0
    skipped = 0
    failed = 0

    for item in items:
        analytics = dict(item.get("analytics", {}))
        analytics["geo_attempted_at"] = now_iso

        try:
            result = geolocation.lookup(item["client_ip"])
        except GeoLookupError as exc:
            analytics["geo_status"] = "lookup_error"
            analytics["geo_error"] = str(exc)
            repository.update_analytics(item["token"], analytics)
            failed += 1
            continue

        analytics.pop("geo_error", None)
        analytics["geo_status"] = result.status
        analytics["geo_provider"] = settings.GEO_LOOKUP_PROVIDER
        analytics["geo_enriched_at"] = now_iso
        analytics.update(result.payload)

        repository.update_analytics(item["token"], analytics)
        statistics.update_session_analytics(token=item["token"], analytics=analytics, now_iso=now_iso)

        if result.status == "enriched":
            enriched += 1
        elif result.status == "skipped_non_public_ip":
            skipped += 1
        else:
            failed += 1

    return {
        "enabled": True,
        "processed": len(items),
        "enriched": enriched,
        "skipped": skipped,
        "failed": failed,
    }
