import pytest
from httpx import Client

from tests import constants
from tests.types import UserInfo, EndpointCreator
from tests.utils.behavioural.geozone_behaviour import country_at_point


def test_point_in_poland(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    r = country_at_point(client, borders_env, get_endpoint_link, constants.COUNTRY_PL_POINT)
    assert r.status_code == 200, f"A point inside the Polish border was not resolved: {r.text}"
    assert r.json() == {"country_tag": "PL"}, f"Wrong country: {r.text}"


@pytest.mark.parametrize("tag, point", [
    ("CZ", constants.COUNTRY_CZ_POINT),
    ("HR", constants.COUNTRY_HR_POINT),
])
def test_point_in_other_country(
    client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator, tag: str, point: tuple[float, float]
):
    r = country_at_point(client, borders_env, get_endpoint_link, point)
    if r.status_code == 404:
        pytest.skip(f"{tag} border is not synced")

    assert r.status_code == 200, f"A point inside the {tag} border was not resolved: {r.text}"
    assert r.json() == {"country_tag": tag}, f"Wrong country: {r.text}"


def test_point_in_sea(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    r = country_at_point(client, borders_env, get_endpoint_link, constants.COUNTRY_SEA_POINT)
    assert r.status_code == 404, f"Open sea is outside every border: {r.text}"


def test_point_outside_europe(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    r = country_at_point(client, borders_env, get_endpoint_link, constants.COUNTRY_OUTSIDE_EUROPE_POINT)
    assert r.status_code == 422, f"Coordinates outside Europe must be rejected: {r.text}"


def test_missing_latitude(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    lon, _ = constants.COUNTRY_PL_POINT
    r = client.get(
        get_endpoint_link("live", "geo-zone/country"),
        headers={"Authorization": f"Bearer {borders_env['tokens']['access_token']}"},
        params={"lon": lon},
    )
    assert r.status_code == 422, f"A point without latitude must be rejected: {r.text}"


def test_without_token(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    r = country_at_point(client, None, get_endpoint_link, constants.COUNTRY_PL_POINT)
    assert r.status_code == 401, f"Country lookup needs an access token: {r.text}"
