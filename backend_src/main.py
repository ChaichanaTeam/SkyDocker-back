from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from backend_src.db import get_db
from backend_src.models import Country

app = FastAPI()

@app.get("/")
async def main(db: AsyncSession = Depends(get_db)):
    country = Country(name="Poland", country_tag="PL")
    
    db.add(country)
    await db.commit()
    await db.refresh(country)

    return {
        "message": f"Congratulations with your country! {country.name} | {country.country_tag} | {country.id}"
    }