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
CHECKIN_OUTSIDE_POINT = (25.28, 54.69)      # Vilnius, outside the Polish border
# Country lookup points, (lon, lat), they depend on the borders synced from GADM
COUNTRY_PL_POINT = (17.6698, 50.1508)       # Opole region, 2.8 km from the Czech border
COUNTRY_CZ_POINT = (17.0278, 50.2295)       # Czechia, 630 m from the Polish border
COUNTRY_HR_POINT = (15.0702, 45.2147)       # Croatia, about 21 km from its border
COUNTRY_SEA_POINT = (18.5, 55.5)            # Baltic Sea, outside every border
COUNTRY_OUTSIDE_EUROPE_POINT = (-40.0, 40.0)
