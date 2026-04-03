from functools import lru_cache

import boto3

from app.config import settings


@lru_cache
def get_dynamo_resource():
    return boto3.resource("dynamodb", region_name=settings.AWS_REGION)

