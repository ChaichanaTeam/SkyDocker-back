from dataclasses import dataclass

from backend_src.core.config import Settings
from backend_src.core.security import IssuedToken

from .client import AsyncRedisSession
from .keys import refresh_key, session_gen_key
from .tokens import hash_token

REFRESH_TTL_SECONDS = Settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


@dataclass(frozen=True)
class SessionScope:
    """Keeps sessions of different roles apart, a pilot and a moderator may share an id."""
    prefix: str
    refresh_ttl: int


PILOT_SCOPE = SessionScope(prefix="", refresh_ttl=REFRESH_TTL_SECONDS)
MODERATOR_SCOPE = SessionScope(prefix="moderator:", refresh_ttl=Settings.MODERATOR_REFRESH_TOKEN_EXPIRE_MINUTES * 60)


async def store_refresh_session(redis: AsyncRedisSession, subject: str, refresh: IssuedToken, scope: SessionScope = PILOT_SCOPE) -> None:
    await redis.set(
        refresh_key(subject, refresh.jti, scope.prefix),
        hash_token(refresh.token),
        ex=scope.refresh_ttl,
    )


async def pop_refresh_session(redis: AsyncRedisSession, subject: str, jti: str, scope: SessionScope = PILOT_SCOPE) -> str | None:
    stored_hash = await redis.getdel(refresh_key(subject, jti, scope.prefix))
    if stored_hash is None:
        return None

    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    return stored_hash


async def revoke_refresh_session(redis: AsyncRedisSession, subject: str, jti: str, scope: SessionScope = PILOT_SCOPE) -> None:
    await redis.delete(refresh_key(subject, jti, scope.prefix))


def verify_refresh_token(stored_hash: str | None, token: str) -> bool:
    return stored_hash is not None and stored_hash == hash_token(token)


async def get_session_gen(redis: AsyncRedisSession, subject: str, scope: SessionScope = PILOT_SCOPE) -> int:
    gen = await redis.get(session_gen_key(subject, scope.prefix))
    if gen is None:
        return 0

    if isinstance(gen, bytes):
        gen = gen.decode()

    return int(gen)


async def revoke_all_sessions(redis: AsyncRedisSession, subject: str, scope: SessionScope = PILOT_SCOPE) -> None:
    # Bumping the generation invalidates every access/reset token issued before
    key = session_gen_key(subject, scope.prefix)
    await redis.incr(key)
    await redis.expire(key, scope.refresh_ttl)

    async for refresh in redis.scan_iter(match=refresh_key(subject, "*", scope.prefix)):
        await redis.delete(refresh)
