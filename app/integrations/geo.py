from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeoResult:
    country: str
    city: str | None
    provider: str


class GeoProvider(Protocol):
    name: str

    def lookup(self, ip: str) -> GeoResult | None: ...


class NullGeoProvider:
    """Safe local default; replace with HTTP adapters only for manual development."""
    name = "disabled"

    def lookup(self, ip: str) -> GeoResult | None:
        return None


def resolve_geo(ip: str, providers: list[GeoProvider]) -> GeoResult | None:
    for provider in providers:
        try:
            result = provider.lookup(ip)
            if result:
                return result
        except Exception:
            # An enrichment dependency is never allowed to fail lead capture.
            continue
    return None
