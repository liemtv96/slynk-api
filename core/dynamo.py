from app.aws.dynamo import get_dynamo_resource
from app.config import settings


def table_name(logical: str) -> str:
    return f"{settings.DYNAMO_PREFIX}{logical}"


__all__ = ["get_dynamo_resource", "table_name"]
