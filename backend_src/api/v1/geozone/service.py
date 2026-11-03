import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, NamedTuple, Optional
from uuid import UUID

import httpx
from loguru import logger
from shapely.geometry import Polygon, mapping, shape
from sqlalchemy import Row, delete, update

from backend_src.api.exceptions import APIExceptions
from backend_src.db import Queries, AsyncDBSession
from backend_src.api.shared_schemas import GeoJson, GeoFeature
from backend_src.integrations.copernicus import ATTRIBUTION as DEM_ATTRIBUTION, CopernicusDemClient, TileCell
from backend_src.integrations.pansa import (
    Activation, DroneMapClient, Notam, Zone, classify, current_notams, height_rule, notam_windows,
)
from backend_src.models import ActivityTime, Country, GeoZone, GeoZoneActivityMode, GeoZoneActivitySource
from .constants import (
    ACTIVITY_HORIZON_DAYS,
    DEFAULT_COUNTRY_NAME,
    DEFAULT_COUNTRY_TAG,
    FEET_PER_METRE,
    MAP_HEIGHT_MARGIN_M,
    MAX_REPORTED_ERRORS,
    MIN_ZONES_RATIO,
    PANSA_SNAPSHOT_DIR,
)
from .activity import reachable, schedule_owner
from .elevation import ground_elevation
from .schema import (
    ActivitySyncReport, ActivityWindow, CatalogSyncReport, FlightPoint, GeozonePointCollection, GeozoneProperties,
    MapArea, TerrainSyncReport,
)


# Fields that make a stored zone outdated even if PANSA did not touch it, e.g. after classifier changes
_COMPARED_FIELDS = ("type", "source_type", "activity_mode", "source_modified_at")


async def geozone_bbox(area: MapArea, db: AsyncDBSession):
    def ceiling_ft(zone: GeoZone) -> Optional[int]:
        return _map_ceiling_ft(zone, area.height_m)

    geozones = [
        gz for gz in await Queries.GeoZone.get_all_by_bbox(*area.unpack(), db)
        if reachable(gz.lower_limit_ft, ceiling_ft(gz))
    ]

    if len(geozones) == 0:
        raise APIExceptions.not_found("No zones in this region")

    return GeoJson(
        features=await _geozone_features(geozones, db, ceiling_ft)
    )


async def geozone_point(point: FlightPoint, db: AsyncDBSession) -> GeozonePointCollection:
    try:
        ground = await ground_elevation(point.lon, point.lat, db)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise APIExceptions.bad_gateway(f"Ground elevation is unavailable: {exc}")

    if ground is None:
        raise APIExceptions.not_found("No ground elevation data for this point")

    max_altitude_ft = math.ceil((ground.metres + point.height_m) * FEET_PER_METRE)
    geozones = await Queries.GeoZone.get_all_at_point(point.lon, point.lat, max_altitude_ft, db)

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
    for window in await Queries.GeoZone.get_windows_ending_after(owners, now, db):
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


async def sync_catalog(db: AsyncDBSession) -> CatalogSyncReport:
    zones = await _fetch_zones()
    country = await _resolve_country(db)
    stored = {row.external_id: row for row in await Queries.GeoZone.get_sync_states(country.id, db)}

    incoming = {zone.uid: zone for zone in zones}
    if not incoming or len(incoming) < len(stored) * MIN_ZONES_RATIO:
        raise APIExceptions.bad_gateway(
            f"PANSA returned {len(incoming)} zones while {len(stored)} are stored, sync aborted"
        )

    removed = [row.id for uid, row in stored.items() if uid not in incoming]
    if removed:
        await db.execute(delete(GeoZone).where(GeoZone.id.in_(removed)))

    now = datetime.now(timezone.utc)
    inserts: list[GeoZone] = []
    updates: list[dict[str, Any]] = []
    errors: list[str] = []
    unchanged = 0

    for zone in incoming.values():
        try:
            values = _zone_values(zone)
        except ValueError as exc:
            errors.append(f"{zone.name}: {exc}")
            continue

        row = stored.get(zone.uid)
        if row is None:
            inserts.append(GeoZone(country_id=country.id, external_id=zone.uid, **values))
        elif any(getattr(row, field) != values[field] for field in _COMPARED_FIELDS):
            # the polygon or the classification may have changed, measure the terrain again
            updates.append({"id": row.id, "updated_at": now, "terrain_max_m": None, **values})
        else:
            unchanged += 1

    db.add_all(inserts)
    if updates:
        await db.execute(update(GeoZone), updates)
    await db.flush()

    parents_linked = await _link_parents(country.id, incoming.values(), db)
    terrain_measured = await Queries.Dem.measure_zone_terrain(db)
    await db.commit()

    if errors:
        logger.warning(f"Geo-zone sync skipped {len(errors)} zones: {errors[:MAX_REPORTED_ERRORS]}")

    return CatalogSyncReport(
        fetched=len(incoming),
        inserted=len(inserts),
        updated=len(updates),
        unchanged=unchanged,
        deleted=len(removed),
        skipped=len(errors),
        parents_linked=parents_linked,
        terrain_measured=terrain_measured,
        errors=errors[:MAX_REPORTED_ERRORS],
    )


async def _fetch_zones() -> list[Zone]:
    try:
        async with DroneMapClient(snapshot_dir=PANSA_SNAPSHOT_DIR) as client:
            return await client.zones()
    except (httpx.HTTPError, RuntimeError) as exc:
        raise APIExceptions.bad_gateway(f"PANSA request failed: {exc}")


async def _resolve_country(db: AsyncDBSession) -> Country:
    country = await Queries.Country.get_by_tag(DEFAULT_COUNTRY_TAG, db)

    if country is None:
        country = Country(name=DEFAULT_COUNTRY_NAME, country_tag=DEFAULT_COUNTRY_TAG)
        db.add(country)
        await db.flush()

    return country


def _zone_values(zone: Zone) -> dict[str, Any]:
    polygon = shape(zone.geometry)
    if not isinstance(polygon, Polygon):
        raise ValueError(f"unsupported geometry type {polygon.geom_type}")

    if zone.min_ft > zone.max_ft:
        raise ValueError(f"lower limit {zone.min_ft} ft is above upper limit {zone.max_ft} ft")

    classification = classify(zone)
    description = zone.description

    return {
        "type": classification.type,
        "source_type": zone.type,
        "activity_mode": classification.activity_mode,
        "tag": zone.name,
        "zone_polygon": polygon,
        "lower_limit_ft": zone.min_ft,
        "upper_limit_ft": zone.max_ft,
        "valid_from": zone.start,
        "valid_to": zone.stop,
        "description_pl": description.pl if description else None,
        "description_en": description.en if description else None,
        "contact": zone.contact,
        "source_modified_at": zone.modified,
    }


async def _link_parents(country_id: int, zones: Iterable[Zone], db: AsyncDBSession) -> int:
    rows: dict[UUID, Row] = {row.external_id: row for row in await Queries.GeoZone.get_sync_states(country_id, db)}
    ids_by_tag = {row.tag: row.id for row in rows.values()}

    changes = []
    for zone in zones:
        row = rows.get(zone.uid)
        if row is None:
            continue

        parent_id = ids_by_tag.get(zone.master) if zone.master else None
        if row.parent_id != parent_id:
            changes.append({"id": row.id, "parent_id": parent_id})

    if changes:
        await db.execute(update(GeoZone), changes)

    return len(changes)


class _ZoneLookup:
    """Finds zones by name; AUP and NOTAM spell some names differently, e.g. EPTR1078 for EP.TR1078."""

    def __init__(self, rows: list[Row]) -> None:
        self._by_tag = {row.tag: row for row in rows}

        candidates: dict[str, list[Row]] = {}
        for row in rows:
            candidates.setdefault(_name_key(row.tag), []).append(row)
        self._by_key = {key: found[0] for key, found in candidates.items() if len(found) == 1}

    def get(self, name: str) -> Optional[Row]:
        return self._by_tag.get(name) or self._by_key.get(_name_key(name))


def _name_key(name: str) -> str:
    # "DRA-R DTM Kakolewo" -> "DTMKAKOLEWO", "EP.TR1078" -> "EPTR1078"
    return re.sub(r"[^A-Z0-9]", "", re.sub(r"^DRA-[A-Z]+\s+", "", name.upper()))


class _Window(NamedTuple):
    zone_name: str
    source: GeoZoneActivitySource
    source_ref: str
    start_at: datetime
    ends_at: datetime
    lower_limit_ft: Optional[int]
    upper_limit_ft: Optional[int]


async def sync_activity(db: AsyncDBSession) -> ActivitySyncReport:
    activations, notams = await _fetch_activity()
    country = await _resolve_country(db)
    zones = _ZoneLookup(await Queries.GeoZone.get_activity_targets(country.id, db))

    now = datetime.now(timezone.utc)
    until = (now + timedelta(days=ACTIVITY_HORIZON_DAYS)).replace(hour=0, minute=0, second=0, microsecond=0)

    # (zone id, start, end, lower, upper) -> (source, reference); the same window from AUP and UUP is kept once
    wanted: dict[tuple, tuple[GeoZoneActivitySource, str]] = {}
    unmatched: set[str] = set()
    ignored = 0

    for window in [*_activation_windows(activations, now), *_notam_windows(notams, now, until)]:
        zone = zones.get(window.zone_name)
        if zone is None:
            unmatched.add(window.zone_name)
            continue

        # Permanent zones are active anyway, inherited ones follow their parent
        if zone.activity_mode != GeoZoneActivityMode.SCHEDULED:
            ignored += 1
            continue

        key = (
            zone.id, window.start_at, window.ends_at,
            _own_limit(window.lower_limit_ft, zone.lower_limit_ft), _own_limit(window.upper_limit_ft, zone.upper_limit_ft),
        )
        if key not in wanted or window.source is GeoZoneActivitySource.UUP:
            wanted[key] = (window.source, window.source_ref)

    rows = {
        (row.geo_zone_id, row.start_at, row.ends_at, row.lower_limit_ft, row.upper_limit_ft, row.source, row.source_ref): row.id
        for row in await Queries.GeoZone.get_activity_windows(country.id, db)
    }
    target = {key + source for key, source in wanted.items()}

    removed = [row_id for key, row_id in rows.items() if key not in target]
    if removed:
        await db.execute(delete(ActivityTime).where(ActivityTime.id.in_(removed)))

    added = [key for key in target if key not in rows]
    db.add_all(
        ActivityTime(
            geo_zone_id=zone_id, start_at=start_at, ends_at=ends_at,
            lower_limit_ft=lower_limit_ft, upper_limit_ft=upper_limit_ft, source=source, source_ref=source_ref,
        )
        for zone_id, start_at, ends_at, lower_limit_ft, upper_limit_ft, source, source_ref in added
    )
    await db.commit()

    return ActivitySyncReport(
        activations=len(activations),
        notams=len(notams),
        windows=len(target),
        inserted=len(added),
        deleted=len(removed),
        unchanged=len(target) - len(added),
        zones_with_windows=len({key[0] for key in target}),
        ignored=ignored,
        unmatched=sorted(unmatched)[:MAX_REPORTED_ERRORS],
    )


async def _fetch_activity() -> tuple[list[Activation], list[Notam]]:
    try:
        async with DroneMapClient(snapshot_dir=PANSA_SNAPSHOT_DIR) as client:
            return await client.activations(), await client.notams()
    except (httpx.HTTPError, RuntimeError) as exc:
        raise APIExceptions.bad_gateway(f"PANSA request failed: {exc}")


def _activation_windows(activations: list[Activation], now: datetime) -> list[_Window]:
    return [
        _Window(
            zone_name=activation.designator,
            source=GeoZoneActivitySource.UUP if activation.plan == "UUP" else GeoZoneActivitySource.AUP,
            source_ref=str(activation.id),
            start_at=activation.start.replace(microsecond=0),
            ends_at=activation.stop.replace(microsecond=0),
            lower_limit_ft=activation.min_ft,
            upper_limit_ft=activation.max_ft,
        )
        for activation in activations
        if activation.stop > now
    ]


def _notam_windows(notams: list[Notam], now: datetime, until: datetime) -> list[_Window]:
    return [
        _Window(
            zone_name=notam.zone_name,
            source=GeoZoneActivitySource.NOTAM,
            source_ref=notam.series,
            start_at=start_at,
            ends_at=ends_at,
            lower_limit_ft=notam.lower_ft,
            upper_limit_ft=notam.upper_ft,
        )
        for notam in current_notams(notams)
        if notam.zone_name
        for start_at, ends_at in notam_windows(notam, now, until)
    ]


async def sync_terrain(db: AsyncDBSession) -> TerrainSyncReport:
    cells = [TileCell(lat=row.lat, lon=row.lon) for row in await Queries.Dem.get_cells_covering_geo_zones(db)]
    if not cells:
        raise APIExceptions.conflict("No geo-zones stored, run the catalog sync first")

    stored = await Queries.Dem.get_stored_tiles(db)
    missing = [cell for cell in cells if cell.name not in stored]
    loaded: list[str] = []
    sea: list[str] = []

    try:
        async with CopernicusDemClient() as client:
            for cell in missing:
                geotiff = await client.tile(cell)
                if geotiff is None:
                    sea.append(cell.name)
                    continue

                # one tile per transaction, a failed sync keeps the tiles loaded before
                await Queries.Dem.add_tile(cell.name, geotiff, db)
                await db.commit()
                loaded.append(cell.name)
    except httpx.HTTPError as exc:
        raise APIExceptions.bad_gateway(f"Copernicus DEM request failed after {len(loaded)} new tiles: {exc}")

    terrain_measured = await Queries.Dem.measure_zone_terrain(db)
    await db.commit()

    return TerrainSyncReport(
        cells=len(cells),
        stored=len(cells) - len(missing),
        loaded=len(loaded),
        sea=sea,
        terrain_measured=terrain_measured,
        attribution=DEM_ATTRIBUTION,
    )


def _own_limit(limit: Optional[int], zone_limit: int) -> Optional[int]:
    # Store a reserved limit only when it differs from the zone itself
    return None if limit is None or limit == zone_limit else limit
