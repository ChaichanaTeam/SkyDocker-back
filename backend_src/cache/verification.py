from backend_src.core.config import Settings
from .client import AsyncRedisSession
from .keys import verification_token_key


# Outlives the token, so a used token stays marked until it expires on its own
_USED_TOKEN_TTL_SECONDS = Settings.VERIFICATION_TOKEN_EXPIRE_MINUTES * 60


async def is_verification_token_used(redis: AsyncRedisSession, jti: str) -> bool:
    return await redis.exists(verification_token_key(jti)) > 0


async def claim_verification_token(redis: AsyncRedisSession, jti: str) -> bool:
    return bool(await redis.set(verification_token_key(jti), 1, nx=True, ex=_USED_TOKEN_TTL_SECONDS))


async def release_verification_token(redis: AsyncRedisSession, jti: str) -> None:
    await redis.delete(verification_token_key(jti))
