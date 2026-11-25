from backend_src.core.config import Settings
from backend_src.storage.constants import PRESIGNED_TTL_SECONDS


OTP_TTL_SECONDS = Settings.VERIFY_TOKEN_EXPIRE_MINUTES * 60
# A review holds the item as long as the document links it gave stay valid
REVIEW_LOCK_TTL_SECONDS = PRESIGNED_TTL_SECONDS
