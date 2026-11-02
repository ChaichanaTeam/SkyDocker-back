import os
from dotenv import load_dotenv
import httpx


load_dotenv()


BASE_HOST = os.getenv("BASE_HOST", "localhost")
LIVE_API_LINK = httpx.URL(f"http://{BASE_HOST}:8000/api/v1/")
DEMO_API_LINK = httpx.URL(f"http://{BASE_HOST}:8000/api/demo/")
OTP_CODE = os.getenv("OTP_CODE")
RATE_LIMIT_THRESHOLD = int(os.getenv("RATE_LIMIT_THRESHOLD", 5))

# Check-in points, (lon, lat), they depend on the PANSA zone catalog
CHECKIN_CLEAN_POINT = (17.0, 53.5)          # no restrictions for a1, 50 m, 200 m
CHECKIN_CONSENT_POINT = (21.012, 52.229)    # Warsaw centre, RPA zones need the zone manager consent
CHECKIN_OUTSIDE_POINT = (25.28, 54.69)      # Vilnius, outside the Polish airspace