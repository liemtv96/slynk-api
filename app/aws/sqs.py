import json
from functools import lru_cache

import boto3

from app.config import settings


@lru_cache
def get_sqs_client():
    return boto3.client("sqs", region_name=settings.AWS_REGION)


def enqueue_delete_job(payload: dict) -> None:
    if not settings.SQS_DELETE_QUEUE_URL:
        return

    get_sqs_client().send_message(
        QueueUrl=settings.SQS_DELETE_QUEUE_URL,
        MessageBody=json.dumps(payload),
    )

