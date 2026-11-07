import httpx
from sqlalchemy.exc import DBAPIError

from backend_src.db import Queries, AsyncDBSession
from backend_src.integrations.gadm import ATTRIBUTION, GADMDataClient
from backend_src.models import Country
from .errors import NotPublished, SyncAborted, UpstreamUnavailable
from .reports import BorderSyncReport


async def sync_border(country: Country, db: AsyncDBSession) -> BorderSyncReport:
    # read before commit, the session expires the country afterwards
    country_id, country_tag = country.id, country.country_tag

    try:
        async with GADMDataClient() as client:
            source, border = await client.border(country_tag)
    except ValueError as exc:
        raise NotPublished(str(exc))
    except httpx.HTTPError as exc:
        raise UpstreamUnavailable(f"GADM request failed: {exc}")

    # border and its parts change together, a failed sync keeps the previous ones
    try:
        await Queries.Country.upsert_border(country_id, border, source, db)
        parts = await Queries.Country.rebuild_parts(country_id, db)
        await db.commit()
    except DBAPIError as exc:
        await db.rollback()
        raise SyncAborted(f"GADM border was rejected by PostGIS: {exc.orig}")

    return BorderSyncReport(
        country_tag=country_tag,
        source=source,
        polygons=len(border.geoms),
        parts=parts,
        attribution=ATTRIBUTION,
    )
