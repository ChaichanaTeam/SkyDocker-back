from backend_src.core.config import Settings


ACCESS_TTL_SECONDS = Settings.MODERATOR_ACCESS_TOKEN_EXPIRE_MINUTES * 60

# The refresh cookie is sent only to the moderator auth endpoints
REFRESH_COOKIE_NAME = "moderator_refresh"
REFRESH_COOKIE_PATH = "/api/v1/moderator/auth"

class RateLimits:
    if Settings.DEBUG:
        LOGIN = (999, 60)
        REFRESH = (999, 60)
        LOGOUT = (999, 60)
    else:
        LOGIN = (10, 60)
        REFRESH = (60, 60)
        LOGOUT = (30, 60)
