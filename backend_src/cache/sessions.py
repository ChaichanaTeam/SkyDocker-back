from backend_src.core.config import Settings
from backend_src.core.security import IssuedToken

from .client import AsyncRedisDep
from .keys import refresh_key
from .tokens import hash_token

REFRESH_TTL_SECONDS = Settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def store_refresh_session(redis: AsyncRedisDep, pilot_id: str, refresh: IssuedToken) -> None:
    await redis.set(
        refresh_key(pilot_id, refresh.jti),
        hash_token(refresh.token),
        ex=REFRESH_TTL_SECONDS,
    )


async def pop_refresh_session(redis: AsyncRedisDep, pilot_id: str, jti: str) -> str | None:
    stored_hash = await redis.getdel(refresh_key(pilot_id, jti))
    if stored_hash is None:
        return None

    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    return stored_hash


async def revoke_refresh_session(redis: AsyncRedisDep, pilot_id: str, jti: str) -> None:
    await redis.delete(refresh_key(pilot_id, jti))


def verify_refresh_token(stored_hash: str | None, token: str) -> bool:
    return stored_hash is not None and stored_hash == hash_token(token)
