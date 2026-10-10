import os
from dotenv import load_dotenv
import httpx


load_dotenv()


BASE_HOST = os.getenv("BASE_HOST", "localhost")
LIVE_API_LINK = httpx.URL(f"http://{BASE_HOST}:8000/api/v1/")
DEMO_API_LINK = httpx.URL(f"http://{BASE_HOST}:8000/api/demo/")
OTP_CODE = os.getenv("OTP_CODE")
RATE_LIMIT_THRESHOLD = int(os.getenv("RATE_LIMIT_THRESHOLD", 5))