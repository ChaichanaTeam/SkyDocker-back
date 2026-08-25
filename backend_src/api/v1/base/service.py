from fastapi.responses import JSONResponse

from backend_src.core.healthcheck import BackendHealthMixin


async def health() -> JSONResponse:
    status = BackendHealthMixin.get_health()

    response = JSONResponse(
        status[0],
        status_code=status[1]
    )

    return response
