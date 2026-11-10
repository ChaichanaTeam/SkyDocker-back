from typing import Any, Optional, TypedDict
from fastapi import HTTPException, status


class EntityError(TypedDict):
    type: str
    loc: list[str]
    msg: str
    input: Any


class APIExceptions:
    @staticmethod
    def unauthorized(detail: str, headers: Optional[dict[str, str]] = None) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
        )

    @staticmethod
    def bad_request(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    @staticmethod
    def conflict(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    @staticmethod
    def not_found(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

    @staticmethod
    def content_too_large(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=detail,
        )

    @staticmethod
    def unprocessable(errors: list[EntityError]) -> HTTPException:
        """Business-rule errors in the same shape as FastAPI request validation errors."""
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=errors,
        )

    @staticmethod
    def bad_gateway(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )

    credentials_exception = unauthorized("Could not validate credentials")