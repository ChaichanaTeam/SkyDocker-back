import os
from dotenv import load_dotenv


load_dotenv()


BASE_URL = "http://{BASE_HOST}:8000".format(BASE_HOST=os.getenv("BASE_HOST", "app"))
DEFAULT_CODE="008967"