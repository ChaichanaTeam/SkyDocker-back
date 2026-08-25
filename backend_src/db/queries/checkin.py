from sqlalchemy import select
from sqlalchemy.orm import joinedload
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope

from backend_src.db import AsyncDBSession
from backend_src.models import Checkin


async def get_all_by_bbox(x1: float, y1: float, x2: float, y2: float, db: AsyncDBSession) -> list[Checkin]:
    result = await db.execute(
        select(Checkin)
        .where(ST_Intersects(Checkin.home_point, ST_MakeEnvelope(x1, y1, x2, y2, 4326)))
        .options(joinedload(Checkin.country))
        .options(joinedload(Checkin.pilot))
    )

    return result.scalars().all() # type: ignore