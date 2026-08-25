from collections.abc import AsyncGenerator

from backend_src.api.exceptions import APIExceptions
from backend_src.db import AsyncDBSession
from backend_src.models import Country
from .constants import COUNTRY_NAMES


async def generate_country() -> AsyncGenerator[Country, None]:
    for country_name, country_code in COUNTRY_NAMES:
        country = Country(name=country_name, code=country_code)
        yield country


async def create_country(db: AsyncDBSession) -> dict[str, str]:
    try:
        country = await anext(generate_country())
    except StopAsyncIteration:
        raise APIExceptions.not_found("No country left")

    db.add(country)
    await db.commit()
    await db.refresh(country)

    return {
        "message": f"Country {country.name} setted up"
    }