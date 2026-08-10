from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis_fastapi import AsyncRedisDep

from backend_src.core.healthcheck import BackendHealthMixin
from backend_src.db import AsyncDBDep
from backend_src.models import Country


router = APIRouter(tags=["base"])


@router.get("/health")
async def health():
    status = BackendHealthMixin.get_health()

    response = JSONResponse(
        status[0],
        status_code=status[1]
    )

    return response

@router.get("/")
async def main(redis: AsyncRedisDep, db: AsyncDBDep):
    country = Country(name="Poland", country_tag="PL")
    
    db.add(country)
    await db.commit()
    await db.refresh(country)

    await redis.set("Country", country.name)
    value = await redis.get("Country")

    return {
        "message": f"Congratulations with your country! {value} | {country.country_tag} | {country.id}"
    }