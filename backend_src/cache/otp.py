from random import choices, shuffle, randint
from string import ascii_uppercase, digits

from backend_src.core.config import Settings
from .client import AsyncRedisSession
from .keys import otp_key
from .tokens import hash_token
from .constants import OTP_TTL_SECONDS


def _generate_otp_code() -> str:
    if Settings.DEBUG:
        return Settings.OTP_CODE # type: ignore

    k_num = randint(1, 3)
    k_letters = 6 - k_num
    nums = choices(digits, k=k_num)
    letters = choices(ascii_uppercase, k=k_letters)

    code = letters + nums
    shuffle(code)
    return ''.join(code)


async def issue_otp(redis: AsyncRedisSession, purpose: str, subject: str) -> None:
    code = _generate_otp_code()
    await redis.set(otp_key(purpose, subject), hash_token(code), ex=OTP_TTL_SECONDS)


async def check_otp(redis: AsyncRedisSession, purpose: str, subject: str, code: str) -> bool:
    stored_hash = await redis.getdel(otp_key(purpose, subject))
    if stored_hash is None:
        return False

    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    return stored_hash == hash_token(code)
