import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_URL = os.getenv("DB_URL")
FLY_AUTH_TOKEN = os.getenv("FLY_AUTH_TOKEN")
FLY_IMAGE_ID = os.getenv("FLY_IMAGE_ID")
REGION = os.getenv("FLY_REGION", "dev")
SUI_PK = os.getenv("SUI_PK")

ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

DEFAULT_RPCS_JSON_FILE_URL = "https://suinfra.io/static/rpcs.json"
