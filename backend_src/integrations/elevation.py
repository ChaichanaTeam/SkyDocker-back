from typing import Optional, Protocol


class ElevationProvider(Protocol):
    """Source of ground elevation: the own Copernicus DEM in PostGIS, PANSA SRTM as a fallback."""

    # reported to clients together with the elevation
    name: str

    async def elevation_m(self, lon: float, lat: float) -> Optional[float]:
        """Ground elevation in metres above mean sea level, None where the source has no data for the point."""
        ...
