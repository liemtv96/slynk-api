from decimal import Decimal

from app.aws.dynamo import get_dynamo_resource
from app.config import settings
from app.repositories.dynamo_types import to_dynamo_value


class CommunityStatisticsRepository:
    """Durable aggregate statistics for sessions, traffic, and geo breakdowns."""

    GLOBAL_KEY = "stats#global"
    SESSION_PREFIX = "session#"

    @staticmethod
    def _table():
        return get_dynamo_resource().Table(settings.DYNAMO_STATISTICS_TABLE)

    @staticmethod
    def _number(value) -> int | float:
        if isinstance(value, Decimal):
            return int(value) if value % 1 == 0 else float(value)
        return value

    def increment_global(
        self,
        *,
        session_delta: int = 0,
        completed_delta: int = 0,
        visit_delta: int = 0,
        download_delta: int = 0,
        bytes_delta: int = 0,
        files_delta: int = 0,
        now_iso: str,
    ) -> None:
        self._table().update_item(
            Key={"stat_key": self.GLOBAL_KEY},
            UpdateExpression=(
                "SET updated_at = :now_iso, "
                "total_sessions = if_not_exists(total_sessions, :zero) + :session_delta, "
                "completed_sessions = if_not_exists(completed_sessions, :zero) + :completed_delta, "
                "total_visits = if_not_exists(total_visits, :zero) + :visit_delta, "
                "total_downloads = if_not_exists(total_downloads, :zero) + :download_delta, "
                "total_bytes_handled = if_not_exists(total_bytes_handled, :zero) + :bytes_delta, "
                "total_files_handled = if_not_exists(total_files_handled, :zero) + :files_delta"
            ),
            ExpressionAttributeValues={
                ":zero": 0,
                ":session_delta": session_delta,
                ":completed_delta": completed_delta,
                ":visit_delta": visit_delta,
                ":download_delta": download_delta,
                ":bytes_delta": bytes_delta,
                ":files_delta": files_delta,
                ":now_iso": now_iso,
            },
        )

    def increment_country(self, *, country: str, delta: int, now_iso: str) -> None:
        normalized_country = (country or "Unknown").strip() or "Unknown"
        key = f"country#{normalized_country}"
        self._table().update_item(
            Key={"stat_key": key},
            UpdateExpression=(
                "SET country = :country, updated_at = :now_iso, "
                "visits = if_not_exists(visits, :zero) + :delta"
            ),
            ExpressionAttributeValues={
                ":country": normalized_country,
                ":now_iso": now_iso,
                ":zero": 0,
                ":delta": delta,
            },
        )

    def get_global(self) -> dict:
        response = self._table().get_item(Key={"stat_key": self.GLOBAL_KEY})
        item = response.get("Item") or {}
        return {key: self._number(value) for key, value in item.items()}

    @staticmethod
    def _session_key(token: str) -> str:
        return f"{CommunityStatisticsRepository.SESSION_PREFIX}{token}"

    def upsert_session_snapshot(
        self,
        *,
        token: str,
        created_at: str,
        expires_at: str,
        status: str,
        total_size: int,
        share_url: str,
        analytics: dict,
        now_iso: str,
    ) -> None:
        item = {
            "stat_key": self._session_key(token),
            "token": token,
            "created_at": created_at,
            "expires_at": expires_at,
            "status": status,
            "total_size": total_size,
            "share_url": share_url,
            "analytics": analytics,
            "updated_at": now_iso,
        }
        self._table().put_item(Item=to_dynamo_value(item))

    def update_session_status(self, *, token: str, status: str, now_iso: str) -> None:
        self._table().update_item(
            Key={"stat_key": self._session_key(token)},
            UpdateExpression="SET #status = :status, updated_at = :now_iso",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status, ":now_iso": now_iso},
        )

    def update_session_analytics(self, *, token: str, analytics: dict, now_iso: str) -> None:
        self._table().update_item(
            Key={"stat_key": self._session_key(token)},
            UpdateExpression="SET analytics = :analytics, updated_at = :now_iso",
            ExpressionAttributeValues={":analytics": to_dynamo_value(analytics), ":now_iso": now_iso},
        )

    def list_session_snapshots(self) -> list[dict]:
        items: list[dict] = []
        scan_kwargs: dict = {}

        while True:
            response = self._table().scan(**scan_kwargs)
            for item in response.get("Items", []):
                stat_key = str(item.get("stat_key", ""))
                if stat_key.startswith(self.SESSION_PREFIX):
                    items.append({key: self._number(value) for key, value in item.items()})

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        return items

    def list_country_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        scan_kwargs: dict = {}

        while True:
            response = self._table().scan(**scan_kwargs)
            for item in response.get("Items", []):
                stat_key = str(item.get("stat_key", ""))
                if not stat_key.startswith("country#"):
                    continue
                country = str(item.get("country") or stat_key.removeprefix("country#"))
                counts[country] = int(self._number(item.get("visits", 0)) or 0)

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        return counts
