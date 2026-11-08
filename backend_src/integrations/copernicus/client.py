from typing import Any, Optional

import httpx

from .constants import BASE_URL, TIMEOUT_SECONDS
from .tile import TileCell


class CopernicusDemClient:
    """Downloads Copernicus DEM GLO-90 tiles: Cloud Optimized GeoTIFFs with heights in metres above mean sea level."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT_SECONDS)

    async def __aenter__(self) -> "CopernicusDemClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.aclose()

    async def tile(self, cell: TileCell) -> Optional[bytes]:
        """GeoTIFF of the cell, None where the grid has no tile: open sea has no land to measure."""
        response = await self._client.get(cell.path)

        if response.status_code == httpx.codes.NOT_FOUND:
            return None

        response.raise_for_status()
        return response.content
