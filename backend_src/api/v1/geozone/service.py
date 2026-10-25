from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import UUID

import httpx
from loguru import logger
from shapely.geometry import Polygon, mapping, shape
from sqlalchemy import Row, delete, update

from backend_src.api.exceptions import APIExceptions
from backend_src.db import Queries, AsyncDBSession
from backend_src.api.shared_schemas import GeoJson, GeoFeature
from backend_src.api.shared_schemas import BoundingBox
from backend_src.integrations.pansa import DroneMapClient, Zone, classify
from backend_src.models import Country, GeoZone
from .constants import DEFAULT_COUNTRY_NAME, DEFAULT_COUNTRY_TAG, MAX_REPORTED_ERRORS, MIN_ZONES_RATIO, PANSA_SNAPSHOT_DIR
from .schema import CatalogSyncReport, GeozoneProperties


# Fields that make a stored zone outdated even if PANSA did not touch it, e.g. after classifier changes
_COMPARED_FIELDS = ("type", "source_type", "activity_mode", "source_modified_at")


async def geozone_bbox(bbox: BoundingBox, db: AsyncDBSession):
    geozones = await Queries.GeoZone.get_all_by_bbox(*bbox.unpack(), db)

    if len(geozones) == 0:
        raise APIExceptions.not_found("No zones in this region")

    features: list[GeoFeature] = [
        GeoFeature(geometry=mapping(gz.zone_polygon), properties=GeozoneProperties.from_geozone(gz)) for gz in geozones
    ]

    return GeoJson(
        features=features
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
            updates.append({"id": row.id, "updated_at": now, **values})
        else:
            unchanged += 1

    db.add_all(inserts)
    if updates:
        await db.execute(update(GeoZone), updates)
    await db.flush()

    parents_linked = await _link_parents(country.id, incoming.values(), db)
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
        errors=errors[:MAX_REPORTED_ERRORS],
    )


async def _fetch_zones() -> list[Zone]:
    try:
        async with DroneMapClient(snapshot_dir=PANSA_SNAPSHOT_DIR) as client:
            return await client.zones()
    except (httpx.HTTPError, RuntimeError) as exc:
        raise APIExceptions.bad_gateway(f"PANSA request failed: {exc}")


async def _resolve_country(db: AsyncDBSession) -> Country:
    country = await Queries.GeoZone.get_country_by_tag(DEFAULT_COUNTRY_TAG, db)

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
