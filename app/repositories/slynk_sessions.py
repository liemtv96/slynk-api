from app.aws.dynamo import get_dynamo_resource
from app.config import settings


class CommunitySessionRepository:
    """Persistence operations for community upload sessions."""

    @staticmethod
    def _table():
        return get_dynamo_resource().Table(settings.DYNAMO_COMMUNITY_TABLE)

    def create(self, item: dict) -> None:
        self._table().put_item(Item=item)

    def get(self, token: str) -> dict | None:
        response = self._table().get_item(Key={"token": token})
        return response.get("Item")

    def set_status(self, token: str, status: str) -> None:
        self._table().update_item(
            Key={"token": token},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status},
        )

    def scan_expired_active(self, now_iso: str) -> list[dict]:
        from boto3.dynamodb.conditions import Attr

        response = self._table().scan(
            FilterExpression=Attr("status").eq("active") & Attr("expires_at").lte(now_iso),
        )
        return response.get("Items", [])

    def delete(self, token: str) -> None:
        self._table().delete_item(Key={"token": token})

    def consume_daily_ip_quota(self, *, ip_address: str, day_key: str, limit: int, ttl_epoch: int, now_iso: str) -> bool:
        from botocore.exceptions import ClientError

        quota_token = f"quota#{day_key}#{ip_address}"
        try:
            self._table().update_item(
                Key={"token": quota_token},
                UpdateExpression=(
                    "SET attempts = if_not_exists(attempts, :zero) + :one, "
                    "bucket_date = :day_key, "
                    "ip_address = :ip_address, "
                    "updated_at = :now_iso, "
                    "created_at = if_not_exists(created_at, :now_iso), "
                    "ttl_epoch = :ttl_epoch"
                ),
                ConditionExpression="attribute_not_exists(attempts) OR attempts < :limit",
                ExpressionAttributeValues={
                    ":zero": 0,
                    ":one": 1,
                    ":limit": limit,
                    ":day_key": day_key,
                    ":ip_address": ip_address,
                    ":now_iso": now_iso,
                    ":ttl_epoch": ttl_epoch,
                },
            )
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return False
            raise
