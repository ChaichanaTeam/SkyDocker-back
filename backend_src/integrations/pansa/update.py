from datetime import datetime
from pathlib import Path
from typing import Any

from starlette.concurrency import run_in_threadpool

from .convert import kml_to_geojson
from .download import download_kml


async def update_geozones(data_dir: Path) -> tuple[Path, dict[str, Any]]:
    stamp = f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
    kml = data_dir / f"utm-zones-{stamp}.kml"
    geojson = data_dir / f"utm-zones-{stamp}.geojson"

    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        await download_kml(kml)
        report = await run_in_threadpool(kml_to_geojson, kml, geojson)
    finally:
        kml.unlink(missing_ok=True)

    return geojson, report
