from httpx import Client

from tests import constants
from tests.types import EndpointCreator, PilotInfo
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import checkin_create, checkin_end, checkin_preview
from tests.utils.behavioural.mission_behaviour import (
    drone_serial, import_missions, imported_ids, mission_checkin_plan, mission_feature, own_mission,
)


def test_mission_from_decision_to_flight(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    serial = drone_serial(client, pilot, get_endpoint_link)
    feature = mission_feature(pilot, serial, constants.CHECKIN_CLEAN_POINT, "pending")
    external_id = feature["properties"]["external_id"]

    # PANSA receives the mission
    r = import_missions(client, get_endpoint_link, [feature])
    assert r.status_code == 200, f"Mission was not imported: {r.text}"
    mission_id = imported_ids(r)[external_id]

    r = checkin_preview(client, pilot, get_endpoint_link, mission_checkin_plan(pilot["drone_id"], mission_id))
    assert "checkin.mission_pending" in functional.error_types(r), f"A pending mission must not be flown: {r.text}"

    # PANSA accepts it
    feature["properties"]["status"] = "accepted"
    r = import_missions(client, get_endpoint_link, [feature])
    assert r.json()["missions"][0] == {"external_id": external_id, "id": mission_id, "status": "accepted"}, \
        f"The decision must update the same mission: {r.text}"

    # the pilot flies it
    r = checkin_preview(client, pilot, get_endpoint_link, mission_checkin_plan(pilot["drone_id"], mission_id))
    assert r.status_code == 200, f"An accepted mission must be flown: {r.text}"
    assert checkin_create(client, pilot, get_endpoint_link, r.json()["checkin_token"]).status_code == 201, "Check-in was not started"
    assert own_mission(client, pilot, get_endpoint_link, mission_id).json()["properties"]["status"] == "active"

    assert checkin_end(client, pilot, get_endpoint_link).status_code == 200, "Check-in was not ended"
    assert own_mission(client, pilot, get_endpoint_link, mission_id).json()["properties"]["status"] == "ended_intime"

    # a flown mission is history, PANSA cannot change it any more
    feature["properties"]["status"] = "rejected"
    feature["properties"]["decision_reason"] = "Too late"
    r = import_missions(client, get_endpoint_link, [feature])
    assert r.status_code == 422, f"A flown mission must not be changed: {r.text}"
    assert functional.error_types(r) == {"mission.flown"}, f"Wrong error: {r.text}"
