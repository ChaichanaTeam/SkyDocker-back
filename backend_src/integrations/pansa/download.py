import ssl
from pathlib import Path

import certifi
import httpx

from .constants import API, HEADERS, INTERMEDIATE_CA, KML_MIME, TIMEOUT_SECONDS


def _ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cafile=INTERMEDIATE_CA)
    return context


async def _get_token(client: httpx.AsyncClient) -> str:
    r = await client.post(f"{API}/v1/front/login")
    r.raise_for_status()
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        raise RuntimeError(f"Server didn't return token: {data}")
    return token


async def download_kml(dst: Path) -> None:
    async with httpx.AsyncClient(headers=HEADERS, verify=_ssl_context(), timeout=TIMEOUT_SECONDS) as client:
        token = await _get_token(client)
        r = await client.get(
            f"{API}/v1/kml",
            params={"extrude": "false"},
            headers={"Authorization": f"Bearer {token}", "Accept": KML_MIME},
        )
        r.raise_for_status()

    if b"<kml" not in r.content[:500]:
        raise RuntimeError("Response is not KML")

    dst.write_bytes(r.content)
