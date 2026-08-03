from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings

from fastapi import FastAPI
from redis_fastapi import AsyncRedisDep, FastAPIRedis

from backend_src.db import AsyncDBDep
from backend_src.models import Country

app = FastAPI()


class BackendApp(FastAPI):
    def __init__(self):
        super().__init__()

        self.add_middleware(
            CORSMiddleware,
            allow_origins=Settings.ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        redis = FastAPIRedis(self)
        redis.lifespan()

        self.__initializeRoutes(super())

    def __initializeRoutes(self, app: FastAPI) -> None:


        @app.get("/")
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
