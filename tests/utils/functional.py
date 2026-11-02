import random
import string
from typing import Any, Optional

from httpx import Response

from tests import constants
from tests.types import PilotInfo, TokenContainer, UserInfo

def random_local():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"testuser_{suffix}"


def random_email():
    return f"{random_local()}@localhost.me"


def random_phone():
    # +4850x is a valid Polish mobile range; arbitrary digits fail phonenumbers validation
    number = "+4850" + ''.join(random.choices(string.digits, k=7))

    return number


def response_shape(r: Response) -> tuple[int, list[str]]:
    # Token values always differ, so only status and keys are comparable
    return r.status_code, sorted(r.json())


def wrong_otp_code() -> str:
    code = constants.OTP_CODE or "000000"

    return ''.join("B" if c == "A" else "A" for c in code)


def create_default_tokens() -> TokenContainer:
    return {
        "type": "Bearer",
        "verify_token": None,
        "register_token": None,
        "reset_token": None,
        "access_token": None,
        "refresh_token": None,
    }


def create_user(**overrides) -> UserInfo:
    user: UserInfo = {
        "email": random_email(),
        "phone_number": random_phone(),
        "first_name": "Name",
        "last_name": "Surname",
        "password": "p455w0rd",
        "tokens": create_default_tokens(),
    }
    user.update(overrides)  # type: ignore

    return user


def create_pilot(**overrides) -> PilotInfo:
    pilot: PilotInfo = {**create_user(), "drone_id": None, "checkin_token": None}  # type: ignore
    pilot.update(overrides)  # type: ignore

    return pilot


def checkin_plan(point: tuple[float, float], drone_id: Optional[int], **overrides) -> dict[str, Any]:
    """Preview body of a flight that passes in a free zone, an override set to None removes the field."""
    lon, lat = point
    plan: dict[str, Any] = {
        "country_tag": "PL",
        "home_point": {"lon": lon, "lat": lat},
        "drone_id": drone_id,
        "category": "a1",
        "height": 50,
        "range": 200,
        "duration": 30,
    }
    plan.update(overrides)

    return {key: value for key, value in plan.items() if value is not None}


def error_types(r: Response) -> set[str]:
    return {error["type"] for error in r.json()["detail"]}