import httpx

from backend_src.db import Queries, AsyncDBSession
from backend_src.integrations.copernicus import ATTRIBUTION, CopernicusDemClient, TileCell
from .errors import NothingToSync, UpstreamUnavailable
from .reports import TerrainSyncReport


async def sync_terrain(db: AsyncDBSession) -> TerrainSyncReport:
    cells = [TileCell(lat=row.lat, lon=row.lon) for row in await Queries.Dem.get_cells_covering_geo_zones(db)]
    if not cells:
        raise NothingToSync("No geo-zones stored, run the catalog sync first")

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
        raise UpstreamUnavailable(f"Copernicus DEM request failed after {len(loaded)} new tiles: {exc}")

    terrain_measured = await Queries.Dem.measure_zone_terrain(db)
    await db.commit()

    return TerrainSyncReport(
        cells=len(cells),
        stored=len(cells) - len(missing),
        loaded=len(loaded),
        sea=sea,
        terrain_measured=terrain_measured,
        attribution=ATTRIBUTION,
    )
