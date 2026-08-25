from fastapi import APIRouter

from . import service


router = APIRouter(tags=["base"])


@router.get("/")
async def main():
    return await service.main()