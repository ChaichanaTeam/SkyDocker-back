from types import ModuleType
from typing import Optional
from fastapi import APIRouter
from loguru import logger


class VersionRouter(APIRouter):
    def __init__(self, api_module: ModuleType):
        self.router_name = api_module.__name__.rsplit('.', 1)[-1]

        super().__init__(prefix=f"/{self.router_name}")
        self.business_routers: Optional[list[APIRouter]] = getattr(api_module, "BusinessRouters", None)
        self.base_router: Optional[APIRouter] = getattr(api_module, "BaseRouter", None)

        if self.base_router is None:
            logger.error("Base router is not valid")

        if self.business_routers is None:
            logger.error("Business router is not valid")

    def attach_base_router(self) -> None:
        if self.base_router is None:
            return

        logger.info(f"{self.router_name}: Attaching router: base")
        self.include_router(self.base_router)

    def attach_business_routers(self) -> None:
        if self.business_routers is None:
            return

        for router in self.business_routers:
            logger.info(f"{self.router_name}: Attaching router: {router.prefix}")
            self.include_router(router)