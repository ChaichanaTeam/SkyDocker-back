from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest
from httpx import Client

from tests import constants
from tests.types import EndpointCreator, PilotInfo
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import checkin_create, checkin_end, checkin_preview
from tests.utils.behavioural.mission_behaviour import (
    drone_serial, import_missions, imported_ids, mission_checkin_plan, mission_feature, own_mission,
)


CLEAN = constants.CHECKIN_CLEAN_POINT


@pytest.fixture(scope="module")
def serial(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator) -> str:
    return drone_serial(client, pilot, get_endpoint_link)


@pytest.fixture
def ended(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator) -> Iterator[None]:
    """Ends the check-in a test started, the pilot can have one at a time."""
    yield
    checkin_end(client, pilot, get_endpoint_link)


def _mission(client: Client, get_endpoint_link: EndpointCreator, feature: dict) -> int:
    r = import_missions(client, get_endpoint_link, [feature])
    assert r.status_code == 200, f"Mission was not imported: {r.text}"
    return imported_ids(r)[feature["properties"]["external_id"]]


def _preview(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator, mission_id: int, **overrides):
    plan = mission_checkin_plan(pilot["drone_id"], mission_id, **overrides)
    return checkin_preview(client, pilot, get_endpoint_link, plan)


@pytest.mark.parametrize("status, overrides, error", [
    pytest.param("pending", {}, "checkin.mission_pending", id="pending"),
    pytest.param("rejected", {}, "checkin.mission_rejected", id="rejected"),
    pytest.param("accepted", {"starts_at": "2026-01-01T08:00:00Z", "ends_at": "2026-01-01T16:00:00Z"},
                 "checkin.mission_outside_window", id="window-passed"),
])
def test_mission_must_be_accepted_and_open(
    client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator, status: str, overrides: dict, error: str,
):
    mission_id = _mission(client, get_endpoint_link, mission_feature(pilot, serial, CLEAN, status, **overrides))

    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert r.status_code == 422, f"The mission must not be flown: {r.text}"
    assert error in functional.error_types(r), f"Expected {error}: {r.text}"


def test_rejection_reason_is_shown(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    feature = mission_feature(pilot, serial, CLEAN, "rejected", decision_reason="Too close to the airport")
    mission_id = _mission(client, get_endpoint_link, feature)

    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert any("Too close to the airport" in e["msg"] for e in r.json()["detail"]), f"The pilot must see why: {r.text}"

    r = own_mission(client, pilot, get_endpoint_link, mission_id)
    properties = r.json()["properties"]
    assert properties["decision_reason"] == "Too close to the airport", f"The pilot must see the reason: {r.text}"
    assert properties["external_id"] == feature["properties"]["external_id"], f"The PANSA number must be shown: {r.text}"


def test_mission_excludes_home_point(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    mission_id = _mission(client, get_endpoint_link, mission_feature(pilot, serial, CLEAN))

    lon, lat = CLEAN
    r = _preview(client, pilot, get_endpoint_link, mission_id, home_point={"lon": lon, "lat": lat})
    assert r.status_code == 422, f"A mission flies from its own point: {r.text}"
    assert not any(t.startswith("checkin.") for t in functional.error_types(r)), f"Validation must fail first: {r.text}"


def test_flight_follows_mission(
    client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator, ended: None,
):
    # 20 minutes of the window are left, the 30 minutes of flight are cut to them
    now = datetime.now(timezone.utc)
    feature = mission_feature(
        pilot, serial, CLEAN, height=40, range=300, duration=30,
        starts_at=(now - timedelta(minutes=40)).isoformat(), ends_at=(now + timedelta(minutes=20)).isoformat(),
    )
    mission_id = _mission(client, get_endpoint_link, feature)

    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert r.status_code == 200, f"An accepted mission in its window must be flown: {r.text}"
    r = checkin_create(client, pilot, get_endpoint_link, r.json()["checkin_token"])
    assert r.status_code == 201, f"Check-in was not started: {r.text}"

    checkin = r.json()
    assert tuple(checkin["geometry"]["coordinates"]) == CLEAN, f"The check-in must start at the mission point: {r.text}"
    assert checkin["properties"]["height"] == 40, f"The mission height must be used: {r.text}"
    assert checkin["properties"]["time"] <= 20 * 60, f"The flight must end with the mission window: {r.text}"


def test_mission_status_follows_checkin(
    client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator,
):
    mission_id = _mission(client, get_endpoint_link, mission_feature(pilot, serial, CLEAN))

    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert checkin_create(client, pilot, get_endpoint_link, r.json()["checkin_token"]).status_code == 201, "Check-in was not started"
    status = own_mission(client, pilot, get_endpoint_link, mission_id).json()["properties"]["status"]
    assert status == "active", f"A mission in flight must be active, got {status}"

    assert checkin_end(client, pilot, get_endpoint_link).status_code == 200, "Check-in was not ended"
    status = own_mission(client, pilot, get_endpoint_link, mission_id).json()["properties"]["status"]
    assert status == "ended_intime", f"A mission flown in time must end in time, got {status}"

    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert "checkin.mission_closed" in functional.error_types(r), f"A mission is flown once: {r.text}"


def test_mission_replaces_consent(
    client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator,
):
    point = constants.CHECKIN_CONSENT_POINT
    r = checkin_preview(client, pilot, get_endpoint_link, functional.checkin_plan(point, pilot["drone_id"], height=60))
    assert "checkin.zone_needs_consent" in functional.error_types(r), f"Without a mission the zone needs consent: {r.text}"

    mission_id = _mission(client, get_endpoint_link, mission_feature(pilot, serial, point, height=60))
    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert r.status_code == 200, f"An accepted mission must replace the consent: {r.text}"


def test_mission_keeps_prohibition(
    client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator,
):
    feature = mission_feature(pilot, serial, constants.CHECKIN_PROHIBITED_POINT, height=30, range=100)
    mission_id = _mission(client, get_endpoint_link, feature)

    r = _preview(client, pilot, get_endpoint_link, mission_id)
    assert "checkin.zone_prohibited" in functional.error_types(r), f"A prohibited zone stays prohibited: {r.text}"
