from pathlib import Path

from .client import DroneMapClient


async def download_kml(dst: Path) -> None:
    async with DroneMapClient() as client:
        dst.write_bytes(await client.kml())
