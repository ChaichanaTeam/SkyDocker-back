import os
from dotenv import load_dotenv


load_dotenv()


BASE_URL = "http://{BASE_HOST}:8000/api/v1".format(BASE_HOST=os.getenv("BASE_HOST", "app"))
OTP_CODE=os.getenv("OTP_CODE")
RATE_LIMIT_THRESHOLD=int(os.getenv("RATE_LIMIT_THRESHOLD", 5))