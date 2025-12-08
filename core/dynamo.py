from functools import lru_cache

import boto3

from .config import settings


@lru_cache
def get_dynamo_resource():
    return boto3.resource("dynamodb", region_name=settings.AWS_REGION)


def table_name(logical: str) -> str:
    return f"{settings.DYNAMO_PREFIX}{logical}"
