from backend_src.core.config import Settings


ACCESS_TTL_SECONDS = Settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

class RateLimits:
    if Settings.DEBUG:
        LOGIN = (999, 60)
        REFRESH = (999, 60)
        LOGOUT = (999, 60)
        REGISTER_REQUEST_OTP = (999, 60)
        REGISTER_VERIFY_OTP = (999, 60)
        REGISTER = (999, 60)
        FORGOT_PASSWORD = (999, 60)
        VERIFY_RESET_TOKEN = (999, 60)
        RESET_PASSWORD = (999, 60)
    else:
        LOGIN = (10, 60)
        REFRESH = (30, 60)
        LOGOUT = (30, 60)
        REGISTER_REQUEST_OTP = (3, 60)
        REGISTER_VERIFY_OTP = (3, 60)
        REGISTER = (3, 60)
        FORGOT_PASSWORD = (3, 60)
        VERIFY_RESET_TOKEN = (10, 60)
        RESET_PASSWORD = (1, 60)