from fastapi import APIRouter, Query
from pydantic import EmailStr

from backend_src.api.dependencies import AsyncDBDep
from backend_src.models.enum import FlyingPrivileges
from . import service


router = APIRouter(prefix="/flying-privilege", tags=["flying-privilege"])


@router.post("/grant")
async def grant_privileges(
    db: AsyncDBDep,
    email: EmailStr = Query(description="Email of an existing pilot"),
    privileges: list[FlyingPrivileges] = Query(description="Privileges to grant, repeat for several"),
):
    return await service.grant_privileges(db, email, privileges)
