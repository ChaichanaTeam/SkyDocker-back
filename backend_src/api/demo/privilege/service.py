from typing import Any, Optional

from sqlalchemy import select

from backend_src.api.exceptions import APIExceptions
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import PilotToFlyingPrivileges
from backend_src.models.enum import FlyingPrivileges


async def _pilot_privileges(db: AsyncDBSession, pilot_id: int) -> set[FlyingPrivileges]:
    result = await db.execute(
        select(PilotToFlyingPrivileges.flying_privilege)
        .where(PilotToFlyingPrivileges.pilot_id == pilot_id)
    )
    return set(result.scalars().all())


async def grant_privileges(
    db: AsyncDBSession,
    email: str,
    privileges: list[FlyingPrivileges],
    phone_number: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> dict[str, Any]:
    if FlyingPrivileges.UNKNOWN in privileges:
        raise APIExceptions.bad_request(f"'{FlyingPrivileges.UNKNOWN}' cannot be granted")

    pilot = await Queries.Pilot.get_by_email(email, db)
    if pilot is None:
        raise APIExceptions.not_found(f"Pilot {email} not found")
    pilot_id = pilot.id

    existing = await _pilot_privileges(db, pilot_id)
    requested = list(dict.fromkeys(privileges))
    missing = [privilege for privilege in requested if privilege not in existing]

    if phone_number is not None:
        pilot.phone_number = phone_number
    if first_name is not None:
        pilot.first_name = first_name
    if last_name is not None:
        pilot.last_name = last_name

    contact = {"phone_number": pilot.phone_number, "first_name": pilot.first_name, "last_name": pilot.last_name}

    db.add_all(
        PilotToFlyingPrivileges(pilot_id=pilot_id, flying_privilege=privilege) for privilege in missing
    )
    await db.commit()

    return {
        "message": f"Granted {len(missing)} of {len(requested)} privilege(s) to {email}",
        "pilot_id": pilot_id,
        "added": missing,
        "skipped": [privilege for privilege in requested if privilege in existing],
        "privileges": sorted(existing | set(missing)),
        **contact,
    }
