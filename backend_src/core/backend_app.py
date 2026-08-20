from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_src.api import AuthRouter, PilotRouter, BaseRouter
from backend_src.cache import init_redis
from .config import Settings
from .healthcheck import BackendHealthMixin, HealthStatus
from .logger import BackendLoggerMixin


class BackendApp(FastAPI, BackendHealthMixin, BackendLoggerMixin):
    def __init__(self, lifespan):
        self.setup_logging()
        super().__init__(lifespan=lifespan)

        self.add_middleware(
            CORSMiddleware,
            allow_origins=Settings.ORIGINS,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.include_router(BaseRouter)

        init_redis(self)


@asynccontextmanager
async def lifespan(app: BackendApp):
    if await app.healthcheck():
        app.include_router(AuthRouter)
        app.include_router(PilotRouter)

    yield
