import os
import typer

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_URL = os.getenv("DB_URL")
FLY_AUTH_TOKEN = os.getenv("FLY_AUTH_TOKEN")
FLY_IMAGE_ID = os.getenv("FLY_IMAGE_ID")
REGION = os.getenv("FLY_REGION", "dev")
SUI_PK = os.getenv("SUI_PK")

if not DB_NAME:
    raise typer.Exit("DB_NAME env var is not set.")
if not DB_URL:
    raise typer.Exit("DB_URL env var is not set.")
if not FLY_AUTH_TOKEN:
    raise typer.Exit("FLY_AUTH_TOKEN env var is not set.")
if not FLY_IMAGE_ID:
    raise typer.Exit("FLY_IMAGE_ID env var is not set.")
if not SUI_PK:
    raise typer.Exit("SUI_PK env var is not set.")

ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

DEFAULT_RPCS_JSON_FILE_URL = "https://suinfra.io/static/rpcs.json"
