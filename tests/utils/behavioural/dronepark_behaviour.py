import uuid
from typing import Any, Optional
from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


def _auth(user: Optional[UserInfo]) -> dict[str, str]:
    if user is None:
        return {}

    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def random_serial() -> str:
    return f"TEST-{uuid.uuid4().hex[:12].upper()}"


def custom_model(**overrides) -> dict[str, Any]:
    """A model that is surely not in the catalog, values as from a specification sheet."""
    model: dict[str, Any] = {
        "manufacturer": "Test Aero",
        "model_name": f"Probe {uuid.uuid4().hex[:8]}",
        "speed": 12,
        "mtom": 600,
        "max_height": 500,
        "max_range": 2000,
    }
    model.update(overrides)

    return model


def drone_body(model_id: Optional[int] = None, **overrides) -> dict[str, Any]:
    """Body of an unmodified c1 drone; without model_id the drone gets a custom model."""
    body: dict[str, Any] = {"serial_number": random_serial(), "category": "c1"}
    if model_id is not None:
        body["model_id"] = model_id
    else:
        body["custom_model"] = custom_model()
    body.update(overrides)

    return body


def drone_models(client: Client, user: Optional[UserInfo], get_endpoint_link: EndpointCreator) -> Response:
    return client.get(get_endpoint_link("live", "drone-models/"), headers=_auth(user))


def own_drones(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    return client.get(get_endpoint_link("live", "pilots/me/drones"), headers=_auth(user))


def own_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone_id: int) -> Response:
    return client.get(get_endpoint_link("live", f"pilots/me/drones/{drone_id}"), headers=_auth(user))


def add_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, body: dict[str, Any]) -> Response:
    return client.post(get_endpoint_link("live", "pilots/me/drones"), headers=_auth(user), json=body)


def update_drone(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone_id: int, body: dict[str, Any]
) -> Response:
    return client.patch(get_endpoint_link("live", f"pilots/me/drones/{drone_id}"), headers=_auth(user), json=body)


def delete_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone_id: int) -> Response:
    return client.delete(get_endpoint_link("live", f"pilots/me/drones/{drone_id}"), headers=_auth(user))


def seed_models(client: Client, get_endpoint_link: EndpointCreator) -> Response:
    return client.post(get_endpoint_link("demo", "drone-park/models/seed"))


def _moderator_auth(token: Optional[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token is not None else {}


def unverified_models(client: Client, token: Optional[str], get_endpoint_link: EndpointCreator) -> Response:
    return client.get(get_endpoint_link("live", "drone-models/unverified"), headers=_moderator_auth(token))


def approve_model(
    client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, model_id: int, correction: dict[str, Any]
) -> Response:
    return client.post(
        get_endpoint_link("live", f"drone-models/{model_id}/approve"), headers=_moderator_auth(token), json=correction
    )


def replace_model(
    client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, model_id: int, by_model_id: int
) -> Response:
    return client.post(
        get_endpoint_link("live", f"drone-models/{model_id}/replace"),
        headers=_moderator_auth(token),
        json={"model_id": by_model_id},
    )


def delete_model(client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, model_id: int) -> Response:
    return client.delete(get_endpoint_link("live", f"drone-models/{model_id}"), headers=_moderator_auth(token))


def remove_custom_drone(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone: dict[str, Any], moderator_token: Optional[str]
) -> None:
    """Cleanup: deletes the drone and, when a moderator is logged in, its typed-in model, so test models do not pile up."""
    delete_drone(client, user, get_endpoint_link, drone["id"])
    if moderator_token is not None:
        delete_model(client, moderator_token, get_endpoint_link, drone["model"]["id"])
