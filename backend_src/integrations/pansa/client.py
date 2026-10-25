import ssl
from pathlib import Path
from typing import Any, Optional, TypeVar

import certifi
import httpx
from loguru import logger
from pydantic import BaseModel, ValidationError

from backend_src.core.config import Settings
from .constants import (
    ACTIVATIONS_PATH,
    INTERMEDIATE_CA,
    LOGIN_PATH,
    NOTAMS_PATH,
    TIMEOUT_SECONDS,
    ZONE_TYPES_PATH,
    ZONES_PATH,
)
from .schema import Activation, Notam, Zone, ZoneType


Model = TypeVar("Model", bound=BaseModel)


def _ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cafile=INTERMEDIATE_CA)
    return context


class DroneMapClient:
    """Read-only client for the API behind dronemap.pansa.pl.

    With ``snapshot_dir`` set, every raw list response is also saved there as ``<name>.json``.
    """

    def __init__(self, snapshot_dir: Optional[Path] = None) -> None:
        if not Settings.PANSA_API_KEY:
            raise RuntimeError("PANSA_API_KEY is not set")

        self._snapshot_dir = snapshot_dir
        self._token: Optional[str] = None
        self._client = httpx.AsyncClient(
            base_url=Settings.PANSA_API_URL,
            headers={"x-api-key": Settings.PANSA_API_KEY, "User-Agent": Settings.PANSA_USER_AGENT},
            verify=_ssl_context(),
            timeout=TIMEOUT_SECONDS,
        )

    async def __aenter__(self) -> "DroneMapClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.aclose()

    async def zones(self) -> list[Zone]:
        return await self._get_list(ZONES_PATH, "zones", Zone)

    async def zone_types(self) -> list[ZoneType]:
        return await self._get_list(ZONE_TYPES_PATH, "zone_types", ZoneType)

    async def activations(self) -> list[Activation]:
        return await self._get_list(ACTIVATIONS_PATH, "activations", Activation)

    async def notams(self) -> list[Notam]:
        return await self._get_list(NOTAMS_PATH, "notams", Notam)

    async def _login(self) -> None:
        response = await self._client.post(LOGIN_PATH)
        response.raise_for_status()

        token = response.json().get("access_token")
        if not token:
            raise RuntimeError(f"PANSA login returned no token: {response.text[:200]}")

        self._token = token

    async def _get(self, path: str, headers: Optional[dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        if self._token is None:
            await self._login()

        response = await self._client.get(path, headers=self._auth(headers), **kwargs)

        # the token lives for an hour, log in again once if it has expired
        if response.status_code == httpx.codes.UNAUTHORIZED:
            await self._login()
            response = await self._client.get(path, headers=self._auth(headers), **kwargs)

        response.raise_for_status()
        return response

    def _auth(self, headers: Optional[dict[str, str]]) -> dict[str, str]:
        return {**(headers or {}), "Authorization": f"Bearer {self._token}"}

    async def _get_list(self, path: str, name: str, model: type[Model]) -> list[Model]:
        response = await self._get(path)
        self._save_snapshot(name, response.content)

        payload = response.json()
        rows = payload.get("properties") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise RuntimeError(f"Unexpected response from {path}: no 'properties' list")

        items: list[Model] = []
        for row in rows:
            try:
                items.append(model.model_validate(row))
            except ValidationError as exc:
                key = (row.get("uid") or row.get("name") or row.get("designator")) if isinstance(row, dict) else None
                logger.warning(f"PANSA {name}: skipped {key}: {exc.errors()[0]['msg']}")

        if len(items) < len(rows):
            logger.warning(f"PANSA {name}: skipped {len(rows) - len(items)} of {len(rows)} rows")

        return items

    def _save_snapshot(self, name: str, content: bytes) -> None:
        if self._snapshot_dir is None:
            return

        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        (self._snapshot_dir / f"{name}.json").write_bytes(content)
