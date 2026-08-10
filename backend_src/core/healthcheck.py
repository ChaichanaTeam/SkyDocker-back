from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from backend_src.db.dependencies import get_db
from backend_src.db.session import SessionLocal


from .config import Settings
from fastapi import status


class HealthStatus:
    HEALTHY = "ok", status.HTTP_200_OK
    ATTENTION = "needs attention", status.HTTP_501_NOT_IMPLEMENTED
    CRITICAL = "critical", status.HTTP_503_SERVICE_UNAVAILABLE


class BackendHealthMixin():
    status = HealthStatus.HEALTHY
    

    def get_health() -> tuple[dict[str, str], int]:
        return ({ "status": BackendHealthMixin.status[0] }, BackendHealthMixin.status[1])


    async def healthcheck(self) -> bool:
        result = True

        count = self._verify_settings()
        if count > 0:
            BackendHealthMixin.status = HealthStatus.ATTENTION
            logger.warning("Server is running. But not configured")
            result = False

        if not await self._verify_db_connection():
            BackendHealthMixin.status = HealthStatus.CRITICAL
            logger.warning("Server cannot function without database")
            result = False

        return result


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
        db = SessionLocal()

        try:
            await db.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Cannot connect to SQL Server")
            logger.debug(f"{e}")
            return False
        finally:
            await db.close()
        
        return True