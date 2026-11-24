from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils.behavioural.dronepark_behaviour import (
    add_drone, approve_model, custom_model, delete_drone, delete_model, drone_body, drone_models, own_drone,
    remove_custom_drone, replace_model, unverified_models,
)


def _queued(client: Client, get_endpoint_link: EndpointCreator, model_id: int) -> dict | None:
    return next((model for model in unverified_models(client, get_endpoint_link).json() if model["id"] == model_id), None)


def test_approve_typed_in_model(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(custom_model=custom_model(mtom=600), category="c1"))
    assert r.status_code == 201, f"Drone with its own model was not added: {r.text}"
    drone = r.json()
    model_id = drone["model"]["id"]

    try:
        queued = _queued(client, get_endpoint_link, model_id)
        assert queued is not None, "A typed-in model must wait in the moderator's queue"
        assert [d["id"] for d in queued["drones"]] == [drone["id"]], f"The queue must show the drone that uses the model: {queued}"
        assert queued["drones"][0]["pilot_email"] == drone_owner["email"], f"The queue must show the pilot: {queued}"

        name = f"{drone['model']['model_name']} Pro"
        r = approve_model(client, get_endpoint_link, model_id, {"model_name": name, "mtom": 950})
        assert r.status_code == 200, f"Model was not approved: {r.text}"
        review = r.json()
        assert review["model"]["is_model_verified"], f"An approved model is checked: {r.text}"
        assert [c["drone_id"] for c in review["class_conflicts"]] == [drone["id"]], \
            f"950 g no longer fits the c1 drone, the moderator must see it: {r.text}"

        r = own_drone(client, drone_owner, get_endpoint_link, drone["id"])
        assert r.json()["model"]["model_name"] == name, f"The drone must get the fixed values: {r.text}"
        assert r.json()["model"]["is_model_verified"], f"The drone's model is checked now: {r.text}"

        listed = {model["id"] for model in drone_models(client, drone_owner, get_endpoint_link).json()}
        assert model_id in listed, "An approved model must be in the catalog"
        assert _queued(client, get_endpoint_link, model_id) is None, "An approved model must leave the queue"
    finally:
        remove_custom_drone(client, drone_owner, get_endpoint_link, drone)


def test_approve_into_existing_model(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(custom_model=custom_model()))
    drone = r.json()

    try:
        air = drone_catalog["DJI Air 3"]
        r = approve_model(client, get_endpoint_link, drone["model"]["id"], {"manufacturer": "DJI", "model_name": "Air 3"})
        assert r.status_code == 409, f"Approving a second DJI Air 3 must be refused: {r.text}"
        assert r.json()["detail"]["model_id"] == air["id"], f"The catalog model to replace it with must be returned: {r.text}"
    finally:
        remove_custom_drone(client, drone_owner, get_endpoint_link, drone)


def test_replace_typed_in_model(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    # "DJl" with a small L does not match DJI, so it is stored as a new model
    typo = custom_model(manufacturer="DJl", model_name="Air 3", mtom=240)
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(custom_model=typo, category="c0"))
    assert r.status_code == 201, f"Drone with a misspelled model was not added: {r.text}"
    drone = r.json()
    model_id = drone["model"]["id"]

    try:
        air = drone_catalog["DJI Air 3"]
        r = replace_model(client, get_endpoint_link, model_id, air["id"])
        assert r.status_code == 200, f"Model was not replaced: {r.text}"
        assert [c["drone_id"] for c in r.json()["class_conflicts"]] == [drone["id"]], \
            f"720 g of the catalog model no longer fits the c0 drone: {r.text}"

        r = own_drone(client, drone_owner, get_endpoint_link, drone["id"])
        assert r.json()["model"]["id"] == air["id"], f"The drone must get the catalog model: {r.text}"
        assert _queued(client, get_endpoint_link, model_id) is None, "A replaced model must leave the queue"
        assert delete_model(client, get_endpoint_link, model_id).status_code == 404, "A replaced model must be removed"
    finally:
        delete_drone(client, drone_owner, get_endpoint_link, drone["id"])


def test_catalog_model_is_not_reviewed(client: Client, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    air = drone_catalog["DJI Air 3"]
    assert approve_model(client, get_endpoint_link, air["id"], {}).status_code == 409, "A catalog model is approved already"
    assert replace_model(client, get_endpoint_link, air["id"], air["id"]).status_code == 409, "A catalog model cannot be replaced"
