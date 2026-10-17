import random
import string

from tests import constants
from tests.types import TokenContainer, UserInfo

def random_local():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"testuser_{suffix}"


def random_email():
    return f"{random_local()}@localhost.me"


def random_phone():
    # +4850x is a valid Polish mobile range; arbitrary digits fail phonenumbers validation
    number = "+4850" + ''.join(random.choices(string.digits, k=7))

    return number


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