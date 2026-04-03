import json
from datetime import datetime, timezone

from app.aws.sqs import enqueue_delete_job
from app.repositories.slynk_sessions import CommunitySessionRepository
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
