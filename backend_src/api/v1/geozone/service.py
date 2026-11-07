import math
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable, Iterator, Optional

import httpx
from shapely.geometry import mapping

from backend_src.api.exceptions import APIExceptions
from backend_src.db import Queries, AsyncDBSession
from backend_src.api.shared_schemas import Coordinate, GeoJson, GeoFeature
from backend_src.integrations.pansa import height_rule
from backend_src.models import ActivityTime, Country, GeoZone
from backend_src import sync
from .constants import FEET_PER_METRE, MAP_HEIGHT_MARGIN_M
from .activity import reachable, schedule_owner
from .elevation import ground_elevation
from .schema import (
    ActivityWindow, CountryResolve, FlightPoint, GeozonePointCollection, GeozoneProperties, MapArea, SupportedCountriesList,
)


async def geozone_bbox(area: MapArea, country: Country, db: AsyncDBSession):
    def ceiling_ft(zone: GeoZone) -> Optional[int]:
        return _map_ceiling_ft(zone, area.height_m)

    geozones = [
        gz for gz in await Queries.GeoZone.get_all_by_bbox(*area.unpack(), country.id, db)
        if reachable(gz.lower_limit_ft, ceiling_ft(gz))
    ]

    if len(geozones) == 0:
        raise APIExceptions.not_found("No zones in this region")

    return GeoJson(
        features=await _geozone_features(geozones, db, ceiling_ft)
    )


async def geozone_point(point: FlightPoint, country: Country, db: AsyncDBSession) -> GeozonePointCollection:
    try:
        ground = await ground_elevation(point.lon, point.lat, db)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise APIExceptions.bad_gateway(f"Ground elevation is unavailable: {exc}")

    if ground is None:
        raise APIExceptions.not_found("No ground elevation data for this point")

    max_altitude_ft = math.ceil((ground.metres + point.height_m) * FEET_PER_METRE)
    geozones = await Queries.GeoZone.get_all_at_point(point.lon, point.lat, max_altitude_ft, country.id, db)

    return GeozonePointCollection(
        features=await _geozone_features(geozones, db, lambda zone: max_altitude_ft),
        ground_elevation_m=round(ground.metres, 1),
        ground_elevation_source=ground.source,
        max_altitude_ft=max_altitude_ft,
    )


async def _geozone_features(
    geozones: list[GeoZone], db: AsyncDBSession, ceiling_ft: Callable[[GeoZone], Optional[int]],
) -> list[GeoFeature]:
    now = datetime.now(timezone.utc)
    owners = {schedule_owner(gz) for gz in geozones} - {None}
    windows: dict[int, list[ActivityTime]] = {}
    for window in await Queries.GeoZone.get_windows_ending_after(owners, now, db): # type: ignore
        windows.setdefault(window.geo_zone_id, []).append(window)

    return [
        GeoFeature(geometry=mapping(gz.zone_polygon), properties=_geozone_properties(gz, windows, now, ceiling_ft(gz)))
        for gz in geozones
    ]


def _map_ceiling_ft(zone: GeoZone, height_m: Optional[int]) -> Optional[int]:
    """Top of a flight over the highest ground of the zone, None where it cannot be told."""
    if height_m is None or zone.terrain_max_m is None:
        return None

    return math.ceil((zone.terrain_max_m + height_m + MAP_HEIGHT_MARGIN_M) * FEET_PER_METRE)


def _geozone_properties(
    zone: GeoZone, windows: dict[int, list[ActivityTime]], now: datetime, ceiling_ft: Optional[int],
) -> GeozoneProperties:
    owner = schedule_owner(zone)
    owned = windows.get(owner, []) if owner is not None else []
    zone_windows = [ActivityWindow.from_activity_time(window, zone) for window in owned]

    # a window reserved only above the drone does not restrict it
    zone_windows = [window for window in zone_windows if reachable(window.lower_limit_ft, ceiling_ft)]

    valid = (zone.valid_from is None or zone.valid_from <= now) and (zone.valid_to is None or zone.valid_to > now)
    scheduled_active = owner is None or any(window.starts_at <= now < window.ends_at for window in zone_windows)

    return GeozoneProperties.from_geozone(
        zone,
        windows=zone_windows,
        active_now=valid and scheduled_active,
        rule=height_rule(zone.type, zone.source_type, zone.tag, zone.description_en),
    )


@contextmanager
def _sync_errors_as_http() -> Iterator[None]:
    """Answers a failed sync with the HTTP error the admin endpoints have always returned."""
    try:
        yield
    except sync.NothingToSync as exc:
        raise APIExceptions.conflict(str(exc))
    except sync.NotPublished as exc:
        raise APIExceptions.not_found(str(exc))
    except sync.SyncError as exc:
        raise APIExceptions.bad_gateway(str(exc))


async def sync_catalog(db: AsyncDBSession) -> sync.CatalogSyncReport:
    with _sync_errors_as_http():
        return await sync.sync_catalog(db)


async def sync_activity(db: AsyncDBSession) -> sync.ActivitySyncReport:
    with _sync_errors_as_http():
        return await sync.sync_activity(db)


async def sync_terrain(db: AsyncDBSession) -> sync.TerrainSyncReport:
    with _sync_errors_as_http():
        return await sync.sync_terrain(db)


async def sync_border(country: Country, db: AsyncDBSession) -> sync.BorderSyncReport:
    with _sync_errors_as_http():
        return await sync.sync_border(country, db)


async def geozone_get_country(coordinates: Coordinate, db: AsyncDBSession) -> CountryResolve:
    country = await Queries.Country.get_by_coordinates(coordinates.lon, coordinates.lat, db)

    if country is None:
        raise APIExceptions.not_found("Point is outside every synced country border")

    return CountryResolve(country_tag=country.country_tag)


async def geozone_get_country_supported(db: AsyncDBSession):
    countries = await Queries.Country.get_supported_countries(db)

    if len(countries) == 0:
        raise APIExceptions.not_found("No supported countries")

    return SupportedCountriesList(countries=[c.country_tag for c in countries])
