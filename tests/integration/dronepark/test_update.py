from typing import Iterator

import pytest
from httpx import Client

from tests import constants
from tests.types import EndpointCreator, PilotInfo, UserInfo
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import checkin_end, checkin_flow
from tests.utils.behavioural.dronepark_behaviour import (
    add_drone, custom_model, delete_drone, delete_model, drone_body, own_drone, random_serial, update_drone,
)
from tests.utils.behavioural.registration_behaviour import registration_flow


@pytest.fixture
def drone(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator) -> Iterator[dict]:
    """An unmodified c1 DJI Air 3 (720 g) of the owner."""
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(drone_catalog["DJI Air 3"]["id"]))
    assert r.status_code == 201, f"Drone was not added: {r.text}"

    yield r.json()
    delete_drone(client, drone_owner, get_endpoint_link, r.json()["id"])


def test_update_serial_number(client: Client, drone_owner: UserInfo, drone: dict, get_endpoint_link: EndpointCreator):
    serial = random_serial()
    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"serial_number": serial})
    assert r.status_code == 200, f"Serial number was not changed: {r.text}"
    assert r.json()["serial_number"] == serial, f"New serial number must be stored: {r.text}"
    assert r.json()["category"] == drone["category"], f"Fields not passed must stay: {r.text}"


def test_modified_drone_mass(client: Client, drone_owner: UserInfo, drone: dict, get_endpoint_link: EndpointCreator):
    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"is_drone_modified": True})
    assert r.status_code == 422, f"A modified drone needs its mass: {r.text}"
    assert functional.error_types(r) == {"drone.mass_required"}, f"Wrong error for the mass: {r.text}"

    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"is_drone_modified": True, "mtom_override": 950})
    assert r.status_code == 422, f"950 g does not fit the c1 class: {r.text}"
    assert functional.error_types(r) == {"drone.class_mass_mismatch"}, f"Wrong error for the class: {r.text}"

    r = update_drone(
        client, drone_owner, get_endpoint_link, drone["id"], {"is_drone_modified": True, "mtom_override": 950, "category": "c2"}
    )
    assert r.status_code == 200, f"Modified drone was not stored: {r.text}"
    assert r.json()["mtom_override"] == 950, f"The modified mass must be stored: {r.text}"

    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"is_drone_modified": False})
    assert r.status_code == 200, f"Modification was not switched off: {r.text}"
    assert r.json()["mtom_override"] is None, f"Switching modified off must clear the mass: {r.text}"


def test_switch_to_custom_model(client: Client, drone_owner: UserInfo, drone: dict, get_endpoint_link: EndpointCreator):
    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"custom_model": custom_model(mtom=500)})
    assert r.status_code == 200, f"Drone did not get its own model: {r.text}"

    model = r.json()["model"]
    assert not model["is_model_verified"], f"A typed-in model waits for a moderator: {r.text}"

    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"model_id": drone["model"]["id"]})
    assert r.status_code == 200, f"Drone did not get the catalog model back: {r.text}"
    # no drone uses the typed-in model any more, it was removed with the change
    assert delete_model(client, get_endpoint_link, model["id"]).status_code == 404, "An unused typed-in model must be removed"


def test_foreign_drone(client: Client, drone: dict, get_endpoint_link: EndpointCreator):
    stranger = functional.create_user()
    assert registration_flow(client, stranger, get_endpoint_link), "Registration failed"

    r = update_drone(client, stranger, get_endpoint_link, drone["id"], {"category": "c2"})
    assert r.status_code == 404, f"Another pilot's drone must not be changed: {r.text}"
    r = delete_drone(client, stranger, get_endpoint_link, drone["id"])
    assert r.status_code == 404, f"Another pilot's drone must not be deleted: {r.text}"


def test_delete_drone(client: Client, drone_owner: UserInfo, drone: dict, get_endpoint_link: EndpointCreator):
    r = delete_drone(client, drone_owner, get_endpoint_link, drone["id"])
    assert r.status_code == 204, f"Drone was not deleted: {r.text}"

    r = own_drone(client, drone_owner, get_endpoint_link, drone["id"])
    assert r.status_code == 404, f"A deleted drone must not be shown: {r.text}"
    r = update_drone(client, drone_owner, get_endpoint_link, drone["id"], {"category": "c2"})
    assert r.status_code == 404, f"A deleted drone must not be changed: {r.text}"


def test_drone_in_flight_is_locked(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_flow(client, pilot, get_endpoint_link, constants.CHECKIN_CLEAN_POINT)
    assert r.status_code == 201, f"Check-in was not started: {r.text}"

    try:
        r = update_drone(client, pilot, get_endpoint_link, pilot["drone_id"], {"category": "pb"}) # type: ignore[arg-type]
        assert r.status_code == 409, f"A drone in a check-in must not be changed: {r.text}"
        r = delete_drone(client, pilot, get_endpoint_link, pilot["drone_id"]) # type: ignore[arg-type]
        assert r.status_code == 409, f"A drone in a check-in must not be deleted: {r.text}"
    finally:
        checkin_end(client, pilot, get_endpoint_link)

    r = update_drone(client, pilot, get_endpoint_link, pilot["drone_id"], {"category": "pb"}) # type: ignore[arg-type]
    assert r.status_code == 200, f"After the check-in ended the drone can be changed again: {r.text}"
