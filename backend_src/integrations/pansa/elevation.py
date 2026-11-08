from typing import Optional

import httpx

from backend_src.core.config import Settings
from .constants import SRTM_TIMEOUT_SECONDS, SRTM_URL


class SrtmElevation:
    """Ground elevation from the SRTM service behind dronemap.pansa.pl."""

    name = "pansa_srtm"

    async def elevation_m(self, lon: float, lat: float) -> Optional[float]:
        async with httpx.AsyncClient(headers={"User-Agent": Settings.PANSA_USER_AGENT}, timeout=SRTM_TIMEOUT_SECONDS) as client:
            response = await client.get(SRTM_URL, params={"lat": lat, "lon": lon})

        # 400 for points without an SRTM tile, e.g. open sea
        if response.status_code == httpx.codes.BAD_REQUEST:
            return None

        response.raise_for_status()

        elevation = response.json().get("hgtElevation")
        if not isinstance(elevation, (int, float)):
            raise RuntimeError(f"PANSA SRTM returned no elevation: {response.text[:200]}")

        return float(elevation)
