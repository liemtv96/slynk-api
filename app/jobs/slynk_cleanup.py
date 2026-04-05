import json
from datetime import datetime, timezone

from app.aws.sqs import enqueue_delete_job
from app.config import settings
from app.repositories.slynk_sessions import CommunitySessionRepository
from app.services.ip_geolocation import GeoLookupError, IpGeolocationService
from app.storage import delete_file


def enqueue_expired_sessions_handler(event, context):
    repository = CommunitySessionRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    items = repository.scan_expired_active(now_iso)

    for item in items:
        repository.set_status(item["token"], "queued_delete")
        enqueue_delete_job(
            {
                "token": item["token"],
                "storage_keys": [file_item["storage_key"] for file_item in item.get("files", [])],
            }
        )

    return {"enqueued": len(items)}


def process_delete_queue_handler(event, context):
    repository = CommunitySessionRepository()
    processed = 0

    for record in event.get("Records", []):
        payload = json.loads(record["body"])
        for storage_key in payload.get("storage_keys", []):
            delete_file(storage_key)
        repository.delete(payload["token"])
        processed += 1

    return {"processed": processed}


def enrich_session_geolocation_handler(event, context):
    if not settings.GEO_ENRICH_ENABLED:
        return {"enabled": False, "processed": 0, "enriched": 0, "skipped": 0, "failed": 0}

    repository = CommunitySessionRepository()
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
        analytics["geo_provider"] = settings.GEO_LOOKUP_BASE_URL
        analytics["geo_enriched_at"] = now_iso
        analytics.update(result.payload)

        repository.update_analytics(item["token"], analytics)

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
