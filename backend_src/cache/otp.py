from loguru import logger
from redis_fastapi import AsyncRedisDep

from backend_src.core.config import Settings

from .keys import otp_key
from .tokens import hash_token

OTP_TTL_SECONDS = Settings.VERIFY_TOKEN_EXPIRE_MINUTES * 60


def _generate_otp_code() -> str:
    return Settings.OTP_CODE


async def issue_otp(redis: AsyncRedisDep, purpose: str, subject: str) -> None:
    code = _generate_otp_code()
    await redis.set(otp_key(purpose, subject), hash_token(code), ex=OTP_TTL_SECONDS)
    logger.info(f"OTP code ({purpose}) for subject {subject}: {code}")


async def check_otp(redis: AsyncRedisDep, purpose: str, subject: str, code: str) -> bool:
    stored_hash = await redis.getdel(otp_key(purpose, subject))
    if stored_hash is None:
        return False

    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    return stored_hash == hash_token(code)
