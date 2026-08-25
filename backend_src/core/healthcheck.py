from dataclasses import dataclass
from loguru import logger
from fastapi import status
from redis import asyncio
from sqlalchemy import text

from backend_src.db.session import AsyncSessionMaker
from .config import Settings

@dataclass(frozen=True)
class HealthStatus:
    HEALTHY = "ok", status.HTTP_200_OK
    ATTENTION = "needs attention", status.HTTP_501_NOT_IMPLEMENTED
    CRITICAL = "critical", status.HTTP_503_SERVICE_UNAVAILABLE


class BackendHealthMixin():
    status = HealthStatus.HEALTHY
    
    @staticmethod
    def get_health() -> tuple[dict[str, str], int]:
        return ({ "status": BackendHealthMixin.status[0] }, BackendHealthMixin.status[1])


    async def healthcheck(self) -> bool:
        count = self._verify_settings()
        if count > 0:
            BackendHealthMixin.status = HealthStatus.ATTENTION
            logger.warning("Server is running. But not configured")
            return False

        if not await self._verify_db_connection():
            BackendHealthMixin.status = HealthStatus.CRITICAL
            logger.warning("Server cannot function without database")
            return False

        if not await self._verify_redis_connection():
            BackendHealthMixin.status = HealthStatus.CRITICAL
            logger.warning("Server cannot function without redis")
            return False

        return True


    def _verify_settings(self) -> int:
        count = 0

        attributes = list(
            filter(
                lambda a: not a.startswith('__') and not callable(getattr(Settings, a)),
                dir(Settings)
            )
        )

        for attribute in attributes:
            if getattr(Settings, attribute) is None:
                count += 1
                logger.warning(f"Attribute {attribute} is not set. Check environment definitions")

        return count


    async def _verify_db_connection(self) -> bool:
        db = AsyncSessionMaker()

        try:
            await db.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Cannot connect to SQL Server")
            logger.debug(f"{e}")
            return False
        finally:
            await db.close()
        
        return True

    async def _verify_redis_connection(self) -> bool:
        redis = None

        try:
            redis = asyncio.Redis.from_url(Settings.REDIS_URL) # type: ignore
            await redis.ping()
        except Exception as e:
            logger.error(f"Cannot connect to Redis")
            logger.debug(f"{e}")
            return False
        finally:
            if redis is not None:
                await redis.close()
        
        return True