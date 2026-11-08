from backend_src.core.config import Settings


class RateLimits:
    if Settings.DEBUG:
        PREVIEW_REQUEST = (999, 60)
        CREATE_REQUEST = (999, 60)
        WITHDRAW_REQUEST = (999, 60)
    else:
        PREVIEW_REQUEST = (10, 60)
        CREATE_REQUEST = (3, 60)
        WITHDRAW_REQUEST = (10, 60)
