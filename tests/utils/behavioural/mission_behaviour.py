import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from httpx import Response, Client

from tests.types import PilotInfo, UserInfo, EndpointCreator


def _auth(user: UserInfo) -> dict[str, str]:
    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def drone_serial(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator) -> str:
    r = client.get(get_endpoint_link("live", f"pilots/me/drones/{pilot['drone_id']}"), headers=_auth(pilot))
    assert r.status_code == 200, f"Drone of the pilot was not found: {r.text}"

    return r.json()["serial_number"]


def mission_feature(
    pilot: PilotInfo, serial: str, point: tuple[float, float], status: str = "accepted", **overrides
) -> dict[str, Any]:
    """A mission open from 10 minutes ago for an hour, an override set to None removes the property."""
    now = datetime.now(timezone.utc)
    properties: dict[str, Any] = {
        "external_id": f"TEST-{uuid.uuid4().hex[:12].upper()}",
        "pilot_email": pilot["email"],
        "drone_serial": serial,
        "flying_privilege": "a1",
        "status": status,
        "height": 60,
        "range": 200,
        "starts_at": (now - timedelta(minutes=10)).isoformat(),
        "ends_at": (now + timedelta(hours=1)).isoformat(),
        "duration": 30,
    }
    if status == "rejected":
        properties["decision_reason"] = "Test rejection"
    properties.update(overrides)

    lon, lat = point
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {key: value for key, value in properties.items() if value is not None},
    }


def import_missions(client: Client, get_endpoint_link: EndpointCreator, features: list[dict[str, Any]]) -> Response:
    content = json.dumps({"type": "FeatureCollection", "features": features}).encode()
    return client.post(
        get_endpoint_link("demo", "mission/"),
        files={"file": ("missions.geojson", content, "application/geo+json")},
    )


def demo_missions(client: Client, get_endpoint_link: EndpointCreator, status: Optional[str] = None) -> Response:
    params = {"limit": 1000, **({"status": status} if status else {})}
    return client.get(get_endpoint_link("demo", "mission/"), params=params)


def own_mission(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator, mission_id: int) -> Response:
    return client.get(get_endpoint_link("live", f"pilots/me/missions/{mission_id}"), headers=_auth(pilot))


def mission_checkin_plan(drone_id: Optional[int], mission_id: int, **overrides) -> dict[str, Any]:
    plan: dict[str, Any] = {"country_tag": "PL", "drone_id": drone_id, "mission_id": mission_id}
    plan.update(overrides)

    return plan


def imported_ids(r: Response) -> dict[str, int]:
    """Mission ids of an import by external_id."""
    return {mission["external_id"]: mission["id"] for mission in r.json()["missions"]}
