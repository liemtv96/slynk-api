from dataclasses import dataclass
from ipaddress import ip_address

import geoip2.database
from geoip2.errors import AddressNotFoundError

from app.config import settings


class GeoLookupError(RuntimeError):
    pass


@dataclass
class GeoLookupResult:
    status: str
    payload: dict


class IpGeolocationService:
    def __init__(self) -> None:
        self.city_db_path = settings.GEOIP_CITY_DB_PATH
        self.country_db_path = settings.GEOIP_COUNTRY_DB_PATH
        if not self.city_db_path and not self.country_db_path:
            raise GeoLookupError("GeoIP database paths are not configured")

    @staticmethod
    def _is_public_ip(candidate: str) -> bool:
        parsed = ip_address(candidate)
        return parsed.is_global

    def lookup(self, candidate_ip: str) -> GeoLookupResult:
        try:
            if not self._is_public_ip(candidate_ip):
                return GeoLookupResult(status="skipped_non_public_ip", payload={})
        except ValueError as exc:
            raise GeoLookupError(f"Invalid IP address: {candidate_ip}") from exc

        city_result = self._lookup_city(candidate_ip)
        if city_result is not None:
            return city_result
        return self._lookup_country(candidate_ip)

    def _lookup_city(self, candidate_ip: str) -> GeoLookupResult | None:
        if not self.city_db_path:
            return None
        try:
            with geoip2.database.Reader(self.city_db_path) as reader:
                city = reader.city(candidate_ip)
        except FileNotFoundError as exc:
            raise GeoLookupError(f"City GeoIP database not found at {self.city_db_path}") from exc
        except AddressNotFoundError:
            return None
        except Exception as exc:  # pragma: no cover - defensive guard around third-party library
            raise GeoLookupError(f"City geo lookup failed: {exc}") from exc

        return GeoLookupResult(
            status="enriched",
            payload={
                "country": city.country.name,
                "region": city.subdivisions.most_specific.name,
                "city": city.city.name,
                "latitude": city.location.latitude,
                "longitude": city.location.longitude,
            },
        )

    def _lookup_country(self, candidate_ip: str) -> GeoLookupResult:
        if not self.country_db_path:
            return GeoLookupResult(status="not_found", payload={})
        try:
            with geoip2.database.Reader(self.country_db_path) as reader:
                country = reader.country(candidate_ip)
        except FileNotFoundError as exc:
            raise GeoLookupError(f"Country GeoIP database not found at {self.country_db_path}") from exc
        except AddressNotFoundError:
            return GeoLookupResult(status="not_found", payload={})
        except Exception as exc:  # pragma: no cover - defensive guard around third-party library
            raise GeoLookupError(f"Country geo lookup failed: {exc}") from exc

        return GeoLookupResult(
            status="enriched_country_only",
            payload={
                "country": country.country.name,
                "region": None,
                "city": None,
                "latitude": None,
                "longitude": None,
            },
        )
