from typing import Any, Iterator, Optional, Sequence
from httpx import Response, Client

from tests.types import PilotInfo, UserInfo, EndpointCreator
from tests.utils import functional
from .registration_behaviour import registration_flow


def _auth(user: UserInfo) -> dict[str, str]:
    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def grant_privileges(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, privileges: Sequence[str]
) -> Response:
    request = {
        "url": get_endpoint_link("demo", "flying-privilege/grant"),
        "params": {
            "email": user["email"],
            "privileges": list(privileges),
            "phone_number": user["phone_number"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
        }
    }
    r = client.post(**request)

    return r


def create_drone(client: Client, user: PilotInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("demo", "drone-park/random"),
        "params": {"email": user["email"], "count": 1}
    }
    r = client.post(**request)

    if r.status_code == 200:
        user["drone_id"] = r.json()["drones"][0]["id"]

    return r


def checkin_preview(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, body: dict[str, Any]
) -> Response:
    request = {
        "url": get_endpoint_link("live", "check-in/preview"),
        "headers": _auth(user),
        "json": body
    }
    r = client.post(**request)

    return r


def checkin_create(
    client: Client, user: PilotInfo, get_endpoint_link: EndpointCreator, token: Optional[str] = None
) -> Response:
    request = {
        "url": get_endpoint_link("live", "check-in/"),
        "headers": _auth(user),
        "json": {"checkin_token": token if token is not None else user["checkin_token"]}
    }
    r = client.post(**request)

    return r


def checkin_end(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "check-in/end"),
        "headers": _auth(user)
    }
    r = client.post(**request)

    return r


def checkin_bbox(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, point: tuple[float, float],
    margin: float = 0.01, country_tag: str = "PL"
) -> Response:
    lon, lat = point
    request = {
        "url": get_endpoint_link("live", "check-in/"),
        "headers": _auth(user),
        "params": {
            "country_tag": country_tag,
            "min_lon": lon - margin, "min_lat": lat - margin, "max_lon": lon + margin, "max_lat": lat + margin,
        }
    }
    r = client.get(**request)

    return r


def pilot_flow(
    client: Client, user: PilotInfo, get_endpoint_link: EndpointCreator, privileges: Sequence[str] = ("a1",)
) -> bool:
    if not registration_flow(client, user, get_endpoint_link):
        return False

    r = grant_privileges(client, user, get_endpoint_link, privileges)
    if r.status_code != 200:
        return False

    r = create_drone(client, user, get_endpoint_link)
    return r.status_code == 200


def checkin_flow(
    client: Client, user: PilotInfo, get_endpoint_link: EndpointCreator, point: tuple[float, float]
) -> Response:
    """Preview and start a check-in, returns the last response."""
    r = checkin_preview(client, user, get_endpoint_link, functional.checkin_plan(point, user["drone_id"]))
    if r.status_code != 200:
        return r

    user["checkin_token"] = r.json()["checkin_token"]
    return checkin_create(client, user, get_endpoint_link)


def pilot_lifetime(client: Client, get_endpoint_link: EndpointCreator) -> Iterator[PilotInfo]:
    """Fixture body: a registered pilot with the a1 privilege and a drone, its check-in is ended afterwards."""
    pilot = functional.create_pilot()
    assert pilot_flow(client, pilot, get_endpoint_link), "Pilot setup failed"

    yield pilot

    # an active check-in would block the pilot in later tests
    checkin_end(client, pilot, get_endpoint_link)
