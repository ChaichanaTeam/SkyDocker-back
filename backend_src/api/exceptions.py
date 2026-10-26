from fastapi import HTTPException, status

class APIExceptions:
    @staticmethod
    def unauthorized(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
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
    def unprocessable(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=detail,
        )

    @staticmethod
    def bad_gateway(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )

    credentials_exception = unauthorized("Could not validate credentials")