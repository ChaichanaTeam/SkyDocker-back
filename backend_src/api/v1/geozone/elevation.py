from typing import NamedTuple, Optional

from backend_src.db import Queries, AsyncDBSession
from backend_src.integrations import ElevationProvider
from backend_src.integrations.pansa import SrtmElevation


class DemElevation:
    """Ground elevation from the Copernicus DEM that the terrain sync stores in PostGIS."""

    name = "copernicus_dem"

    def __init__(self, db: AsyncDBSession) -> None:
        self._db = db

    async def elevation_m(self, lon: float, lat: float) -> Optional[float]:
        return await Queries.Dem.get_elevation_m(lon, lat, self._db)


class GroundElevation(NamedTuple):
    metres: float
    source: str


async def ground_elevation(lon: float, lat: float, db: AsyncDBSession) -> Optional[GroundElevation]:
    """Elevation from the first provider that has data for the point: own DEM, then PANSA SRTM."""
    providers: list[ElevationProvider] = [DemElevation(db), SrtmElevation()]

    for provider in providers:
        metres = await provider.elevation_m(lon, lat)
        if metres is not None:
            return GroundElevation(metres, provider.name)

    return None
