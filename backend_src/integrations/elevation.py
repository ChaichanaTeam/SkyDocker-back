from typing import Protocol


class ElevationProvider(Protocol):
    """Source of ground elevation, PANSA SRTM for now, an own DEM in PostGIS later."""

    async def elevation_m(self, lon: float, lat: float) -> float:
        """Ground elevation in metres above mean sea level."""
        ...
