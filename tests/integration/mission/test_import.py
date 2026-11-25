import pytest
from httpx import Client

from tests import constants
from tests.types import EndpointCreator, PilotInfo
from tests.utils import functional
from tests.utils.behavioural.mission_behaviour import (
    demo_missions, drone_serial, import_missions, imported_ids, mission_feature,
)


CLEAN = constants.CHECKIN_CLEAN_POINT


@pytest.fixture(scope="module")
def serial(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator) -> str:
    return drone_serial(client, pilot, get_endpoint_link)


def test_import_decisions(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    features = [mission_feature(pilot, serial, CLEAN, status) for status in ("pending", "accepted", "rejected")]
    r = import_missions(client, get_endpoint_link, features)
    assert r.status_code == 200, f"Missions were not imported: {r.text}"

    body = r.json()
    assert (body["created"], body["updated"]) == (3, 0), f"Three new missions were expected: {r.text}"
    assert [m["status"] for m in body["missions"]] == ["pending", "accepted", "rejected"], f"PANSA decisions must be kept: {r.text}"


def test_reimport_updates_decision(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    pending = mission_feature(pilot, serial, CLEAN, "pending")
    first = import_missions(client, get_endpoint_link, [pending])
    assert first.status_code == 200, f"Mission was not imported: {first.text}"

    pending["properties"]["status"] = "accepted"
    r = import_missions(client, get_endpoint_link, [pending])
    assert r.status_code == 200, f"The decision was not updated: {r.text}"
    assert (r.json()["created"], r.json()["updated"]) == (0, 1), f"The same external_id must update the mission: {r.text}"
    assert imported_ids(r) == imported_ids(first), "The updated mission must keep its id"
    assert r.json()["missions"][0]["status"] == "accepted", f"The new decision must be stored: {r.text}"


def test_import_is_all_or_nothing(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    good = mission_feature(pilot, serial, CLEAN)
    bad = mission_feature(pilot, serial, CLEAN, pilot_email="nobody.at.all@localhost.me")
    r = import_missions(client, get_endpoint_link, [good, bad])
    assert r.status_code == 422, f"A file with a wrong mission must be refused: {r.text}"
    assert functional.error_types(r) == {"mission.pilot_not_found"}, f"Wrong error: {r.text}"
    assert r.json()["detail"][0]["loc"][:2] == ["file", bad["properties"]["external_id"]], f"The error must name the mission: {r.text}"

    stored = {m["external_id"] for m in demo_missions(client, get_endpoint_link).json()["missions"]}
    assert good["properties"]["external_id"] not in stored, "Nothing of a refused file must be stored"


@pytest.mark.parametrize("overrides, error", [
    pytest.param({"drone_serial": "NO-SUCH-SERIAL"}, "mission.drone_not_found", id="unknown-drone"),
    pytest.param({"status": "rejected", "decision_reason": None}, "mission.value_error", id="rejected-without-reason"),
    pytest.param({"decision_reason": "Not rejected"}, "mission.value_error", id="reason-without-rejection"),
    pytest.param({"height": 121}, "mission.less_than_equal", id="height-over-120"),
    pytest.param({"range": 2001}, "mission.less_than_equal", id="range-over-2-km"),
    pytest.param({"duration": 4}, "mission.greater_than_equal", id="duration-under-5-min"),
    pytest.param({"duration": 120}, "mission.value_error", id="duration-longer-than-window"),
    pytest.param({"status": "active"}, "mission.literal_error", id="flight-status-from-file"),
    pytest.param({"starts_at": "2026-12-01T10:00:00"}, "mission.timezone_aware", id="time-without-zone"),
])
def test_wrong_mission(
    client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator, overrides: dict, error: str,
):
    r = import_missions(client, get_endpoint_link, [mission_feature(pilot, serial, CLEAN, **overrides)])
    assert r.status_code == 422, f"A wrong mission must be refused: {r.text}"
    assert error in functional.error_types(r), f"Expected {error}: {r.text}"


def test_point_outside_borders(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    r = import_missions(client, get_endpoint_link, [mission_feature(pilot, serial, constants.CHECKIN_OUTSIDE_POINT)])
    assert r.status_code == 422, f"A mission outside the synced borders must be refused: {r.text}"
    assert functional.error_types(r) == {"mission.outside_borders"}, f"Wrong error: {r.text}"


def test_repeated_external_id(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    mission = mission_feature(pilot, serial, CLEAN)
    r = import_missions(client, get_endpoint_link, [mission, mission])
    assert r.status_code == 422, f"An external_id twice in a file must be refused: {r.text}"
    assert functional.error_types(r) == {"mission.duplicate"}, f"Wrong error: {r.text}"


@pytest.mark.parametrize("content, reason", [
    pytest.param(b"{not json", "invalid-json", id="invalid-json"),
    pytest.param(b'{"type": "Feature"}', "not-a-collection", id="not-a-collection"),
    pytest.param(b'{"type": "FeatureCollection", "features": []}', "no-features", id="no-features"),
])
def test_unusable_file(client: Client, get_endpoint_link: EndpointCreator, content: bytes, reason: str):
    r = client.post(get_endpoint_link("demo", "mission/"), files={"file": ("missions.geojson", content, "application/geo+json")})
    assert r.status_code == 400, f"An unusable file must be refused ({reason}): {r.text}"


def test_list_by_status(client: Client, pilot: PilotInfo, serial: str, get_endpoint_link: EndpointCreator):
    r = import_missions(client, get_endpoint_link, [mission_feature(pilot, serial, CLEAN, "rejected")])
    rejected_id = r.json()["missions"][0]["id"]

    missions = demo_missions(client, get_endpoint_link, "rejected").json()["missions"]
    assert all(m["status"] == "rejected" for m in missions), "The list must keep only the asked status"
    assert rejected_id in {m["id"] for m in missions}, "The rejected mission must be listed"
