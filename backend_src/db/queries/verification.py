from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from backend_src.db import AsyncDBSession
from backend_src.models import VerificationRequest, VerificationRequestStatus


def _with_documents():
    return select(VerificationRequest).options(selectinload(VerificationRequest.verification_document))


async def get_by_id(id: int, db: AsyncDBSession) -> Optional[VerificationRequest]:
    result = await db.execute(_with_documents().where(VerificationRequest.id == id))
    return result.scalar_one_or_none()


async def get_pending_by_pilot(pilot_id: int, db: AsyncDBSession) -> Optional[VerificationRequest]:
    result = await db.execute(
        select(VerificationRequest).where(
            VerificationRequest.pilot_id == pilot_id,
            VerificationRequest.status == VerificationRequestStatus.PENDING,
        )
    )
    return result.scalar_one_or_none()


async def get_all(status: Optional[VerificationRequestStatus], db: AsyncDBSession) -> list[VerificationRequest]:
    query = _with_documents().order_by(VerificationRequest.id.desc())
    if status is not None:
        query = query.where(VerificationRequest.status == status)

    result = await db.execute(query)
    return list(result.scalars().all())
