import json
from typing import Any, Optional

from fastapi import UploadFile
from shapely.geometry import Polygon
from sqlalchemy import delete, select

from backend_src.api.exceptions import APIExceptions
from backend_src.db import AsyncDBSession
from backend_src.models import Country, GeoZone
from backend_src.models.enum import GeoZoneType
from .constants import DEFAULT_COUNTRY_NAME, DEFAULT_COUNTRY_TAG


def _load_feature_collection(raw: bytes) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise APIExceptions.bad_request(f"Invalid JSON: {exc}")

    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise APIExceptions.bad_request("Expected a GeoJSON FeatureCollection")

    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise APIExceptions.bad_request("FeatureCollection has no features")

    return features


def _polygon_from_geometry(geometry: dict[str, Any]) -> Polygon:
    if geometry.get("type") != "Polygon":
        raise ValueError(f"unsupported geometry type: {geometry.get('type')}")

    rings = geometry.get("coordinates") or []
    if not rings:
        raise ValueError("polygon has no coordinates")

    return Polygon(rings[0], rings[1:])


def _geozone_type(raw: Optional[str]) -> GeoZoneType:
    try:
        return GeoZoneType(raw)
    except ValueError:
        raise ValueError(f"unknown geo zone type: {raw!r}")


async def _resolve_country(db: AsyncDBSession, name: str, tag: str) -> Country:
    country = (
        await db.execute(select(Country).where(Country.country_tag == tag))
    ).scalar_one_or_none()

    if country is None:
        country = Country(name=name, country_tag=tag)
        db.add(country)
        await db.flush()

    return country


async def import_geozones(db: AsyncDBSession, file: UploadFile, reset: bool) -> dict[str, Any]:
    features = _load_feature_collection(await file.read())
    country = await _resolve_country(db, DEFAULT_COUNTRY_NAME, DEFAULT_COUNTRY_TAG)
    country_id = country.id
    country_name = country.name

    if reset:
        await db.execute(delete(GeoZone).where(GeoZone.country_id == country_id))

    zones: list[GeoZone] = []
    errors: list[str] = []

    for index, feature in enumerate(features):
        props = feature.get("properties") or {}
        tag = props.get("name") or props.get("tag") or f"zone-{index}"

        try:
            polygon = _polygon_from_geometry(feature.get("geometry") or {})
            zone_type = _geozone_type(props.get("type"))
        except ValueError as exc:
            errors.append(f"{tag}: {exc}")
            continue

        zones.append(
            GeoZone(
                country_id=country_id,
                type=zone_type,
                tag=str(tag),
                strength=int(props.get("strength") or 0),
                zone_polygon=polygon,
                height_agl=props.get("height_agl"),
                height_amsl=props.get("height_amsl"),
            )
        )

    if not zones:
        raise APIExceptions.bad_request("No valid geo zones to import")

    db.add_all(zones)
    await db.commit()

    return {
        "message": f"Imported {len(zones)} geo zones for {country_name}",
        "imported": len(zones),
        "skipped": len(errors),
        "errors": errors[:20],
    }
