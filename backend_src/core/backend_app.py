from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_src.api import (
    MainAPIRouter,
    DemoAPIRouter
)
from backend_src.cache.client import init_redis
from .config import Settings
from .healthcheck import BackendHealthMixin
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

        init_redis(self)


@asynccontextmanager
async def lifespan(app: BackendApp):
    if Settings.DEBUG:
        DemoAPIRouter.attach_base_router()
        DemoAPIRouter.attach_business_routers()
        app.include_router(DemoAPIRouter)

    MainAPIRouter.attach_base_router()
    
    if await app.healthcheck():
        MainAPIRouter.attach_business_routers()

    app.include_router(MainAPIRouter)
    
    yield
