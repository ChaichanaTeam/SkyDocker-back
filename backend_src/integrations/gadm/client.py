from typing import Any

import httpx
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.validation import make_valid

from .constants import BASE_URL, TIMEOUT_SECONDS, file_name


class GADMDataClient:
    """Downloads country outlines from GADM."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT_SECONDS)

    async def __aenter__(self) -> "GADMDataClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.aclose()

    async def border(self, country_tag: str) -> tuple[str, MultiPolygon]:
        """URL of the source file and the country outline. ValueError when GADM has no usable outline."""
        response = await self._client.get(file_name(country_tag))

        if response.status_code == httpx.codes.NOT_FOUND:
            raise ValueError(f"GADM has no border for {country_tag}")

        response.raise_for_status()
        return str(response.url), _outline(response.json())


def _outline(collection: dict[str, Any]) -> MultiPolygon:
    features = collection.get("features") or []
    if len(features) != 1:
        raise ValueError(f"Expected one country outline, got {len(features)} features")

    geometry = shape(features[0]["geometry"])
    if not geometry.is_valid:
        geometry = make_valid(geometry)

    return _polygons(geometry)


def _polygons(geometry: Any) -> MultiPolygon:
    # make_valid can return a collection with lines next to the polygons, only the area counts
    if isinstance(geometry, Polygon):
        return MultiPolygon([geometry])
    if isinstance(geometry, MultiPolygon):
        return geometry

    polygons = [polygon for part in getattr(geometry, "geoms", []) for polygon in _polygons_of(part)]
    if not polygons:
        raise ValueError(f"Country outline is {geometry.geom_type}, not a polygon")

    return MultiPolygon(polygons)


def _polygons_of(geometry: Any) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    return []
