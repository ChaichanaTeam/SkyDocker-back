from typing import Optional
from fastapi import APIRouter, Query

from backend_src.api.dependencies import AsyncDBDep
from backend_src.api.shared_schemas import E164PhoneNumber, NormalizedEmailStr
from backend_src.models.enum import FlyingPrivileges
from . import service


router = APIRouter(prefix="/flying-privilege", tags=["flying-privilege"])


@router.post("/grant")
async def grant_privileges(
    db: AsyncDBDep,
    email: NormalizedEmailStr = Query(description="Email of an existing pilot"),
    privileges: list[FlyingPrivileges] = Query(description="Privileges to grant, repeat for several"),
    phone_number: Optional[E164PhoneNumber] = Query(None, description="Pilot contact, a check-in shows it"),
    first_name: Optional[str] = Query(None, max_length=255),
    last_name: Optional[str] = Query(None, max_length=255),
):
    # stands in for the licence verification, which fills the pilot data together with the privileges
    return await service.grant_privileges(db, email, privileges, phone_number, first_name, last_name)
