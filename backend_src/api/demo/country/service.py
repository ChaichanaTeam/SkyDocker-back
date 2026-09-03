from typing import Any

from sqlalchemy import select

from backend_src.db import AsyncDBSession
from backend_src.models import Country
from .constants import COUNTRY_NAMES


async def create_countries(db: AsyncDBSession) -> dict[str, Any]:
    existing = set(
        (await db.execute(select(Country.country_tag))).scalars().all()
    )

    name_by_tag = {tag: name for name, tag in COUNTRY_NAMES}
    missing_tags = [tag for _, tag in COUNTRY_NAMES if tag not in existing]

    if missing_tags:
        db.add_all(
            Country(name=name_by_tag[tag], country_tag=tag) for tag in missing_tags
        )
        await db.commit()

    return {
        "message": f"Created {len(missing_tags)} of {len(COUNTRY_NAMES)} countries",
        "added": missing_tags,
        "skipped": sorted(tag for tag in name_by_tag if tag in existing),
        "total": len(COUNTRY_NAMES),
    }
