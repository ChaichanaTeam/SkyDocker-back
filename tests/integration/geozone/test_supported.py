from httpx import Client

from tests import constants
from tests.types import UserInfo, EndpointCreator
from tests.utils.behavioural.geozone_behaviour import country_at_point, supported_countries


def test_supported_countries(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    r = supported_countries(client, borders_env, get_endpoint_link)
    assert r.status_code == 200, f"Supported countries were not listed: {r.text}"

    countries = r.json()["countries"]
    assert "PL" in countries, f"Poland has a border and geo-zones, it must be supported: {r.text}"
    assert len(countries) == len(set(countries)), f"Countries must not repeat: {r.text}"
    assert all(len(tag) == 2 and tag.isupper() for tag in countries), f"Countries must be ISO alpha-2 codes: {r.text}"


def test_resolved_country_is_supported(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    # the frontend resolves the country at the home point and checks it can be used for a check-in
    tag = country_at_point(client, borders_env, get_endpoint_link, constants.COUNTRY_PL_POINT).json()["country_tag"]

    r = supported_countries(client, borders_env, get_endpoint_link)
    assert tag in r.json()["countries"], f"{tag} was resolved but is not supported: {r.text}"


def test_without_token(client: Client, borders_env: UserInfo, get_endpoint_link: EndpointCreator):
    r = supported_countries(client, None, get_endpoint_link)
    assert r.status_code == 401, f"Supported countries need an access token: {r.text}"
